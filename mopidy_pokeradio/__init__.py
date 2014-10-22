from __future__ import unicode_literals

import os
from mopidy import config, exceptions, ext


__version__ = '0.1.5.3'


class Extension(ext.Extension):

    dist_name = 'Mopidy-Pokeradio'
    ext_name = 'pokeradio'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['hostname'] = config.Hostname(optional=False)
        schema['port'] = config.Integer(optional=False)
        schema['redis_db'] = config.Integer(optional=False)
        schema['redis_port'] = config.Integer(optional=True)
        schema['redis_password'] = config.Integer(optional=True)
        return schema


    def setup(self, registry):
        """ Register the frontend class of this extension
        """

        from .actor import PokeRadioFrontend
        registry.add('frontend', PokeRadioFrontend)
