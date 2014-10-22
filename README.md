#pokeradio-mopidy
The Mopidy client that plays music from Spotify.
Install this on a Raspberry Pi, connect it up to the [PokeRadio webapp](https://github.com/pokelondon/pokeradio) and start queuing tracks and voting.

##Also in this family:
- [PokeRadio app](https://github.com/pokelondon/pokeradio)
- [PokeRadio Socket Server](https://github.com/pokelondon/pokeradio-socketserver)
- [**PokeRadio Mopidy Client**](https://github.com/pokelondon/pokeradio-mopidy) ☜ This!

## Running it

###You need:
- Some sort of Linux running hardware. RaspberryPi recommended, probably running [Raspian](http://www.raspberrypi.org/downloads/)
- A Spotify Pro account
- LibSpotify
- Speakers
- T'internets
- An installation of the [PokeRadio webapp](https://github.com/pokelondon/pokeradio)

###1. Clone the repo
```sh
$ ssh pi@{yourpi}
$ git clone http://github.com/pokelondon/pokeradio-mopidy
$ cd pokeradio-mopidy
```

###2. Install a few things.
Follow [these instructions to install Mopidy](https://docs.mopidy.com/en/latest/installation/raspberrypi/)

###3. Install the pokeradio extension
```sh
$ sudo python setup.py develop
```

###4. Set Config
Open `mopidy_pokeradio/config/mopidy.conf`
Set your Spotify Username and Password

#### PubSub (optional)
Redis PubSub allows the player to be notified of newly queued tracks, and when downvotes trigger a track skip. If you want to, find the Redis server connection details used for the [webapp](https://github.com/pokelondon/pokeradio) and add them to the `[pokeradio]` part of the config file.

###5. Run it
Make sure the path to where you installed the pokeradio extension to is available and run Mopidy from the commandline

```sh
$ mopidy --config /home/pi/pokeradio-mopidy/mopidy_pokeradio/config/mopidy.conf # Probably
```

###6. Bonus points.
You will probably want to keep this running with Upstart or similar.
We have found that ours stays running stably for weeks without much prodding.
