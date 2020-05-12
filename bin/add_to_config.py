# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: add_to_config.py
# Project: bin
# Author: Brian Cherinka
# Created: Monday, 18th November 2019 6:12:06 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Monday, 18th November 2019 6:57:04 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

import os
import sys
import yaml
import argparse


def update_config(envvars):
    ''' Update the custom config with environment variables '''
    data = {row[0]: row[1] for row in envvars}
    
    custom_config_fn = os.path.expanduser('~/.{0}/{0}.yml'.format('sdss_install'))

    if os.path.exists(custom_config_fn):
        config = yaml.load(open(custom_config_fn), Loader=yaml.SafeLoader)

        # add the environment variables
        if 'envs' in config:
            config['envs'].update(data)
        else:
            config['envs'] = data

        # append to the file
        with open(custom_config_fn, 'w+') as file:
            yaml.dump(config, file)   
    else:
        # write a new custom config
        dirname = os.path.dirname(custom_config_fn)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(custom_config_fn, 'w') as file:
            yaml.dump({'envs': data}, file)


def parse_args():
    ''' Parse the arguments '''

    parser = argparse.ArgumentParser(
        prog='update your custom sdss_install.yaml config file', usage='%(prog)s [opts]')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Print extra information.', default=False)
    parser.add_argument('-e', "--envvars", nargs='*',
                        type=lambda kv: kv.split("="), dest='envvars', 
                        help='The environment variables to add to the config file; as key-value pairs')
    opts = parser.parse_args()

    return opts


def main(args):

    # parse arguments
    opts = parse_args()

    # write to config
    update_config(opts.envvars)


if __name__ == '__main__':
    main(sys.argv[1:])
