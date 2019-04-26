# encoding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import yaml
import distutils.version

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(name).
from .utils import log


def merge(user, default):
    """Merges a user configuration with the default one."""

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge(user[kk], vv)

    return user


NAME = 'sdss_install'

# Loads config
yaml_version = distutils.version.StrictVersion(yaml.__version__)
with open(os.path.dirname(__file__) + '/etc/{0}.yml'.format(NAME)) as ff:
    if yaml_version >= distutils.version.StrictVersion('5.1'):
        config = yaml.load(ff, Loader=yaml.FullLoader)
    else:
        config = yaml.load(ff)

# If there is a custom configuration file, updates the defaults using it.
custom_config_fn = os.path.expanduser('~/.{0}/{0}.yml'.format(NAME))
if os.path.exists(custom_config_fn):
    config = merge(yaml.load(open(custom_config_fn)), config)


__version__ = '0.2.2dev'
