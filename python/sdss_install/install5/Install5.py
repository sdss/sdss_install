# License information goes here
# -*- coding: utf-8 -*-
"""Install SDSS-V software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
#import glob
#import logging
#import subprocess
#import datetime
#from sys import argv, executable, path
#from shutil import copyfile, copytree, rmtree
#from os import chdir, environ, getcwd, getenv, makedirs, walk
from os.path import basename, dirname, exists, isdir, join
#from argparse import ArgumentParser
#try: from ConfigParser import SafeConfigParser, RawConfigParser
#except ImportError: from configparser import SafeConfigParser, RawConfigParser
#from .most_recent_tag import most_recent_tag
#from .modules import Modules
from json import dumps


from sdss_install.install5 import Tags
from sdss_install.install5 import Repositories

class Install5:
    '''Place install5 only related methods here. Place methods related to both install4 and install5 in another directory (install ?).'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.ready = None
#        self.package = None
#        self.product = None
#        self.url = None
#        self.directory = None
#        self.svncommand = None
#        self.exists = None
#        self.modules = None
#        self.build_type = None

    def set_logger(self, logger=None):
        self.logger = logger if logger else None
        if not self.logger: print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    #
    # Sanity check self.options
    #
    def set_ready(self):
        self.ready = self.options is not None
        if self.ready:
            self.url = self.options.url
            if self.options.product == 'NO PACKAGE' or self.options.product_version == 'NO VERSION':
                if self.options.bootstrap:
                    self.options.default = True
                    self.options.product = 'marvin' ### DEBUG ### sdss_install
                    tags = Tags(logger=self.logger,options=self.options)
                    self.options.product_version = tags.most_recent_tag_name()
#                    print('self.options.product_version: %r' % self.options.product_version)
                    self.logger.info("Selected sdss_install/{0} for bootstrap installation.".format(self.options.product_version))
                else:
                    self.logger.error("You must specify a product and the version (after a space)!")
                    self.ready = False
            elif self.options.product:
                if self.options.product.endswith('/'): self.options.product = dirname(self.options.product)
                product = self.options.product
                version = self.options.version
#                print('product: %r' % product)
#                print('version: %r' % version)

                repositories = Repositories(logger=self.logger,
                                            options=self.options).get_repository_names()
                tags = Tags(logger=self.logger,options=self.options).get_tag_names()
                valid_product = product in repositories
                valid_version = version in tags
#                print('repositories:\n' + dumps(repositories,indent=1))
#                print('tags:\n' + dumps(tags,indent=1))
#                print('valid_product: %r' % valid_product)
#                print('valid_version: %r' % valid_version)

#                self.pause()
        else: self.url = None

    def pause(self):
        input('Press enter to continue')
