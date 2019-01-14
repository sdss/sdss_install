# License information goes here
# -*- coding: utf-8 -*-
"""Install SDSS-IV software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from sdss_install.application import Argument

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
from .most_recent_tag import most_recent_tag

class Install4:
    '''Class for sdss_install'ation of SVN repositories.'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.ready = None
        self.url = None
        self.product = None
        self.package = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None

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
        '''Set self.ready after sanity check self.options.'''
        self.ready = self.options and self.logger
        if self.ready:
            self.url = (join(self.options.url,'public')
                        if self.options.public
                        else self.options.url)
            if (self.options.product == 'NO PACKAGE' or
                self.options.product_version == 'NO VERSION'):
                self.logger.error("You must specify a product " +
                                  "and the version (after a space)!")
                self.ready = False
            elif self.options.product:
                if self.options.product.endswith('/'):
                    self.options.product = dirname(self.options.product)
                if self.options.product_version.endswith('/'):
                    self.options.product_version = (
                        dirname(self.options.product_version))
                svnroots = ['repo','data','deprecated']
                validproduct = [svnroot for svnroot in svnroots
                                if self.options.product.startswith(svnroot)]
                if not validproduct:
                    self.options.product = join('repo',self.options.product)
        else: self.url = None

    def set_product(self):
        '''Set self.product dict containing product and version names etc.'''
        # Determine the product and version names.
        if self.ready:
            self.product = {}
            self.product['root'] = (dirname(self.options.product)
                                    if self.options.longpath
                                    else None)
            self.product['name'] = basename(self.options.product)
            self.product['version'] = basename(self.options.product_version)
            self.product['is_master'] = self.options.product_version == 'trunk'
            self.product['is_branch'] = (
                self.options.product_version.startswith('branches'))
            self.product['is_master_or_branch'] = (self.product['is_master'] or
                                                   self.product['is_branch'])
            self.product['url'] = (self.options.product_version
                                   if self.product['is_master_or_branch']
                                   else join('tags',
                                             self.options.product_version))
            self.product['url'] = join(self.url,
                                       self.options.product,
                                       self.product['url'])
            self.product['checkout_or_export'] = (
                'checkout'
                if self.product['is_master_or_branch']
                and not self.options.public
                else 'export')

    def set_svncommand(self):
        '''
            Set the SVN command for public,
            otherwise add username to SVN command.
        '''
        if self.ready:
            self.svncommand = ['svn']
            if not self.options.public and self.options.username:
                self.svncommand += ['--username', self.options.username]

    def set_exists(self):
        '''Check for existence of the product URL.'''
        if self.ready:
            self.logger.info("Contacting {url} ".format(url=self.url))
            command = self.svncommand + ['ls',self.product['url']]
            self.logger.debug(' '.join(command))
            proc = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, err = proc.communicate()
            self.logger.debug(out)
            self.exists = proc.returncode == 0
            if self.exists:
                self.logger.info("Found URL at %(url)s " % self.product)
            else:
                self.logger.error("Nonexistent URL at %(url)s" % self.product)
                self.logger.error(err)
                self.ready = False

    def fetch(self):
        '''SVN checkout or export the product version.'''
        if self.ready:
            command = (self.svncommand +
                       [self.product['checkout_or_export'],
                        self.product['url'],
                        self.directory['work']])
            self.logger.info("Running %(checkout_or_export)s of %(url)s"
                             % self.product)
            self.logger.debug(' '.join(command))
            proc = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, err = proc.communicate()
            self.logger.debug(out)
            self.ready = not len(err)
            if self.ready:
                self.logger.info("Completed svn %(checkout_or_export)s " +
                                 "of %(url)s" % self.product)
            else: self.logger.error("svn error during %(checkout_or_export)s " +
                                    "of %(url)s: " % self.product + err)
