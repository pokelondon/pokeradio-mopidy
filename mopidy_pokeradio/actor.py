from __future__ import unicode_literals

import sys
import simplejson as json
from os import path
from threading import Event, Thread, RLock, Timer

import redis
import pykka
import requests
import logging

from mopidy.core import CoreListener
from mopidy.audio import PlaybackState


SCRATCH_PATH = path.abspath(path.join(
    path.dirname(__file__),
    'config',
    'common',
    'scratch.mp3'))

SCRATCH_FILE = 'file://{0}'.format(SCRATCH_PATH)

logger = logging.getLogger('mopidy_pokeradio')


class Base(object):
    """ Shared methods for the main frontend class and the Threaded Redis
    listner
    """

    def _play_track(self):
        r = requests.get(self.playlist_endpoint)
        try:
            data = r.json()
        except ValueError:
            logger.error('Invalid JSON from server')
        else:
            if 'empty' == data.get('status'):
                logger.info('No track to play next')

            if 'href' in data:
                # Check playing state again, incase it changed while the
                # get request is running in the redis listner thread.
                playing_state = self.core.playback.state.get()

                if PlaybackState.STOPPED == playing_state:
                    logger.info('Opening Track: {0}'.format(data['href']))
                    self._open_uri(data['href'])
                else:
                    logger.info('Play state change during request; '\
                                'abandoning this _play_track call')

    def _open_uri(self, uri):
        logger.info('Opening: {0}'.format(uri))
        tl_track = self.core.tracklist.add(uri=uri).get()
        try:
            self.core.playback.play(tl_track[0]).get()
        except IndexError:
            logger.error('No Tracks in PL')
        return tl_track



class PokeRadioFrontend(pykka.ThreadingActor, CoreListener, Base):

    config = None

    def __init__(self, config, core):
        super(PokeRadioFrontend, self).__init__()

        self.core = core
        self.config = config

        hostname = config['pokeradio']['hostname']
        port = config['pokeradio']['port']

        redis_host = config['pokeradio']['hostname']
        redis_db = config['pokeradio']['redis_db']
        redis_port = config['pokeradio'].get('redis_port', 6379)
        redis_password = config['pokeradio'].get('password', None)

        self.playlist_endpoint = 'http://{0}:{1}/api/mopidy/'\
                .format(hostname, port)

        self.r_conn = redis.StrictRedis(redis_host, redis_port, redis_db,
                                        password=redis_password)
        self.connect_to_redis()

        self.lock = RLock()
        interval = 10

        def update():
            self.track_playback_progress()
            self.timer = self._timer(interval, update)
        update()

    def connect_to_redis(self):
        self.pubsub = Listener(self.r_conn, self.core, self.config)
        try:
            self.pubsub.start()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()

    # Core listener
    def playback_state_changed(self, old_state, new_state):
        logger.info('State Change: {0} -> {1}'.format(old_state, new_state))

    # Core listener
    def track_playback_started(self, tl_track):
        tlid, track = tl_track
        if self._is_scratch(track):
            return

        requests.put(self.playlist_endpoint, json.dumps({'action': 'started',
                                                         'href': track.uri}))

        logger.info('Track Started: {0}'.format(track.name))


    # Core listener
    def track_playback_ended(self, tl_track, time_position):
        tlid, track = tl_track

        if not self._is_scratch(track):
            logger.info('Track Playback Ended: {0}'.format(track.name))
            self._send_track_ended(track.uri)

        self.estimated_end = None

        # Play the next track
        self._play_track()

    def _send_track_ended(self, track_uri):
        """ Update server that track has played
        """
        self.last_track_uri = None
        requests.put(self.playlist_endpoint,
                json.dumps({'action': 'ended', 'href': track_uri}))

    # ThreadingActor
    def on_start(self):
        logger.info('Actor Starting')
        self._play_track()

    # ThreadingActor
    def on_stop(self):
        logger.info('Actor Stopping')
        self.pubsub.stop()

    def _is_scratch(self, track):
        return track.uri == SCRATCH_FILE

    def track_playback_progress(self):
        status = {}

        cur_track = self.core.playback.current_track.get()

        if cur_track:
            time_position = self.core.playback.time_position.get()
            status['action'] = 'progress'
            status['playback_state'] = self.core.playback.state.get()
            status['uri'] = cur_track.uri
            status['time_position'] = time_position
            status['length'] = cur_track.length

            try:
                status['percentage'] = \
                        (float(time_position) / cur_track.length) * 100
            except (TypeError, ZeroDivisionError):
                status['percentage'] = 0

            if cur_track.uri != SCRATCH_FILE:
                requests.post(self.playlist_endpoint, json.dumps(status))

    def _timer(self, interval, func):
        if not interval or not func:
            return None
        with self.lock:
            if self.actor_stopped.is_set():
                return None
            timer = Timer(interval, func)
            timer.start()
            return timer


class Listener(Thread, Base):
    daemon = True

    def __init__(self, r_conn, core, config):
        Thread.__init__(self)

        self.core = core
        self.redis = r_conn
        self.ps = self.redis.pubsub()
        self.ps.subscribe(['mopdiy:track_scratch', 'mopidy:track_added'])
        self.playlist_endpoint = 'http://{0}:{1}/api/mopidy/'\
                .format(config['pokeradio']['hostname'],
                        config['pokeradio']['port'])

        self._stop = Event()

    def work(self, data):

        if 'message' != data['type']:
            return

        if 'mopdiy:track_scratch' == data['channel']:
            current_track = self.core.playback.current_track.get()
            if current_track:
                self._open_uri(SCRATCH_FILE)
                logger.info('Scratching: {0}'.format(current_track.name))
            return

        if 'mopidy:track_added' == data['channel']:
            playing_state = self.core.playback.state.get()
            if PlaybackState.STOPPED == playing_state:
                # Checks state again in _play_track
                self._play_track()
                logger.info('Track Added - Resuming')
            return

    def stop(self):
        self._stop.set()

    def run(self):
        for item in self.ps.listen():
            if self._stop.isSet():
                self.ps.unsubscribe()
                sys.exit()
            else:
                self.work(item)
