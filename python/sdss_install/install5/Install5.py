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
from inspect import stack, getmodule
from sdss_install.install5 import Tags
from sdss_install.install5 import Repositories
from sdss_install.install5 import Branches 


class Install5:
    '''Class for sdss_install'ation of GitHub repositories.'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.ready = None
        self.repositories = None
        self.tags = None
        self.branches = None
        self.product = None
        self.directory = None
        self.github_remote_url = None

    def set_logger(self, logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        if not self.logger:
            print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        '''Set command line argument options'''
        self.options = options if options else None
        if not self.options:
            if self.logger: self.logger.error('Unable to set_options')
            else:           print('ERROR: Unable to set_options')

    def set_ready(self):
        '''
            Set self.ready after sanity check self.options and
            product/version validation
        '''
        self.ready = self.options and self.logger
        if self.ready:
            if (self.options.product == 'NO PACKAGE' or
                self.options.product_version == 'NO VERSION'):
                if self.options.bootstrap:
                    self.options.default = True
                    self.options.product = 'sdss_install'
                    self.options.product_version = 'master'
                    tags = Tags(logger=self.logger,options=self.options)
                    self.ready = tags
                    if self.ready:
                        tag_names = tags.get_tag_names()
                        self.options.product_version = (
                            tags.most_recent_tag_name()
                            if tag_names
                            else 'master')
                        s = ('No GitHub tags found for {}. '
                              .format(self.options.product)
                             if not tag_names
                             else str())
                        s += ("Selected sdss_install/{} for bootstrap installation."
                              .format(self.options.product_version))
                        self.logger.info(s)
                else:
                    self.logger.error("You must specify a product " +
                                      "and the version (after a space)!")
                    self.ready = False
            elif self.options.product:
                    if self.options.product.endswith('/'):
                        self.options.product = dirname(self.options.product)
                    if self.options.product_version.endswith('/'):
                        self.options.product_version = (
                            dirname(self.options.product_version))
                    self.repositories = (Repositories(logger=self.logger,
                                                     options=self.options)
                                                     .get_repository_names())
                    valid_product = self.options.product in self.repositories
                    if valid_product:
                        self.tags = Tags(logger=self.logger,
                                         options=self.options).get_tag_names()
                        self.branches = (Branches(logger=self.logger,
                                                  options=self.options)
                                                  .get_branch_names())
                        self.ready = self.tags or self.branches
                        if self.ready:
                            version = self.options.product_version
                            is_master = version == 'master'
                            is_branch = (version in self.branches
                                         if self.branches
                                         else None)
                            is_tag = version in self.tags if self.tags else None
                            valid_version =  is_master or is_branch or is_tag
                            if not valid_version:
                                self.logger.error('Invalid version: %r'
                                                    % version)
                                self.ready = False
                    else:
                        self.logger.error('Invalid product: %r'
                                            % self.options.product)
                        self.ready = False

    def set_product(self):
        '''Set self.product dict containing product and version names etc.'''
        #
        # For backwards compatibility, we will maintain the use of trunk
        # used in sdss4install for SVN, with the understanding that trunk is
        # synonomuous with master for GitHub.
        #
        if self.ready:
            self.product = dict()
            self.product['root'] = None # There's o GitHub directory structure to preserve, as in svn
            self.product['name'] = self.options.product
            self.product['version'] = self.options.product_version
            self.product['is_master'] = self.options.product_version == 'master'
            self.product['is_branch'] = (
                self.options.product_version in self.branches
                if self.branches
                else False)
            self.product['is_tag'] = (
                self.options.product_version in self.tags
                if self.tags
                else False)
            self.product['is_master_or_branch'] = (
                self.product['is_master'] or self.product['is_branch'])
            self.product['checkout_or_export'] = (
                'checkout'
                if self.product['is_master_or_branch']
                else 'export')

    def set_github_remote_url(self):
        '''Set the SDSS GitHub HTTPS remote URL'''
        if self.ready:
            product = self.options.product if self.options else None
            self.github_remote_url = ('https://github.com/sdss/%s.git' % product
                                      if product
                                      else None)

    def fetch(self):
        '''
            Clone master branch of product version from GitHub then checkout
            other branch or tag if necessary.
        '''
        self.clone()
        self.checkout()
        
    def clone(self):
        '''Clone the GitHub repository for the product.'''
        if self.ready:
            command = ['git',
                       'clone',
                       self.github_remote_url,
                       basename(self.directory['work'])]
            self.execute_command(command=command)
            if self.ready:
                self.logger.info("Completed GitHub clone of repository %(name)s"
                                    % self.product)

    def execute_command(self, command=None):
        '''Execute the passed terminal command.'''
        ### Look at Joel's Cli.py class and use it here ###
        if command:
            self.logger.info('Running command: %s' % ' '.join(command))
            proc = Popen(command, stdout=PIPE, stderr=PIPE) 
            (stdout, stderr) = proc.communicate() if proc else (None,None)
            # NOTE: stderr is non-empty even when git clone is successful.
            self.ready = proc.returncode == 0
            if not self.ready:
                s = ("Error encountered while running command: %s\n"
                        % ' '.join(command))
                s += stderr.decode('utf-8')
                self.logger.error(s)
        else: self.logger.error('Unable to execute_command')

    def checkout(self):
        '''Checkout branch or tag, and delete .git directory if tag.'''
        if self.ready and not self.product['is_master']:
            if self.product['is_branch']:
                version = self.product['version']
                s = "Completed checkout of branch %(version)s" % self.product
                remove = False
            elif self.product['is_tag']:
                version = 'tags/' + self.product['version']
                s = ("Completed checkout of tag %(version)s and removal " +
                     "of .git directory" % self.product)
                remove = True
            chdir(self.directory['work'])
            command = ['git','checkout',version]
            self.execute_command(command=command)
            chdir(self.directory['original'])
            if remove: self.export()
            self.logger.info(s)

    def export(self):
        if self.ready: rmtree(join(self.directory['work'],'.git'))


