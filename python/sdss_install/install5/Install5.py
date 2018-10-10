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
from os import getcwd, environ, makedirs#, chdir, getenv, walk
from os.path import isdir, join, exists#, basename, dirname
#from argparse import ArgumentParser
#try: from ConfigParser import SafeConfigParser, RawConfigParser
#except ImportError: from configparser import SafeConfigParser, RawConfigParser
#from .most_recent_tag import most_recent_tag
#from .modules import Modules

from json import dumps ### DEBUG ###


from sdss_install.install5 import Tags
from sdss_install.install5 import Repositories
from sdss_install.install5 import Branches 

class Install5:
    '''Place install5 only related methods here. Place methods related to both install4 and install5 in another directory (install ?).'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.ready = None
        self.repositories = None
        self.tags = None
        self.branches = None
#        self.package = None
#        self.product = None
#        self.url = None
#        self.directory = None
#        self.svncommand = None
#        self.exists = None
#        self.modules = None
#        self.build_type = None

    def set_logger(self, logger=None):
        '''Set self.logger wrapper'''
        self.logger = logger if logger else None
        if not self.logger: print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        '''Set self.options wrapper'''
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    def set_ready(self):
        '''Set self.ready after sanity check self.options'''
        self.ready = self.options is not None
        if self.ready:
            self.url = self.options.url
#            print('self.options.product: %r' % self.options.product) ### DEBUG ###
#            print('self.options.product_version: %r' % self.options.product_version) ### DEBUG ###
#            print('self.options.bootstrap: %r' % self.options.bootstrap) ### DEBUG ###
            if self.options.product == 'NO PACKAGE' or self.options.product_version == 'NO VERSION':
                if self.options.bootstrap:
                    self.options.default = True
                    self.options.product = 'marvin' ### DEBUG ### sdss_install
                    tags = Tags(logger=self.logger,options=self.options)
                    self.options.product_version = tags.most_recent_tag_name()
                    self.logger.info("Selected sdss_install/{0} for bootstrap installation.".format(self.options.product_version))
                else:
                    self.logger.error("You must specify a product and the version (after a space)!")
                    self.ready = False
            elif self.options.product:
                product = self.options.product
                version = self.options.product_version
                self.repositories = Repositories(logger=self.logger,
                                            options=self.options).get_repository_names()
                self.tags = Tags(logger=self.logger,options=self.options).get_tag_names()
                self.branches = Branches(logger=self.logger,options=self.options).get_branch_names()
                valid_product = product in self.repositories
                valid_version = version == 'master' or version in self.branches or version in self.tags
                self.ready = valid_product and valid_version
#                print('self.repositories:\n' + dumps(self.repositories,indent=1)) ### DEBUG ###
#                print('self.branches:\n' + dumps(self.branches,indent=1)) ### DEBUG ###
#                print('self.tags:\n' + dumps(self.tags,indent=1)) ### DEBUG ###
#                print('valid_product: %r' % valid_product) ### DEBUG ###
#                print('valid_version: %r' % valid_version) ### DEBUG ###
#                print('self.ready: %r' % self.ready) ### DEBUG ###
#                print('product: %r' % product) ### DEBUG ###
#                print('version: %r' % version) ### DEBUG ###
        else: self.url = None
#        print('self.ready: %r' % self.ready) ### DEBUG ###

    def set_product(self):
        '''Set the self.product dictionary containing product and version names etc.'''
        if self.ready:
            self.product = dict()
            self.product['name'] = self.options.product
            self.product['root'] = None # There's no GitHub directory structure to preserve (like svn)
            self.product['version'] = self.options.product_version
            self.product['is_master'] = self.options.product_version == 'master'
            self.product['is_branch'] = self.options.product_version in self.branches
            self.product['is_tag'] = self.options.product_version in self.tags
            self.product['is_master_or_branch'] = self.product['is_master'] or self.product['is_branch']
            self.product['checkout_or_export'] = 'checkout' if self.product['is_master_or_branch'] else 'export'
#            print('self.product:\n' + dumps(self.product,indent=1)) ### DEBUG ###


    ### Same as install4 ###
    def set_directory(self):
        '''Initialize a dictionary of directories and set the key 'original' to the current working directory'''
        if self.ready:
            self.directory = dict()
            try: self.directory['original'] = getcwd()
            except OSError as ose:
                self.logger.error("Check current directory: {0}".format(ose.strerror))
                self.ready = False
#            print('self.directory: %r' % self.directory) ### DEBUG ###

    def set_directory_install(self):
        '''Set the directory keys 'root' and 'install' '''
        if self.ready:
#            print('self.options.root: %r' % self.options.root) ### DEBUG ###
#            print('isdir(self.options.root): %r' % isdir(self.options.root)) ### DEBUG ###
            # The default of self.options.root is $SDSS_INSTALL_PRODUCT_ROOT
            # if self.options.root hasn't been set at the command line or to its default value,
            # or if it has been set but the root directory hasn't been created
            if self.options.root is None or not isdir(self.options.root):
                # if self.options.root has been set at the command line or set to its default value
                if self.options.root is not None:
                    # if the root directory hasn't been created, then try to create it
                    if not exists(self.options.root):
                        try:
                            makedirs(self.options.root)
                            self.logger.info("Creating {0}".format(self.options.root))
                        except OSError as ose:
                            self.logger.error("mkdir: cannot create directory '{0}': {1}".format(self.options.root,ose.strerror))
                            self.ready = False
                    else:
                        self.logger.error("Please set the --root keyword or SDSS_INSTALL_PRODUCT_ROOT environmental variable to a valid directory.")
                        self.ready = False
                else:
                    self.logger.error("Please use the --root keyword or set a SDSS_INSTALL_PRODUCT_ROOT environmental variable.")
                    self.ready = False
        # if the root directory has been created
        if self.ready:
            if self.options.root is not None: environ['SDSS_INSTALL_PRODUCT_ROOT'] = self.options.root
            if self.options.longpath is not None: environ['SDSS4TOOLS_LONGPATH'] = 'True'
            self.directory['root'] = join(self.options.root, self.product['root']) if self.product['root'] else self.options.root
            self.directory['install'] = join(self.directory['root'],'github',self.product['name'],self.product['version'])
#            print('self.product:\n' + dumps(self.product,indent=1)) ### DEBUG ###
#            print('self.directory:\n' + dumps(self.directory,indent=1)) ### DEBUG ###


    def pause(self): ### DEBUG ###
        input('Press enter to continue')
