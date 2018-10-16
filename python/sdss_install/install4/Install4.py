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

from json import dumps ### DEBUG ###


class Install4:

    def __init__(self, logger=None, options=None):
        self.logger = logger if logger else None
        self.options = options if options else None
        self.ready = None
        self.url = None
        self.product = None
        self.package = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None

    #
    # Sanity check self.options
    #
    def set_ready(self):
        self.ready = self.options is not None
        if self.ready:
            self.url = join(self.options.url,'public') if self.options.public else self.options.url
            if self.options.product == 'NO PACKAGE' or self.options.product_version == 'NO VERSION':
                if self.options.bootstrap:
                    self.options.default = True
                    self.options.product = 'repo/sdss/sdss4tools'
                    self.options.product_version = most_recent_tag(join(self.url,self.options.product,'tags'))
                    self.logger.info("Selected sdss4tools/{0} for bootstrap installation.".format(self.options.product_version))
                else:
                    self.logger.error("You must specify a product and the version (after a space)!")
                    self.ready = False
            elif self.options.product:
                svnroots = ['repo','data','deprecated']
                validproduct = [svnroot for svnroot in svnroots if self.options.product.startswith(svnroot)]
                if not validproduct: self.options.product = join('repo', self.options.product)
                if self.options.product.endswith('/'): self.options.product = dirname(self.options.product)
        else: self.url = None

    #
    # Determine the product and version names.
    #
    def set_product(self):
        if self.ready:
            self.product = {}
            self.product['root'] = dirname(self.options.product) if self.options.longpath else None
            self.product['name'] = basename(self.options.product)
            self.product['version'] = basename(self.options.product_version)
            self.product['is_trunk'] = self.options.product_version == 'trunk'
            self.product['is_branch'] = self.options.product_version.startswith('branches')
            self.product['is_trunk_or_branch'] = self.product['is_trunk'] or self.product['is_branch']
            self.product['url'] = self.options.product_version if self.product['is_trunk_or_branch'] else join('tags',self.options.product_version)
            self.product['url'] = join(self.url,self.options.product,self.product['url'])
            self.product['checkout_or_export'] = 'checkout' if self.product['is_trunk_or_branch'] and not self.options.public else 'export'

    #
    # Set the svn command for public or add username.
    #
    def set_svncommand(self):
        if self.ready:
            self.svncommand = ['svn']
            if not self.options.public and self.options.username: self.svncommand += ['--username', self.options.username]

    #
    # Check for existence of the product URL.
    #
    def set_exists(self):
        if self.ready:
            self.logger.info("Contacting {url} ".format(url=self.url))
            command = self.svncommand + ['ls',self.product['url']]
            self.logger.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            self.logger.debug(out)
            self.exists = proc.returncode == 0
            if self.exists: self.logger.info("Found URL at %(url)s " % self.product)
            else:
                self.logger.error("Nonexistent URL at %(url)s" % self.product)
                self.logger.error(err)
                self.ready = False
    #
    # Fetch the code from svn
    #
    def fetch(self):
        if self.ready:
            command = self.svncommand + [self.product['checkout_or_export'],self.product['url'],self.directory['work']]
            self.logger.info("Running %(checkout_or_export)s of %(url)s" % self.product)
            self.logger.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            self.logger.debug(out)
            self.ready = not len(err)
            if self.ready: self.logger.info("Completed svn %(checkout_or_export)s of %(url)s" % self.product)
            else: self.logger.error("svn error during %(checkout_or_export)s of %(url)s: " % self.product + err)

    def pause(self): ### DEBUG ###
        input('Press enter to continue')
