# License information goes here
# -*- coding: utf-8 -*-
"""Install SDSS-V software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from shutil import rmtree#, copyfile, copytree
from os import getcwd, environ, makedirs, chdir, remove#, getenv, walk
from os.path import isdir, join, exists, basename, dirname
from subprocess import Popen, PIPE
from inspect import stack, getmodule
from re import search, compile, match

class Install5:
    '''Class for sdss_install'ation of GitHub repositories.'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.set_attributes()

    def set_logger(self,logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        self.ready = bool(self.logger)
        if not self.ready:
            print('ERROR: %r> Unable to set_logger.' % self.__class__)

    def set_options(self,options=None):
        '''Set command line argument options'''
        self.options = None
        if self.ready:
            self.options = options if options else None
            if not self.options:
                self.ready = False
                self.logger.error('Unable to set_options' +
                                  'self.options: {}'.format(self.options))

    def set_attributes(self):
        '''Set class attributes.'''
        self.ready = False
        self.repositories = None
        self.tags = None
        self.branches = None
        self.product = None
        self.directory = None
        self.github_remote_url = None
        self.repositories = list()
    
    def set_ready(self):
        '''
            Set self.ready after sanity check self.options and
            product/version validation
        '''
        self.ready = self.options and self.logger
        if self.ready:
            if (self.options.product         == 'NO PACKAGE' or
                self.options.product_version == 'NO VERSION'
                ):
                if self.options.bootstrap:
                    self.options.default = True
                    self.options.product = 'sdss_install'
                    self.options.product_version = self.get_bootstrap_version()
                    if self.get_valid_version() and self.ready:
                        self.logger.info(
                            "Selected sdss_install/{} for bootstrap installation."
                            .format(self.options.product_version))
                else:
                    self.ready = False
                    self.logger.error("You must specify a product " +
                                      "and the version (after a space)!")
            elif self.options.product:
                if self.options.product.endswith('/'):
                    self.options.product = dirname(self.options.product)
                if self.options.product_version.endswith('/'):
                    self.options.product_version = (
                        dirname(self.options.product_version))
                self.validate_product_and_version()
            else:
                self.ready = False
                self.logger.error('Invalid product. {} '.format(self.options.product) )

    def validate_product_and_version(self):
        '''Validate the product and product version.'''
        if self.ready:
            if self.get_valid_product():
                self.get_valid_version()

    def get_valid_product(self):
        '''Validate the product'''
        valid_product = None
        if self.ready:
            self.logger.info('Validating product')
            # check for master branch
            valid_product = self.is_type(type='repository')
            if not valid_product:
                self.ready = False
                self.logger.error('Invalid product. {} '.format(self.options.product) )
        return valid_product

    def get_valid_version(self):
        '''Validate the product version'''
        valid_version = None
        if self.ready:
            self.logger.info('Validating version')
            version = self.options.product_version
            is_master = (version == 'master')
            is_branch = True if is_master else self.is_type(type='branch')
            is_tag    = False if is_branch else self.is_type(type='tag')
            valid_version =  bool(is_master or is_branch or is_tag)
            if not valid_version:
                self.ready = False
                self.logger.error('Invalid version: {}'.format(version))
        return valid_version

    def get_bootstrap_version(self):
        '''Return latest sdss_install tag, if present, otherwise 'master'.'''
        version = 'master'
        if self.ready:
            try: product_root = environ['SDSS_INSTALL_PRODUCT_ROOT']
            except:
                product_root = None
                self.logger.error('Environmental variable not found: SDSS_INSTALL_PRODUCT_ROOT. '
                                    'Please set before running sdss_install_bootstrap.')
            sdss_install_dir = (join(product_root,'github','sdss_install')
                                if product_root else None)
            sdss_install_master_dir = (join(sdss_install_dir,'master')
                                        if sdss_install_dir else None)
            if sdss_install_master_dir and isdir(sdss_install_master_dir):
                self.logger.debug('Changing directory to: {}'.format(sdss_install_master_dir))
                chdir(sdss_install_master_dir)
                # get most recent tag information
                command = ['git','describe','--tags']
                self.logger.debug('Running command: %s' % ' '.join(command))
                (stdout,stderr,proc_returncode) = self.execute_command(command=command)
                if proc_returncode == 0:
                    # set version to most recent tag
                    regex = '^(\d+\.)(\d+\.)(\d+)'
                    matches = self.get_matches(regex=regex,string=stdout) if stdout else list()
                    match = matches[0] if matches else str()
                    if match:
                        version = match.strip()
                        # rename directory name master to version name
                        self.logger.debug('Changing directory to: {}'.format(sdss_install_dir))
                        chdir(sdss_install_dir)
                        sdss_install_version_dir = (join(sdss_install_dir,version)
                                                    if sdss_install_dir else None)
                        command = ['mv',sdss_install_master_dir,sdss_install_version_dir]
                        self.logger.debug('Running command: %s' % ' '.join(command))
                        (stdout,stderr,proc_returncode) = self.execute_command(command=command)
                        if not proc_returncode == 0:
                            self.ready = False
                            self.logger.error('Error encountered while running command: {}. '
                                                .format(' '.join(command)) +
                                              'stderr: {}.'.format(stderr.decode('utf-8')))
                    else: version = 'master'
                    self.logger.debug('Changing directory to: {}'.format(product_root))
                    chdir(product_root)
                else:
                    self.ready = False
                    self.logger.error('Error encountered while running command: {}. '
                                        .format(' '.join(command)) +
                                      'stderr: {}.'.format(stderr.decode('utf-8')))
            else:
                self.ready = False
                self.logger.error(
                    'Directory does not exist: {}. '.format(sdss_install_master_dir) +
                    'Please first set SDSS_INSTALL_PRODUCT_ROOT and clone ' +
                    'sdss_install to $SDSS_INSTALL_PRODUCT_ROOT/github/master')
        return version

    def get_matches(self,regex=None,string=None):
        matches = None
        if self.ready:
            if regex and string:
                string = str(string)
                pattern = compile(regex)
                iterator = pattern.finditer(string)
                matches = list()
                for match in iterator:
                    text = string[match.start() : match.end()] if match else None
                    if text: matches.append(text)
            else:
                self.ready = False
                self.logger.error('Unable to check_match. ' +
                                  'regex: {}'.format(regex) +
                                  'string: {}'.format(string)
                                  )
        return matches


    def set_product(self):
        '''Set self.product dict containing product and version names etc.'''
        #
        # For backwards compatibility, we will maintain the use of trunk
        # used in sdss4install for SVN, with the understanding that trunk is
        # synonomuous with master for GitHub.
        #
        if self.ready:
            self.product = dict()
            self.product['root'] = None # No GitHub directory structure to preserve, as in SVN
            self.product['name']      = self.options.product
            self.product['version']   = self.options.product_version
            self.product['is_master'] = (self.options.product_version == 'master')
            self.product['is_branch'] = (True if self.product['is_master']
                                         else self.is_type(type='branch'))
            self.product['is_tag']    = (False if self.product['is_branch']
                                         else self.is_type(type='tag'))
            self.product['is_master_or_branch'] = (self.product['is_master'] or
                                                   self.product['is_branch'])
            self.product['checkout_or_export'] = ('checkout'
                                                  if self.product['is_master_or_branch']
                                                  else 'export')

    def is_type(self,type=None):
        '''Check if the product_version is a valid Github branch.'''
        if self.ready:
            if type:
                options = {'repository' : '--heads', # for validating product
                           'branch'     : '--heads', # for validating product_version
                           'tag'        : '--tags',  # for validating product_version
                           }
                if type in options:
                    product_version = (self.options.product_version
                                       if type != 'repository'
                                       else 'master') # every product has master branch
                    url = join('git@github.com:sdss',self.options.product + '.git')
                    command = ['git',
                               'ls-remote',
                               options[type],
                               url,
                               product_version]
                    self.logger.debug('Running command: %s' % ' '.join(command))
                    (stdout,stderr,proc_returncode) = self.execute_command(command=command)
                else:
                    self.ready = False
                    self.logger.error('Invalid type. ' +
                                      "Must be 'repository', 'branch', or 'tag'. " +
                                      'type: {}'.format(type))

            else:
                self.ready = False
                self.logger.error('Unable to check is_type. ' +
                                  'type: {}'.format(type))
        return bool(stdout)

    def execute_command(self, command=None):
        '''Execute the passed terminal command.'''
        (stdout,stderr,proc_returncode) = (None,None,None)
        if command:
            proc = Popen(command, stdout=PIPE, stderr=PIPE)
            if proc:
                (stdout, stderr) = proc.communicate() if proc else (None,None)
                proc_returncode = proc.returncode if proc else None
            else:
                self.ready = False
                self.logger.error('Unable to execute_command. ' +
                                  'proc: {}'.format(proc))
        else:
            self.ready = False
            self.logger.error('Unable to execute_command. ' +
                              'command: {}'.format(command))
        return (stdout,stderr,proc_returncode)

    def set_github_remote_url(self):
        '''Set the SDSS GitHub HTTPS remote URL'''
        if self.ready:
            product = self.options.product if self.options else None
            self.github_remote_url = ('https://github.com/sdss/%s.git' % product
                                      if product else None)

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
            self.logger.debug('Running command: %s' % ' '.join(command))
            (stdout,stderr,proc_returncode) = self.execute_command(command=command)
            # NOTE: stderr is non-empty even when git clone is successful.
            if proc_returncode == 0:
                self.logger.info("Completed GitHub clone of repository %(name)s"
                                    % self.product)
            else:
                self.ready = False
                self.logger.error('Error encountered while running command: {}. '
                                    .format(' '.join(command)) +
                                  'stderr: {}.'.format(stderr.decode('utf-8')))

    def checkout(self):
        '''Checkout branch or tag, and delete .git directory if tag.'''
        if self.ready:
            if not self.product['is_master']:
                if self.product['is_branch']:
                    version = self.product['version']
                    s = 'Completed checkout of branch {}'.format(version)
                    remove = False
                elif self.product['is_tag']:
                    version = 'tags/' + self.product['version']
                    s = ('Completed checkout of tag {} '.format(version) +
                         'and removal of .git directory')
                    remove = True
                chdir(self.directory['work'])
                command = ['git','checkout',version]
                self.logger.debug('Running command: %s' % ' '.join(command))
                (stdout,stderr,proc_returncode) = self.execute_command(command=command)
                # NOTE: stderr is non-empty even when git checkout is successful.
                if proc_returncode == 0:
                    chdir(self.directory['original'])
                    if remove: self.export()
                    self.logger.info(s)
                else:
                    self.ready = False
                    self.logger.error('Error encountered while running command: {}. '
                                        .format(' '.join(command)) +
                                      'stderr: {}.'.format(stderr.decode('utf-8')))

    def export(self):
        if self.ready: rmtree(join(self.directory['work'],'.git'))


