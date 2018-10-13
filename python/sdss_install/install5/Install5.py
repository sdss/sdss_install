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
from shutil import rmtree#, copyfile, copytree
from os import getcwd, environ, makedirs, chdir, remove#, getenv, walk
from os.path import isdir, join, exists, basename, dirname
#from argparse import ArgumentParser
#try: from ConfigParser import SafeConfigParser, RawConfigParser
#except ImportError: from configparser import SafeConfigParser, RawConfigParser
#from .most_recent_tag import most_recent_tag
#from .modules import Modules

from subprocess import Popen, PIPE
from json import dumps ### DEBUG ###
from inspect import stack, getmodule

from sdss_install.install5 import Tags
from sdss_install.install5 import Repositories
from sdss_install.install5 import Branches 

class Install5:
    '''Place install5 only related methods here. Place methods related to both install4 and install5 in another directory (install ?).'''

    def __init__(self, logger=None, options=None):
        self.logger = logger if logger else None
        self.options = options if options else None
        self.ready = None
        self.repositories = None
        self.tags = None
        self.branches = None
        self.product = None
        self.directory = None
        self.github_remote_url = None

    def set_ready(self):
        '''Set self.ready after sanity check self.options'''
        self.ready = self.options is not None
        if self.ready:
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
#        print('self.ready: %r' % self.ready) ### DEBUG ###

    def set_product(self):
        '''Set the self.product dictionary containing product and version names etc.'''
        if self.ready:
            self.product = dict()
            self.product['name'] = self.options.product
            self.product['root'] = None # There's no GitHub directory structure to preserve, as in svn
            self.product['version'] = self.options.product_version
            self.product['is_master'] = self.options.product_version == 'master'
            self.product['is_branch'] = self.options.product_version in self.branches
            self.product['is_tag'] = self.options.product_version in self.tags
            self.product['is_master_or_branch'] = self.product['is_master'] or self.product['is_branch']
            self.product['checkout_or_export'] = 'checkout' if self.product['is_master_or_branch'] else 'export'
#            print('self.product:\n' + dumps(self.product,indent=1)) ### DEBUG ###

    def set_github_remote_url(self):
        '''Set the SDSS GitHub HTTPS remote URL'''
        if self.ready:
            product = self.options.product if self.options else None
            self.github_remote_url = 'https://github.com/sdss/%s.git' % product if product else None

    def fetch(self):
        '''Fetch the code from GitHub'''
        ### Look at Joel's Cli.py class and use it here ###
        if self.ready:
            command = ['git','clone',self.github_remote_url,self.directory['work']]
#            command = ['git','clone',self.github_remote_url,basename(self.directory['work'])]
            self.execute_command(command=command)
            if self.ready:
                self.logger.info("Completed GitHub clone of repository %(name)s" % self.product)
            self.checkout()

    def execute_command(self, command=None):
        if command:
            self.logger.info('Running command: %s' % ' '.join(command))
            proc = Popen(command, stdout=PIPE, stderr=PIPE) if Popen else None
            (self.stdout, self.stderr) = proc.communicate() if proc else (None,None)
            # NOTE: self.stderr is non-empty even when git clone is successful.
            self.ready = proc.returncode == 0
            if not self.ready:
                s = "Error encountered while running command: %s\n" % ' '.join(self.command)
                s += self.stderr.decode('utf-8')
                self.logger.error(s)
        else: self.logger.error('Unable to execute_command')

    def checkout(self):
        if self.ready:
            if self.product['is_branch'] and not self.product['is_master']:
                version = self.product['version']
                s = "Completed checkout of branch %(version)s" % self.product
            if self.product['is_tag']:
                version = 'tags/' + self.product['version']
                s = "Completed checkout of tag %(version)s and removal of .git directory" % self.product
            chdir(self.directory['work'])
            command = ['git','checkout',version]
            self.execute_command(command=command)
            if self.ready:
                if self.product['is_tag']: rmtree(join(self.directory['work'],'.git'))
                chdir(self.directory['original'])
                self.logger.info(s)

    def pause(self): ### DEBUG ###
        input('Press enter to continue')
