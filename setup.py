from __future__ import unicode_literals

import re
from setuptools import setup


def get_version(filename):
    content = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
    return metadata['version']


setup(
    name='Mopidy-Pokeradio',
    version=get_version('mopidy_pokeradio/__init__.py'),
    url='http://pokelondon.com',
    license='Apache License, Version 2.0',
    author='Adam Edwards',
    author_email='adam@pokelondon.com',
    description='Very short description',
    package=['mopidy_pokeradio'],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'pyspotify == 1.11',
        'setuptools',
        'Mopidy == 0.19.4', # Be careful with this version. Or the ext wont load
        'Mopidy-Spotify == 1.2',
        'simplejson == 3.3.1',
        'requests',
        'redis == 2.8.0',
    ],
    entry_points={
        'mopidy.ext': [
            'pokeradio = mopidy_pokeradio:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players'
    ],
)

