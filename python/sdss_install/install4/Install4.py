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

    def make_directory_install(self):
        '''Make install directory'''
        # If this is a trunk or branch install or nothing to build,
        # this directory will be created by other means.
        if self.ready:
            print("self.directory['install']: %r" % self.directory['install'])
            if not (self.product['is_trunk_or_branch'] or self.options.no_python_package or self.options.evilmake or not self.build_type or self.options.test):
                try:
                    makedirs(self.directory['install'])
                except OSError as ose:
                    self.logger.error(ose.strerror)
                    self.ready = False

    #
    # Set up some convenient environment variables.
    #
    def set_environ(self):
        if self.ready:
            environ['WORKING_DIR'] = self.directory['work']
            environ['INSTALL_DIR'] = self.directory['install']

    #
    # Build the install
    #
    def build(self):
        if self.ready:
            if self.product['is_trunk_or_branch'] or self.options.no_python_package or self.options.evilmake or not self.build_type:
                if self.options.test:
                    self.logger.info("Skipping install in %(install)s (--test)" % self.directory)
                else:
                    self.logger.info("Installing in %(install)s" % self.directory)
                    copytree(self.directory['work'],self.directory['install'])
                    chdir(self.directory['install'])
                    if 'evilmake' in self.build_type:
                        if not self.options.skip_module: self.modules.load(product=self.product['name'],version=self.product['version'])
                        command = ['evilmake','clean']
                        self.logger.info('Running "{0}" in {1}'.format(' '.join(command),self.directory['install']))
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        self.logger.debug(out)
                        if len(err) > 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(err)
                        command = ['evilmake']
                        if self.options.make_target: command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'.format(' '.join(command),self.directory['install']))
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        self.logger.debug(out)
                        if len(err) > 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(unicode(err, errors='ignore'))
                    elif 'c' in self.build_type:
                        if not self.options.skip_module: self.modules.load(product=self.product['name'],version=self.product['version'])
                        command = ['make','-C', 'src'] if exists(join(self.directory['work'],'src')) else ['make']
                        if self.options.make_target: command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'.format(' '.join(command),self.directory['install']))
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        self.logger.debug(out)
                        if len(err) > 0:
                            self.logger.error("Error during compile:")
                            self.logger.error(err)
                            self.ready = False
                if self.options.documentation:
                    self.logger.warn('Documentation will not be built for trunk or branch installs!')
            else:
                self.package = True
                chdir(self.directory['work'])
                if 'python' in self.build_type:
                    command = [executable, 'setup.py', 'install', "--prefix=%(install)s" % self.directory]
                    self.logger.debug(' '.join(command))
                    if not self.options.test:
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        self.logger.debug(out)
                        if len(err) > 0:
                            self.logger.error("Error during installation:")
                            self.logger.error(err)
                            self.ready = False
                #
                # Copy additional files
                #
                if isdir('etc'):
                    md = list()
                    cf = list()
                    for root, dirs, files in walk('etc'):
                        for d in dirs:
                            md.append(join(self.directory['install'],root,d))
                        for name in files:
                            if name.endswith('.module'):
                                continue
                            cf.append((join(root,name),join(self.directory['install'],root,name)))
                if md or cf:
                    etc_dir = join(self.directory['install'],'etc')
                    self.logger.debug('Creating {0}'.format(etc_dir))
                    makedirs(etc_dir)
                    if md:
                        for name in md:
                            self.logger.debug('Creating {0}'.format(name))
                            if not self.options.test:
                                makedirs(name)
                    if cf:
                        for src,dst in cf:
                            self.logger.debug('Copying {0} -> {1}'.format(src,dst))
                            if not self.options.test:
                                copyfile(src,dst)
    #
    # Build documentation
    #
    def build_documentation(self):
        if self.ready and self.options.documentation:
            if 'python' in self.build_type:
                if exists(join('doc','index.rst')):
                    #
                    # Assume Sphinx documentation.
                    #
                    self.logger.debug("Found Sphinx documentation.")
                    if not self.options.skip_module: self.modules.load(product=self.product['name'],version=self.product['version'])
                    sphinx_keywords = {
                        'name':self.product['name'],
                        'release':self.product['version'],
                        'version':'.'.join(self.product['version'].split('.')[0:3]),
                        'year':datetime.date.today().year}
                    for sd in ('_templates','_build','_static'):
                        if not isdir(join('doc',sd)):
                            try:
                                makedirs(join('doc',sd))
                            except OSError as ose:
                                self.logger.error(ose.strerror)
                                self.ready = False
                    if not exists(join('doc','Makefile')):
                        copyfile(join(getenv('sdss4tools_DIR'),'etc','doc','sphinx','Makefile'),
                            join('doc','Makefile'))
                    if not exists(join('doc','conf.py')):
                        with open(join(getenv('sdss4tools_DIR'),'etc','doc','sphinx','conf.py')) as conf:
                            newconf = conf.read().format(**sphinx_keywords)
                        with open(join('doc','conf.py'),'w') as conf2:
                            conf2.write(newconf)
                    command = [executable, 'setup.py', 'build_sphinx']
                    self.logger.debug(' '.join(command))
                    if not self.options.test:
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        self.logger.debug(out)
                        if len(err) > 0:
                            self.logger.error("Error during documentation build:")
                            self.logger.error(err)
                            self.ready = False
                    if not self.options.test:
                        if isdir(join('build','sphinx','html')):
                            copytree(join('build','sphinx','html'),join(self.directory['install'],'doc'))
                else:
                    self.logger.warn("Documentation build requested, but no documentation found.")
            else:
                #
                # This is not a Python product, assume Doxygen documentation.
                #
                if isdir('doc'):
                    doxygen_keywords = {
                        'name':self.product['name'],
                        'version':self.product['version'],
                        'description':"Documentation for %(name)s built by sdss4install." % self.product}
                    if not exists(join('doc','Makefile')):
                        copyfile(join(getenv('sdss4tools_DIR'),'etc','doc','doxygen','Makefile'),
                            join('doc','Makefile'))
                    if not exists(join('doc','Docyfile')):
                        with open(join(getenv('sdss4tools_DIR'),'etc','doc','doxygen','Doxyfile')) as conf:
                            newconf = conf.read().format(**doxygen_keywords)
                        with open(join('doc','Doxyfile'),'w') as conf2:
                            conf2.write(newconf)
                else:
                    self.logger.warn("Documentation build requested, but no documentation found.")

    #
    # At this point either we have already completed a Python installation
    # or we still need to compile the C/C++ product (we had to construct
    # doc/Makefile first).
    #
    def build_package(self):
        if self.ready and 'c' in self.build_type and self.package:
            environ[self.product['name'].upper()+'_DIR'] = self.directory['work']
            command = ['make', 'install']
            self.logger.debug(' '.join(command))
            if not self.options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                self.logger.debug(out)
                if len(err) > 0:
                    self.logger.error("Error during compile:")
                    self.logger.error(err)
                    self.ready = False

    #
    # Clean up
    #
    def clean(self):
        try: rmtree(self.directory['work'])
        except: pass

    #
    # Done
    #
    def finalize(self):
        if self.directory['original']: chdir(self.directory['original'])
        finalize = "Done" if self.ready else "Fail"
        finalize_ps = None
        if self.options.test: finalize = "Test " + finalize
        else: finalize += "!"
        if basename(self.options.product)=='tree': pass
        elif self.options.skip_module: finalize += " (skipped modules)"
        elif self.modules and not self.modules.built:
            finalize += " (failed modules)"
            if self.modules.built==False: finalize_ps = "Nonexistent template %r" % self.modules.file
        elif self.modules and self.modules.built: finalize_ps = "Ready to load module %(name)s/%(version)s" % self.product
        self.logger.info(finalize)
        if finalize_ps: self.logger.info(finalize_ps)


    def pause(self): ### DEBUG ###
        input('Press enter to continue')
