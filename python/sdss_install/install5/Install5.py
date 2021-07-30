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
        self.product = None
        self.directory = None
        self.github_remote_url = None
        self.external_product = None
    
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

    def validate_product_and_version(self,github_url=None,product=None,version=None):
        '''Validate the product and product version.'''
        if self.ready:
            if self.get_valid_product(github_url=github_url,product=product,version=version):
                self.get_valid_version(github_url=github_url,product=product,version=version)

    def get_valid_product(self,github_url=None,product=None,version=None):
        '''Validate the product'''
        valid_product = None
        if self.ready:
            self.logger.info('Validating product')
            product = product if product else self.options.product
            # check for master/main branch
            valid_product = self.is_type(type='repository',
                                         github_url=github_url,
                                         product=product,
                                         version=version)
            if self.ready:
                if valid_product:
                    self.logger.debug('Valid product: {} '.format(product) )
                else:
                    self.ready = False
                    self.logger.error('Invalid product: {} '.format(product) )
        return valid_product

    def get_valid_version(self,github_url=None,product=None,version=None):
        '''Validate the product version'''
        valid_version = None
        if self.ready:
            version = version if version else self.options.product_version
            self.logger.info('Validating version')
            is_master = (version == 'master')
            is_main = (version == 'main')
            is_branch = True if ( is_master or is_main ) else self.is_type(type='branch',
                                                            github_url=github_url,
                                                            product=product,
                                                            version=version)
            is_tag    = False if is_branch else self.is_type(type='tag',
                                                             github_url=github_url,
                                                             product=product,
                                                             version=version)
            valid_version =  bool(is_master or is_main or is_branch or is_tag)
            if self.ready:
                if valid_version:
                    self.logger.debug('Valid version: {}'.format(version))
                else:
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
                #self.logger.debug('Running command: %s' % ' '.join(command))
                (out,err,proc_returncode) = self.execute_command(command=command)
                if proc_returncode == 0:
                    # set version to most recent tag
                    regex = '^(\d+\.)(\d+\.)(\d+)'
                    matches = self.get_matches(regex=regex,string=out) if out else list()
                    match = matches[0] if matches else str()
                    if match:
                        version = match.strip()
                        # rename directory name master to version name
                        self.logger.debug('Changing directory to: {}'.format(sdss_install_dir))
                        chdir(sdss_install_dir)
                        sdss_install_version_dir = (join(sdss_install_dir,version)
                                                    if sdss_install_dir else None)
                        command = ['mv',sdss_install_master_dir,sdss_install_version_dir]
                        #self.logger.debug('Running command: %s' % ' '.join(command))
                        (out,err,proc_returncode) = self.execute_command(command=command)
                        if not proc_returncode == 0:
                            self.ready = False
                            self.logger.error('Error encountered while running command: {}. '
                                                .format(' '.join(command)) +
                                              'err: {}.'.format(err))
                    else: version = 'master'
                    self.logger.debug('Changing directory to: {}'.format(product_root))
                    chdir(product_root)
                else:
                    self.ready = False
                    self.logger.error('Error encountered while running command: {}. '
                                        .format(' '.join(command)) +
                                      'err: {}.'.format(err))
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
                string = string.decode("utf-8") if isinstance(string,bytes) else string
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
        # synonomuous with master/main for GitHub.
        #
        if self.ready:
            self.product = dict()
            self.product['root'] = None # No GitHub directory structure to preserve, as in SVN
            self.product['name']      = self.options.product
            self.product['version']   = self.options.product_version
            self.product['is_master'] = (self.options.product_version == 'master')
            self.product['is_main'] = (self.options.product_version == 'main')
            self.product['is_branch'] = (True if ( self.product['is_master'] or self.product['is_main'] )
                                         else self.is_type(type='branch'))
            self.product['is_tag']    = (False if self.product['is_branch']
                                         else self.is_type(type='tag'))
            self.product['is_not_tag'] = (self.product['is_master'] or self.product['is_main'] or
                                                   self.product['is_branch'])
            self.product['checkout_or_export'] = ('checkout'
                                                  if self.product['is_not_tag']
                                                  else 'export')

    def is_type(self,type=None,github_url=None,product=None,version=None):
        check_type = None
        if not check_type:
            check_type = self.check_origin(type=type,github_url=github_url,product=product,version=version,origin='master')
        if not check_type:
            check_type = self.check_origin(type=type,github_url=github_url,product=product,version=version,origin='main')
        return check_type
            
    def check_origin(self,type=None,github_url=None,product=None,version=None,origin=None):
        '''Check if the product_version is a valid Github branch.'''
        if self.ready:
            if type:
                product = product if product else self.options.product
                version = version if version else self.options.product_version
                github_url = (github_url if github_url
                             else 'https://github.com/sdss' if self.options.https
                             else 'git@github.com:sdss')
                url = join(github_url,product + '.git')
                options = {'repository' : '--heads', # for validating product
                           'branch'     : '--heads', # for validating product_version
                           'tag'        : '--tags',  # for validating product_version
                           }
                if type in options:
                    product_version = (version
                                       if type != 'repository'
                                       else origin)
                    command = ['git',
                               'ls-remote',
                               options[type],
                               url,
                               product_version]
                    #self.logger.debug('Running command: %s' % ' '.join(command))
                    (out,err,proc_returncode) = self.execute_command(command=command)
                    if proc_returncode != 0:
                        regex = '(?i)Permission denied \(publickey\)'
                        matches = self.get_matches(regex=regex,string=err) if err else list()
                        match = matches[0] if matches else str()
                        s = ('While running the command\n{0}\nthe following error occurred:\n{1}\n'
                            .format(' '.join(command),err))
                        if match:
                            s += ('Please see the following URL for more informaiton: \n' +
                                  'https://help.github.com' +
                                  '/en/articles/error-permission-denied-publickey'
                                   )
                        self.ready = False
                        self.logger.error(s)
                else:
                    self.ready = False
                    self.logger.error('Invalid type. ' +
                                      "Must be 'repository', 'branch', or 'tag'. " +
                                      'type: {}'.format(type))

            else:
                self.ready = False
                self.logger.error('Unable to check is_type. ' +
                                  'type: {}'.format(type))
        return bool(out)

    def set_sdss_github_remote_url(self):
        '''Set the SDSS GitHub HTTPS remote URL'''
        self.github_remote_url = None
        if self.ready:
            product = self.options.product if self.options else None
            if product:
                self.github_remote_url = ('https://github.com/sdss/{!s}.git'.format(product)
                                          if self.options.https else
                                          'git@github.com:sdss/{!s}.git'.format(product)
                                          )

    def fetch(self):
        '''
            Clone master/main branch of product version from GitHub then checkout
            other branch or tag if necessary.
        '''
        self.clone()
        self.checkout()
        
    def clone(self):
        '''Clone the GitHub repository for the product.'''
        if self.ready:
            github_remote_url = (self.external_product['github_remote_url']
                                 if self.external_product
                                 and 'github_remote_url' in self.external_product
                                 else self.github_remote_url)
            clone_dir = (self.external_product['install_dir']
                         if self.external_product else
                         self.directory['work'])
            command = ['git','clone',github_remote_url,clone_dir]
            #self.logger.debug('Running command: %s' % ' '.join(command))
            (out,err,proc_returncode) = self.execute_command(command=command)
            # NOTE: err is non-empty even when git clone is successful.
            if proc_returncode == 0:
                self.logger.info("Completed GitHub clone of repository {}"
                                    .format(basename(github_remote_url)
                                    .replace('.git',str())))
            else:
                self.ready = False
                self.logger.error('Error encountered while running command: {}. '
                                    .format(' '.join(command)) +
                                  'err: {}.'.format(err))

    def checkout(self):
        '''Checkout branch or tag and, if tag, remove git remote origin.'''
        if self.ready:
            version = None
            install_dir = None
            if self.external_product:
                install_dir = self.external_product['install_dir']
                if self.external_product['is_master']:
                    self.logger.debug('Skipping checkout for {} branch'
                        .format(self.external_product['version']))
                else:
                    if self.external_product['is_branch']:
                        version = self.external_product['version']
                        s = 'Completed checkout of branch {}'.format(version)
                        remove = False
                    elif self.external_product['is_tag']:
                        version = 'tags/' + self.external_product['version']
                        s = ('Completed checkout of tag {} '.format(version) +
                             'and removal of git remote origin')
                        remove = True
                    else:
                        version = None
            else:
                install_dir = self.directory['work']
                if self.product['is_master']:
                    self.logger.debug('Skipping checkout for {} branch'
                        .format(self.product['version']))
                else:
                    if self.product['is_branch']:
                        version = self.product['version']
                        s = 'Completed checkout of branch {}'.format(version)
                        remove = False
                    elif self.product['is_tag']:
                        version = 'tags/' + self.product['version']
                        s = ('Completed checkout of tag {} '.format(version) +
                             'and removal of git remote origin')
                        remove = True
                    else:
                        version = None
            if version and install_dir:
                chdir(install_dir)
                command = ['git','checkout',version]
                #self.logger.debug('Running command: %s' % ' '.join(command))
                (out,err,proc_returncode) = self.execute_command(command=command)
                # NOTE: err is non-empty even when git checkout is successful.
                if proc_returncode == 0:
                    chdir(self.directory['original'])
                    if remove:     self.export()
                    if self.ready: self.logger.info(s)
                else:
                    self.ready = False
                    self.logger.error('Error encountered while running command: {}. '
                                        .format(' '.join(command)) +
                                      'err: {}.'.format(err))
            else: pass # version and install_dir can be None when is_master

    def export(self):
        '''Remove git remote origin.'''
        if self.ready:
            chdir(self.directory['work'])
            command = ['git','remote','rm','origin']
            #self.logger.debug('Running command: %s' % ' '.join(command))
            (out,err,proc_returncode) = self.execute_command(command=command)
            if not proc_returncode == 0:
                self.ready = False
                self.logger.error('Error encountered while running command: {}. '
                                    .format(' '.join(command)) +
                                  'err: {}.'.format(err))

    def execute_command(self, command=None):
        '''Execute the passed terminal command.'''
        (out,err,proc_returncode) = (None,None,None)
        if command:
            proc = Popen(command, stdout=PIPE, stderr=PIPE)
            if proc:
                (out, err) = proc.communicate() if proc else (None,None)
                out = out.decode("utf-8") if isinstance(out,bytes) else out
                err = err.decode("utf-8") if isinstance(err,bytes) else err
                proc_returncode = proc.returncode if proc else None
            else:
                self.ready = False
                self.logger.error('Unable to execute_command. ' +
                                  'proc: {}'.format(proc))
        else:
            self.ready = False
            self.logger.error('Unable to execute_command. ' +
                              'command: {}'.format(command))
        return (out,err,proc_returncode)

