# License information goes here
# -*- coding: utf-8 -*-
"""Install SDSS-IV and SDSS-V software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
import glob
import logging
import subprocess
import datetime
from sys import argv, executable, path
from shutil import copyfile, copytree, rmtree
from os import chdir, environ, getcwd, getenv, makedirs, walk
from os.path import basename, dirname, exists, isdir, join
from argparse import ArgumentParser
try: from ConfigParser import SafeConfigParser, RawConfigParser
except ImportError: from configparser import SafeConfigParser, RawConfigParser
#from .most_recent_tag import most_recent_tag
from .modules import Modules
from sdss_install.application import Argument


class Install:
    '''Place install5 only related methods here. Place methods related to both install4 and install5 in another directory (install ?).'''

    def __init__(self, options=None):
        self.options = options if options else None
        self.logger = None
        self.ready = None
        self.package = None
        self.product = None
        self.url = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None
        self.set_logger(options=options)

    #
    # Parse arguments
    #
    def set_options(self, name=None):
        self.options = Argument(name).options if name else None

    #
    # Set up self.logger
    #
    def set_logger(self, options=None):
        if options:
            debug = self.options.test or self.options.verbose
            self.logger = logging.getLogger('sdss4install')
            if debug: self.logger.setLevel(logging.DEBUG)
            else: self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else: print('ERROR: Unable to set_logger. options=%r' % options)
    


