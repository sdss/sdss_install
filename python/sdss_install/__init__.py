# encoding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import yaml
import distutils.version

from .utils import get_logger


def merge(user, default):
    """Merges a user configuration with the default one."""

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge(user[kk], vv)

    return user


def expand(config):
    ''' Expands the environment variables inside a configuration '''
    for key, val in config.items():
        if isinstance(val, dict):
            config[key] = expand(val)
        elif isinstance(val, str):
            config[key] = os.path.expandvars(val)
    return config


def add_to_os(config):
    ''' Add environment variables into the OS ''' 

    envs = config.get('envs', None)
    if not envs:
        return

    for key, val in envs.items():
        os.environ[key] = os.path.expandvars(val)


NAME = 'sdss_install'

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(path).
log = get_logger(NAME)


yaml_kwds = dict()
yaml_version = distutils.version.StrictVersion(yaml.__version__)
if yaml_version >= distutils.version.StrictVersion('5.1'):
    yaml_kwds.update(Loader=yaml.FullLoader)

# Loads config
with open(os.path.dirname(__file__) + '/etc/{0}.yml'.format(NAME)) as ff:
    config = yaml.load(ff, **yaml_kwds)

# If there is a custom configuration file, updates the defaults using it.
custom_config_fn = os.path.expanduser('~/.{0}/{0}.yml'.format(NAME))
if os.path.exists(custom_config_fn):
    config = merge(yaml.load(open(custom_config_fn), **yaml_kwds), config)

# expand any environment variables in the config
config = expand(config)
add_to_os(config)

__version__ = '0.2.2dev'
