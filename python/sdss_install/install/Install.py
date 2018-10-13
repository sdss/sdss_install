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
from sdss_install.application import Logging
from sdss_install.install4 import Install4
from sdss_install.install5 import Install5

class Install:
    '''Place install5 only related methods here. Place methods related to both install4 and install5 in another directory (install ?).'''

    def __init__(self, options=None):
        self.set_options(options=options)
        self.set_logger(options=options)
        self.initialize_data()

    def set_options(self, options=None):
        '''Set self.options wrapper'''
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

#    def set_logger(self, options=None):
#        self.logger = None
#        if options:
#            self.logging = Logging(name=options._name,
#                                   level=options.level) if options else None
#            self.logger = self.logging.logger if self.logging else None
#        if not options or not self.logger: print('ERROR: %r> Unable to set_logging.' % self.__class__)

    def set_logger(self, options=None):
        '''Set the package logger'''
        if options:
            debug = self.options.test or self.options.verbose
            self.logger = logging.getLogger('sdssinstall')
            if debug: self.logger.setLevel(logging.DEBUG)
            else: self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else: print('ERROR: Unable to set_logger. options=%r' % options)

    def initialize_data(self):
        self.ready = None
        self.url = None
        self.product = None
        self.package = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None
        self.repositories = None
        self.tags = None
        self.branches = None
        self.github_remote_url = None

    def set_install4(self):
        self.install4 = Install4(logger=self.logger, options=self.options)
        if not self.install4: self.logger.error('Unable to set self.install4')

    def set_install5(self):
        self.install5 = Install5(logger=self.logger, options=self.options)
        if not self.install5: self.logger.error('Unable to set self.install5')

    def import_data(self):
        if self.options.github:
            if self.install5:
                self.ready          = self.install5.ready
                self.repositories   = self.install5.repositories
                self.tags           = self.install5.tags
                self.branches       = self.install5.branches
                self.product        = self.install5.product
                self.directory      = self.install5.directory
        else:
            if self.install4:
                self.ready          = self.install4.ready
                self.url            = self.install4.url
                self.product        = self.install4.product
                self.package        = self.install4.package
                self.directory      = self.install4.directory
                self.svncommand     = self.install4.svncommand
                self.exists         = self.install4.exists
                self.modules        = self.install4.modules
                self.build_type     = self.install4.build_type

    def export_data(self):
        if self.options.github:
            if self.install5:
                self.install5.ready         = self.ready
                self.install5.repositories  = self.repositories
                self.install5.tags          = self.tags
                self.install5.branches      = self.branches
                self.install5.product       = self.product
                self.install5.directory     = self.directory
            else: self.logger.error('Unable to export_data to class Install5')
        else:
            if self.install4:
                self.install4.ready         = self.ready
                self.install4.url           = self.url
                self.install4.product       = self.product
                self.install4.package       = self.package
                self.install4.directory     = self.directory
                self.install4.svncommand    = self.svncommand
                self.install4.exists        = self.exists
                self.install4.modules       = self.modules
                self.install4.build_type    = self.build_type
            else: self.logger.error('Unable to export_data to class Install5')

    def set_ready(self):
        '''Call set_ready() of Install4 or Install5'''
        self.ready = self.logger and self.options
        if self.ready:
            if self.options.github:
                self.set_install5()
                if self.install5: self.install5.set_ready()
                else: self.ready = False
            else:
                self.set_install4()
                if self.install4: self.install4.set_ready()
                else: self.ready = False
            if self.ready: self.import_data()

    def set_product(self):
        '''Call set_product() of Install4 or Install5'''
        if self.ready:
            if self.options.github: self.install5.set_product()
            else:                   self.install4.set_product()
            self.import_data()

    def set_directory(self):
        '''Initialize a dictionary of directories and set 'original' to the current working directory'''
        if self.ready:
            self.directory = dict()
            try: self.directory['original'] = getcwd()
            except OSError as ose:
                self.logger.error("Check current directory: {0}".format(ose.strerror))
                self.ready = False
#            print('self.directory: %r' % self.directory) ### DEBUG ###
            self.export_data()

    def set_directory_install(self):
        '''Set the directory keys 'root' and 'install' '''
        if self.ready:
            self.import_data()
            if self.options.root is None or not isdir(self.options.root):
                if self.options.root is not None:
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
        if self.ready:
            if self.options.root is not None: environ['SDSS_INSTALL_PRODUCT_ROOT'] = self.options.root
            if self.options.longpath is not None: environ['SDSS4TOOLS_LONGPATH'] = 'True'
            self.directory['root'] = join(self.options.root, self.product['root']) if self.product['root'] else self.options.root
            self.directory['install'] = join(self.directory['root'],self.product['name'],self.product['version'])
            self.export_data()

    def set_directory_work(self):
        '''Make a work directory, to which the product and/or the module file is ultimately installed.'''
        if self.ready:
            self.import_data()
            if self.options.module_only: self.directory['work']=self.directory['install']
            else:
                self.directory['work'] = join(self.directory['original'],"%(name)s-%(version)s" % self.product)
                if isdir(self.directory['work']):
                    self.logger.info("Detected old working directory, %(work)s. Deleting..." % self.directory)
                    rmtree(self.directory['work'])
            self.export_data()

    def clean_directory_install(self):
        '''Remove existing directory (if exists if --force)'''
        if self.ready:
            self.import_data()
            if isdir(self.directory['install']) and not self.options.test:
                if self.options.force:
                    if self.directory['work'].startswith(self.directory['install']):
                        self.logger.error("Current working directory, %(work)s, is inside the install directory, %(install)s, which will be deleted via the -F (or --force) option, so please cd to another working directory and try again!" % self.directory)
                        self.ready = False
                    else:
                        self.logger.info("Preparing to install in %(install)s (overwriting due to force option)" % self.directory)
                        rmtree(self.directory['install'])
                else:
                    self.logger.error("Install directory, %(install)s, already exists!" % self.directory)
                    self.logger.info("Use the -F (or --force) option to overwrite.")
                    self.ready = False
            else: self.logger.info("Preparing to install in %(install)s" % self.directory)
            self.export_data()

    def set_github_remote_url():
        if self.ready and self.options.github and self.install5:
            self.install5.set_github_remote_url()
            self.import_data()

    def set_svncommand(self):
        '''Set the set_svncommand() of Install4'''
        if self.ready and not self.options.github: self.install4.set_svncommand()


    def set_exists(self):
        '''Call set_exists() of Install4 or Install5'''
        if self.ready:
            if not self.options.github: self.install4.set_exists()
            self.import_data()

    def fetch(self):
        '''Call set_fetch() of Install4 or Install5'''
        if self.ready:
            if self.options.github: self.install5.fetch()
            else:                   self.install4.fetch()
            self.import_data()

    def set_github_remote_url(self):
        '''Set the set_github_remote_url() of Install5'''
        if self.ready and self.options.github: self.install5.set_github_remote_url()









    def pause(self): ### DEBUG ###
        input('Press enter to continue')

