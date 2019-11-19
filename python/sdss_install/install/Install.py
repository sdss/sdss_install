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
from subprocess import Popen, PIPE
from argparse import ArgumentParser
from json import loads, dumps, load
try:
    from ConfigParser import SafeConfigParser, RawConfigParser
except ImportError:
    from configparser import SafeConfigParser, RawConfigParser
#from .most_recent_tag import most_recent_tag
from .modules import Modules
from sdss_install.application import Argument
from sdss_install.install4 import Install4
from sdss_install.install5 import Install5


class Install:
    '''
        Main class which calls Install4 and Install5
        for SVN and GitHub installations, respectively
    '''

    def __init__(self, options=None):
        self.set_options(options=options)
        self.set_logger(options=options)
        self.initialize_data()

    def set_logger(self, options=None):
        '''Set the logger used by all classes in the package.'''
        if options and logging:
            debug = self.options.test or self.options.verbose or self.options.level == 'debug'
            self.logger = logging.getLogger('sdss_install')
            if self.logger:
                if debug:
                    self.logger.setLevel(logging.DEBUG)
                else:
                    self.logger.setLevel(logging.INFO)
                handler = logging.StreamHandler()
                if debug:
                    formatter = logging.Formatter("%(name)s - " +
                                                  "%(levelname)s - " +
                                                  "%(filename)s - " +
                                                  "line %(lineno)d - " +
                                                  "%(message)s")
                else:
                    formatter = logging.Formatter("%(name)s - " +
                                                  "%(levelname)s - " +
                                                  "%(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            else:
                print('ERROR: Unable to set_logger')
        else:
            print('ERROR: Unable to set_logger. options=%r, logging=%r'
                  % (options, logging))

    def set_options(self, options=None):
        '''Set self.options wrapper'''
        self.options = options if options else None
        if not self.options:
            print('ERROR - Unable to set_options')

    def initialize_data(self):
        '''Initialize class Install data.'''
        self.ready = False
        self.url = None
        self.product = None
        self.package = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None
        self.github_remote_url = None
        self.external_product = None

    def set_install4(self):
        '''Set a class Install4 instance.'''
        self.install4 = Install4(logger=self.logger, options=self.options)
        if not self.install4:
            self.logger.error('Unable to set self.install4')

    def set_install5(self):
        '''Set a class Install5 instance.'''
        self.install5 = Install5(logger=self.logger, options=self.options)
        if not self.install5:
            self.logger.error('Unable to set self.install5')

    def import_data(self):
        '''Sync data from class Import4 or class Import5 to class Import.'''
        if self.options.github:
            if self.install5:
                self.ready = self.install5.ready
                self.product = self.install5.product
                self.directory = self.install5.directory
        else:
            if self.install4:
                self.ready = self.install4.ready
                self.url = self.install4.url
                self.product = self.install4.product
                self.package = self.install4.package
                self.directory = self.install4.directory
                self.svncommand = self.install4.svncommand
                self.exists = self.install4.exists
                self.modules = self.install4.modules
                self.build_type = self.install4.build_type

    def export_data(self):
        '''Sync class Import data to class Import4 or class Import5.'''
        if self.options.github:
            if self.install5:
                self.install5.ready = self.ready
                self.install5.product = self.product
                self.install5.directory = self.directory
            else:
                self.logger.error('Unable to export_data to class Install5')
        else:
            if self.install4:
                self.install4.ready = self.ready
                self.install4.url = self.url
                self.install4.product = self.product
                self.install4.package = self.package
                self.install4.directory = self.directory
                self.install4.svncommand = self.svncommand
                self.install4.exists = self.exists
                self.install4.modules = self.modules
                self.install4.build_type = self.build_type
            else:
                self.logger.error('Unable to export_data to class Install5')

    def set_ready(self):
        '''Call set_ready() of class Install4 or class Install5.'''
        self.ready = self.logger and self.options
        if self.ready:
            if self.options.github:
                self.set_install5()
                if self.install5:
                    self.install5.set_ready()
                else:
                    self.ready = False
            else:
                self.set_install4()
                if self.install4:
                    self.install4.set_ready()
                else:
                    self.ready = False
            if self.ready:
                self.import_data()

    def set_product(self):
        '''Call set_product() of class Install4 or class Install5.'''
        if self.ready:
            if self.options.github:
                self.install5.set_product()
            else:
                self.install4.set_product()
            self.import_data()

    def set_directory(self):
        '''
            Initialize dict self.directory and set value for key 'original' to
            current working directory.
        '''
        if self.ready:
            self.directory = dict()
            try:
                self.directory['original'] = getcwd()
            except OSError as ose:
                self.logger.error("Check current directory: {0}"
                                  .format(ose.strerror))
                self.ready = False
            self.export_data()

    def set_directory_install(self):
        '''Set dict self.directory values for keys 'root' and 'install'.'''
        if self.ready:
            self.import_data()
            if self.options.root is None or not isdir(self.options.root):
                if self.options.root is not None:
                    if not exists(self.options.root):
                        try:
                            makedirs(self.options.root)
                            self.logger.info("Creating {0}"
                                             .format(self.options.root))
                        except OSError as ose:
                            self.logger.error("mkdir: " +
                                              "cannot create directory '{0}': {1}"
                                              .format(self.options.root, ose.strerror))
                            self.ready = False
                    else:
                        self.logger.error("Please set the --root keyword or " +
                                          "SDSS_INSTALL_PRODUCT_ROOT environmental variable " +
                                          "to a valid directory.")
                        self.ready = False
                else:
                    self.logger.error("Please use the --root keyword " +
                                      "or set a SDSS_INSTALL_PRODUCT_ROOT " +
                                      "environmental variable.")
                    self.ready = False
        if self.ready:
            if self.options.root.endswith('/'):
                self.options.root = dirname(self.options.root)
            if self.options.root is not None:
                environ['SDSS_INSTALL_PRODUCT_ROOT'] = self.options.root
            if self.options.longpath is not None:
                environ['SDSS4TOOLS_LONGPATH'] = 'True'
            repo_type = 'github' if self.options.github else 'svn'
            self.directory['root'] = (
                join(self.options.root,
                     repo_type,
                     self.product['root'])
                if self.product['root']
                else join(self.options.root, repo_type))
            self.directory['install'] = join(self.directory['root'],
                                             self.product['name'],
                                             self.product['version'])
            self.export_data()

    def set_directory_work(self):
        '''
            Set dict self.directory value for key 'work',
            used to install product and/or module file.
            Remove existing work directory.
        '''
        if self.ready:
            self.import_data()
            if self.options.module_only:
                self.directory['work'] = self.directory['install']
            else:
                self.directory['work'] = join(self.directory['original'],
                                              "%(name)s-%(version)s" %
                                              self.product)
                if isdir(self.directory['work']):
                    self.logger.info("Detected old working directory, " +
                                     "%(work)s. Deleting..." % self.directory)
                    rmtree(self.directory['work'])
            self.export_data()

    def clean_directory_install(self, install_dir=None):
        '''Remove existing install directory if exists and if option --force.'''
        if self.ready:
            self.import_data()
            install_dir = install_dir if install_dir else self.directory['install']
            if isdir(install_dir) and not self.options.test:
                if self.options.force:
                    try:
                        cwd = getcwd()
                    except OSError as ose:
                        self.logger.error(
                            "Check current directory: {0}".format(ose.strerror))
                        self.ready = False
                    if self.ready:
                        if cwd.startswith(install_dir):
                            self.logger.error("Current working directory, {}, ".format(cwd) +
                                              "is inside the install directory, {}, ".format(install_dir) +
                                              "which will be deleted via the " +
                                              "-F (or --force) option, so please cd to another " +
                                              "working directory and try again!" % self.directory)
                            self.ready = False
                        else:
                            self.logger.info("Preparing to install in " +
                                             "{} (overwriting due to force option)".format(install_dir))
                            rmtree(install_dir)
                else:
                    self.logger.error("Install directory, %(install)s, already exists!"
                                      % self.directory)
                    self.logger.info("Use the -F (or --force) option " +
                                     "to overwrite.")
                    self.ready = False
            else:
                self.logger.info("Preparing to install in %(install)s"
                                 % self.directory)
            self.export_data()

    def set_sdss_github_remote_url():
        '''Wrapper for method Install5.set_sdss_github_remote_url()'''
        if self.ready and self.options.github and self.install5:
            self.install5.set_sdss_github_remote_url()
            self.import_data()

    def set_svncommand(self):
        '''Wrapper for method Install4.set_svncommand()'''
        if self.ready and not self.options.github:
            self.install4.set_svncommand()

    def set_exists(self):
        '''Call set_exists() of class Install4 or class Install5'''
        if self.ready:
            if not self.options.github:
                self.install4.set_exists()
            self.import_data()

    def fetch(self):
        '''Call set_fetch() of class Install4 or class Install5'''
        if self.ready:
            if self.options.github:
                self.install5.fetch()
            else:
                self.install4.fetch()
            self.import_data()

    def install_external_dependencies(self):
        '''Install external dependencies.'''
        if self.ready:
            if (self.options.external_dependencies and
                isinstance(self.options.external_dependencies, dict)
                ):
                for key in self.options.external_dependencies:
                    if self.ready:
                        self.external_product = dict()
                        external_dependency = self.options.external_dependencies[key]
                        install_product = (external_dependency['install_product']
                                           if external_dependency
                                           and 'install_product' in external_dependency
                                           else None)
                        paths = (external_dependency['paths']
                                 if external_dependency
                                 and 'paths' in external_dependency
                                 else None)
                        if install_product:
                            self.install_external_product(
                                install_product=install_product)
                        else:
                            self.logger.debug('No install_product found.')
                        # Needs to be called after self.install_external_product()
                        if paths:
                            self.set_external_paths(paths=paths)
                        else:
                            self.logger.debug('No PATHs found')
            else:
                self.ready = False
                self.logger.error('Failed to install external dependencies. ' +
                                  'self.options.external_dependencies: {}'
                                  .format(self.options.external_dependencies) +
                                  'isinstance(self.options.external_dependencies,dict): {}'
                                  .format(isinstance(self.options.external_dependencies, dict))
                                  )

    def install_external_product(self, install_product=None):
        '''Install external products'''
        if self.ready:
            if install_product and isinstance(install_product, dict):
                url = (install_product['url']
                       if install_product and 'url' in install_product else None)
                if url:
                    if 'github.com' in url:
                        self.install_external_github_product(
                            github_product=install_product)
                    elif 'svn.' in url:
                        self.install_external_svn_product(
                            svn_product=install_product)
                    else:
                        self.ready = False
                        self.logger.error('Encountered unsupported ' +
                                          'install_product url: {}.'.format(url))
                else:
                    self.ready = False
                    self.logger.error('Unable to install_external_product. ' +
                                      'install_product: {}, '.format(install_product) +
                                      'url: {}, '.format(url)
                                      )
            else:
                self.ready = False
                self.logger.error('Unable to install_external_product. ' +
                                  'install_product: {}, '.format(install_product) +
                                  'isinstance(install_product,dict): {}, '
                                  .format(isinstance(install_product, dict))
                                  )

    def install_external_svn_product(self, svn_product=None):
        '''Install external dependency from SVN'''
        self.ready = False
        self.logger.error('Installing external dependencies from svn is currently ' +
                          'unsupported. Please make a GitHub sdss_install issue (ticket) ' +
                          'to request that this feature be added.')

    def install_external_github_product(self, github_product=None):
        '''Install external dependency from GitHub'''
        if self.ready:
            if github_product and isinstance(github_product, dict):
                url = (github_product['url']
                       if github_product and 'url' in github_product else None)
                github_url = dirname(url) if url else None
                product = basename(url) if url else None
                version = (github_product['version']
                           if github_product and 'version' in github_product else None)
                github_remote_url = join(github_url, product)
                self.install5.validate_product_and_version(github_url=github_url,
                                                           product=product,
                                                           version=version)
                self.ready = self.ready and self.install5.ready
                if self.ready:
                    self.external_product['github_remote_url'] = github_remote_url
                    self.external_product['product'] = product
                    self.external_product['version'] = version
                    self.external_product['is_master'] = (version == 'master')
                    self.external_product['is_branch'] = (
                        True if self.external_product['is_master'] else
                        self.install5.is_type(type='branch',
                                              github_url=github_url,
                                              product=product,
                                              version=version))
                    self.external_product['is_tag'] = (
                        False if self.external_product['is_branch'] else
                        self.install5.is_type(type='tag',
                                              github_url=github_url,
                                              product=product,
                                              version=version))
                    self.ready = self.ready and self.install5.ready
                if self.ready:
                    self.set_external_product_install_dir()
                    self.clean_directory_install(
                        install_dir=dirname(self.external_product['install_dir']))
                    self.install5.external_product = self.external_product
                    self.install5.clone()
                    self.ready = self.ready and self.install5.ready
                    self.install5.checkout()
            else:
                self.ready = False
                self.logger.error('Unable to install_external_github_product. ' +
                                  'github_product: {}, '.format(github_product) +
                                  'isinstance(github_product,dict): {}, '
                                  .format(isinstance(github_product, dict))
                                  )

    def set_external_product_install_dir(self):
        '''Set the directory for external dependencies.'''
        if self.ready:
            if (self.external_product and
                'product' in self.external_product and
                        'version' in self.external_product
                ):
                install_dir = join(self.directory['root'],
                                   'external',
                                   self.external_product['product'],
                                   self.external_product['version']
                                   )
                self.external_product['install_dir'] = install_dir
                if not exists(install_dir):
                    try:
                        makedirs(install_dir)
                        self.logger.info("Creating {0}".format(install_dir))
                    except OSError as ose:
                        self.logger.error("mkdir: " +
                                          "cannot create directory '{0}': {1}"
                                          .format(install_dir, ose.strerror))
                        self.ready = False
            else:
                self.ready = False
                self.logger.error('Unable to set_external_product_install_dir. ' +
                                  'self.external_product: {}, '
                                  .format(self.external_product)
                                  )

    def set_external_paths(self, paths=None):
        '''Set external paths, like PATH, IDL_PATH, and PYTHONPATH'''
        if self.ready:
            if paths and isinstance(paths, dict):
                idl_paths = paths['idl'] if paths and 'idl' in paths else None
                shell_paths = paths['shell'] if paths and 'shell' in paths else None
                python_paths = paths['python'] if paths and 'python' in paths else None

                install_dir = (self.external_product['install_dir']
                               if self.external_product else None)
                if idl_paths:
                    for idl_path in idl_paths:
                        if self.ready:
                            path = (join(install_dir, idl_path)
                                    if install_dir and isinstance(idl_path, str)
                                    else None)
                            self.set_external_path(
                                path=path, path_type='IDL_PATH')
                elif shell_paths:
                    for shell_path in shell_paths:
                        if self.ready:
                            path = (join(install_dir, shell_path)
                                    if install_dir and isinstance(shell_path, str)
                                    else None)
                            self.set_external_path(path=path, path_type='PATH')
                elif python_paths:
                    for python_path in python_paths:
                        if self.ready:
                            path = (join(install_dir, python_path)
                                    if install_dir and isinstance(python_path, str)
                                    else None)
                            self.set_external_path(
                                path=path, path_type='PYTHONPATH')
                else:
                    self.ready = False
                    self.logger.error('Unable to set_external_paths. ' +
                                      'Encountered unsupported key in paths: {}, '.format(paths) +
                                      "Supported keys: ['idl','shell','python']"
                                      )
            else:
                self.ready = False
                self.logger.error('Unable to set_external_paths. ' +
                                  'paths: {}, '.format(paths) +
                                  'isinstance(paths,dict): {}, '
                                  .format(isinstance(paths, dict))
                                  )

    def set_external_path(self, path=None, path_type=None):
        '''Prepend the given path to the given path_type.'''
        if self.ready:
            if path and path_type:
                if path.endswith('/'):
                    path = path.rstrip('/')
                supported_path_types = ['PATH', 'IDL_PATH', 'PYTHONPATH']
                if path_type in supported_path_types:
                    old_path = None
                    try:
                        self.logger.info(
                            'Loading current {}'.format(path_type))
                        old_path = environ[path_type]
                        if old_path and path not in old_path:
                            new_path = path + ':' + old_path
                            try:
                                environ[path_type] = new_path
                                self.logger.info(
                                    'Updated {}'.format(path_type))
                                if self.options.level == 'debug':
                                    self.logger.debug("environ['{0}']: {1}"
                                                      .format(path_type, environ[path_type]))
                            except:
                                self.logger.info(
                                    'WARNING: Unable to update {}. Skipping.'.format(path_type))
                    except:
                        try:
                            environ[path_type] = path
                            self.logger.info('WARNING: Unable to set {}. '.format(path_type) +
                                             'Setting it to {}.'.format(path))
                        except:
                            self.logger.info('WARNING: Unable to set or reset {}. Skipping.'
                                             .format(path_type))

                else:
                    self.logger.info('WARNING: Unable to set_external_path. ' +
                                     'Unsupported path_type: {}. '.format(path_type) +
                                     'Supported path types: {}. '.format(
                                         supported_path_types)
                                     )
            else:
                self.logger.info('WARNING: Unable to set_external_path. ' +
                                 'path: {0}, path_type: {1}'.format(path, path_type))

    def checkout(self):
        '''Call Install5.checkout'''
        if self.ready:
            self.install5.checkout()
            self.import_data()

    def set_sdss_github_remote_url(self):
        '''Set the set_sdss_github_remote_url() of class Install5'''
        if self.ready and self.options.github:
            self.install5.set_sdss_github_remote_url()

    def reset_options_from_config(self):
        '''
            Set absent command-line options from etc/config.ini file,
            if it exists.
        '''
        # NOTE: Initially, config files only have the option [sdss4install].
        #       These options need to be duplicated for [sdss_install] in order
        #       to transition from sdss4install to sdss_install.
        # Some products may contain an optional etc/config.ini file to
        # determine the config self.options to build
        if self.ready:
            config_filename = join('etc', 'config.ini')
            config_file = join(self.directory['work'], config_filename)
            if exists(config_file):
                config = SafeConfigParser()
                try:
                    config.optionxform = unicode
                except:
                    config.optionxform = str
                if len(config.read(config_file)) == 1:
                    if config.has_section('sdss4install'):
                        self.process_install_section(config=config,
                                                     section='sdss4install')
                    if config.has_section('sdss_install'):
                        self.process_install_section(config=config,
                                                     section='sdss_install')
                    if config.has_section('envs'):
                        missing = [env for key, env in config.items('envs')
                                   if not getenv(env, None)]
                        for env in missing:
                            self.logger.error("Required environment variable " +
                                              "{0} must be set prior to sdss_install"
                                              .format(env))
                        if missing:
                            self.ready = False
                    if config.has_section('external_dependencies'):
                        self.process_install_section(config=config,
                                                     section='external_dependencies')

    def process_install_section(self, config=None, section=None):
        if config and section:
            if section == 'external_dependencies':
                if 'json_filepath' in config.options(section):
                    json_filepath = join(self.directory['work'],
                                         config.get(section, 'json_filepath'))
                    if exists(json_filepath):
                        try:
                            with open(json_filepath) as json_file:
                                self.options.external_dependencies = load(
                                    json_file)
                        except:
                            self.logger.info(
                                'WARNING: Unable to open the file {}'.format(json_filepath))
            else:
                for option in config.options(section):
                    if option == 'no_build' and not self.options.no_build:
                        try:
                            self.options.no_build = config.getboolean(section,
                                                                      option)
                            if self.options.no_build:
                                self.logger.info("Using {0} to set " +
                                                 "--no-build option"
                                                 .format(config_filename))
                        except:
                            pass
                    elif option == 'skip_module' and not self.options.skip_module:
                        try:
                            self.options.skip_module = config.getboolean(section,
                                                                         option)
                            if self.options.skip_module:
                                self.logger.info("Using {0} to set " +
                                                 "--skip_module option".format(config_filename))
                        except:
                            pass
                    elif (option == 'no_python_package' and not
                          self.options.no_python_package):
                        try:
                            self.options.no_python_package = (
                                config.getboolean(section, option))
                            if self.options.no_python_package:
                                self.logger.info("Using {0} to set " +
                                                 "--no_python_package option"
                                                 .format(config_filename))
                        except:
                            pass
                    elif option == 'make_target' and not self.options.make_target:
                        try:
                            self.options.make_target = config.get(
                                section, option)
                            if self.options.make_target:
                                self.logger.info("Using {0} to set " +
                                                 "--make_target {1} option"
                                                 .format(config_filename,
                                                         self.options.make_target))
                        except:
                            pass
                    elif option == 'evilmake' and not self.options.evilmake:
                        try:
                            self.options.evilmake = config.getboolean(section,
                                                                      option)
                            if self.options.evilmake:
                                self.logger.info("Using {0} to set " +
                                                 "--evilmake option".format(config_filename))
                        except:
                            pass
                    else:
                        self.logger.error('Unable to process_install_section. ' +
                                          'config={0}, section={1}'.format(config, section))

    def set_build_type(self):
        '''Analyze the code to determine the build type'''
        self.build_message = None
        if self.ready:
            self.build_type = list()
            if self.options.no_build:
                self.build_message = "Proceeding without build..."
            else:
                if (exists(join(self.directory['work'], 'Makefile'))
                        and self.options.evilmake):
                    self.build_message = "Installing via evilmake"
                    self.build_type.append('evilmake')
                elif (exists(join(self.directory['work'], 'setup.py'))
                      and not self.options.force_build_type):
                    self.build_type.append('python')
                    if exists(join(self.directory['work'], 'Makefile')):
                        self.build_type.append('c')
                elif exists(join(self.directory['work'], 'Makefile')):
                    self.build_type.append('c')
                if not self.build_type:
                    self.build_message = ("Proceeding without a setup.py " +
                                          "or Makefile...")

    def logger_build_message(self):
        '''Log the build message.'''
        if self.build_message:
            self.logger.info(self.build_message)

    def make_directory_install(self):
        '''Make install directory.'''
        # If this is a trunk or branch install or nothing to build,
        # this directory will be created by other means.
        if self.ready:
            if not (self.product['is_master_or_branch'] or
                    self.options.no_python_package or
                    self.options.evilmake or not
                    self.build_type or
                    self.options.test):
                try:
                    makedirs(self.directory['install'])
                except OSError as ose:
                    self.logger.error(ose.strerror)
                    self.ready = False

    def set_modules(self):
        '''Set a class Modules instance.'''
        self.modules = Modules(options=self.options,
                               logger=self.logger,
                               product=self.product,
                               directory=self.directory,
                               build_type=self.build_type)

    def set_environ(self):
        '''Set environment variables WORKING_DIR and INSTALL_DIR.'''
        if self.ready:
            environ['WORKING_DIR'] = self.directory['work']
            environ['INSTALL_DIR'] = self.directory['install']

    def build(self):
        '''Build the installed product.'''
        if self.ready:
            if (self.product['is_master_or_branch'] or
                self.options.no_python_package or
                self.options.evilmake or not
                    self.build_type):
                if self.options.test:
                    self.logger.info("Skipping install in %(install)s " +
                                     "(--test)" % self.directory)
                else:
                    self.logger.info("Installing in %(install)s" %
                                     self.directory)
                    copytree(self.directory['work'], self.directory['install'])
                    chdir(self.directory['install'])
                    if 'evilmake' in self.build_type:
                        if not self.options.skip_module:
                            self.modules.load(product=self.product['name'],
                                              version=self.product['version'])
                        command = ['evilmake', 'clean']
                        self.logger.info('Running "{0}" in {1}'
                                         .format(' '.join(command),
                                                 self.directory['install']))
                        (out, err, proc_returncode) = self.execute_command(
                            command=command)
                        self.logger.debug(out)
                        if proc_returncode != 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(err)
                        command = ['evilmake']
                        if self.options.make_target:
                            command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'
                                         .format(' '.join(command),
                                                 self.directory['install']))
                        (out, err, proc_returncode) = self.execute_command(command=command,
                                                                           argument='ignore')
                        self.logger.debug(out)
                        if proc_returncode != 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(err)
                    elif 'c' in self.build_type:
                        if not self.options.skip_module:
                            self.modules.load(product=self.product['name'],
                                              version=self.product['version'])
                        command = (['make', '-C', 'src']
                                   if exists(join(self.directory['work'], 'src'))
                                   else ['make'])
                        if self.options.make_target:
                            command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'
                                         .format(' '.join(command),
                                                 self.directory['install']))
                        (out, err, proc_returncode) = self.execute_command(
                            command=command)
                        self.logger.debug(out)
                        if proc_returncode != 0:
                            self.logger.error("Error during compile:")
                            self.logger.error(err)
                            self.ready = False
                if self.options.documentation:
                    self.logger.info('WARNING: Documentation will not be built ' +
                                     'for trunk or branch installs!')
            else:
                self.package = True
                chdir(self.directory['work'])
                if 'python' in self.build_type:
                    command = [executable,
                               'setup.py',
                               'install',
                               "--prefix=%(install)s" % self.directory]
                    self.logger.debug(' '.join(command))
                    if not self.options.test:
                        (out, err, proc_returncode) = self.execute_command(
                            command=command)
                        self.logger.debug(out)
                        if proc_returncode != 0:
                            self.logger.error("Error during installation:")
                            self.logger.error(err)
                            self.ready = False
                #
                # Copy additional files
                #
                md = None
                cf = None
                if isdir('etc'):
                    md = list()
                    cf = list()
                    for root, dirs, files in walk('etc'):
                        for d in dirs:
                            md.append(join(self.directory['install'], root, d))
                        for name in files:
                            if name.endswith('.module'):
                                continue
                            cf.append((join(root, name),
                                       join(self.directory['install'],
                                            root,
                                            name)))
                if md or cf:
                    etc_dir = join(self.directory['install'], 'etc')
                    self.logger.debug('Creating {0}'.format(etc_dir))
                    makedirs(etc_dir)
                    if md:
                        for name in md:
                            self.logger.debug('Creating {0}'.format(name))
                            if not self.options.test:
                                makedirs(name)
                    if cf:
                        for src, dst in cf:
                            self.logger.debug('Copying {0} -> {1}'
                                              .format(src, dst))
                            if not self.options.test:
                                copyfile(src, dst)

    def build_documentation(self):
        '''Build the documentaion of the installed product.'''
        if self.ready and self.options.documentation:
            if 'python' in self.build_type:
                if exists(join('doc', 'index.rst')):
                    #
                    # Assume Sphinx documentation.
                    #
                    self.logger.debug("Found Sphinx documentation.")
                    if not self.options.skip_module:
                        self.modules.load(product=self.product['name'],
                                          version=self.product['version'])
                    sphinx_keywords = {
                        'name':
                            self.product['name'],
                        'release':
                            self.product['version'],
                        'version':
                            '.'.join(self.product['version'].split('.')[0:3]),
                        'year':
                            datetime.date.today().year}
                    for sd in ('_templates', '_build', '_static'):
                        if not isdir(join('doc', sd)):
                            try:
                                makedirs(join('doc', sd))
                            except OSError as ose:
                                self.logger.error(ose.strerror)
                                self.ready = False
                    if not exists(join('doc', 'Makefile')):
                        copyfile(join(getenv('sdss_install_DIR'),
                                      'etc',
                                      'doc',
                                      'sphinx',
                                      'Makefile'),
                                 join('doc', 'Makefile'))
                    if not exists(join('doc', 'conf.py')):
                        with open(join(getenv('sdss_install_DIR'),
                                       'etc',
                                       'doc',
                                       'sphinx',
                                       'conf.py')) as conf:
                            newconf = conf.read().format(**sphinx_keywords)
                        with open(join('doc', 'conf.py'), 'w') as conf2:
                            conf2.write(newconf)
                    command = [executable, 'setup.py', 'build_sphinx']
                    self.logger.debug(' '.join(command))
                    if not self.options.test:
                        (out, err, proc_returncode) = self.execute_command(
                            command=command)
                        self.logger.debug(out)
                        if proc_returncode != 0:
                            self.logger.error(
                                "Error during documentation build:")
                            self.logger.error(err)
                            self.ready = False
                    if not self.options.test:
                        if isdir(join('build', 'sphinx', 'html')):
                            copytree(join('build', 'sphinx', 'html'),
                                     join(self.directory['install'], 'doc'))
                else:
                    self.logger.warning("Documentation build requested, " +
                                        "but no documentation found.")
            else:
                #
                # This is not a Python product, assume Doxygen documentation.
                #
                if isdir('doc'):
                    doxygen_keywords = {
                        'name':
                            self.product['name'],
                        'version':
                            self.product['version'],
                        'description':
                            ("Documentation for %(name)s built by sdss_install."
                                % self.product)}
                    if not exists(join('doc', 'Makefile')):
                        copyfile(join(getenv('sdss_install_DIR'),
                                      'etc',
                                      'doc',
                                      'doxygen',
                                      'Makefile'),
                                 join('doc', 'Makefile'))
                    if not exists(join('doc', 'Docyfile')):
                        with open(join(getenv('sdss_install_DIR'),
                                       'etc',
                                       'doc', 'doxygen', 'Doxyfile')) as conf:
                            newconf = conf.read().format(**doxygen_keywords)
                        with open(join('doc', 'Doxyfile'), 'w') as conf2:
                            conf2.write(newconf)
                else:
                    self.logger.warning("Documentation build requested, " +
                                        "but no documentation found.")

    #
    # At this point either we have already completed a Python installation
    # or we still need to compile the C/C++ product (we had to construct
    # doc/Makefile first).
    #
    def build_package(self):
        '''Build the C/C++ product.'''
        if self.ready and 'c' in self.build_type and self.package:
            environ[self.product['name'].upper()+'_DIR'] = self.directory['work']
            command = ['make', 'install']
            self.logger.debug(' '.join(command))
            if not self.options.test:
                (out, err, proc_returncode) = self.execute_command(command=command)
                self.logger.debug(out)
                if proc_returncode != 0:
                    self.logger.error("Error during compile:")
                    self.logger.error(err)
                    self.ready = False

    def clean(self):
        '''Remove the work directory tree.'''
        if self.ready:
            try:
                rmtree(self.directory['work'])
            except:
                pass

    def finalize(self):
        '''Log installation final result message.'''
        # Don't put <if self.ready> here:
        if self.directory and self.directory['original']:
            chdir(self.directory['original'])
        finalize = "Done" if self.ready else "Fail"
#        if self.options.github and self.options.module_only:
#            rmtree(join(self.product['name'],self.product['version']))
        finalize_ps = None
        if self.options.test:
            finalize = "Test " + finalize
        else:
            finalize += "!"
        if basename(self.options.product) == 'tree':
            pass
        elif self.options.skip_module:
            finalize += " (skipped modules)"
        elif self.modules and not self.modules.built:
            finalize += " (failed modules)"
            if self.modules.built == False:
                finalize_ps = "Nonexistent template %r" % self.modules.file
        elif self.modules and self.modules.built:
            finalize_ps = ("Ready to load module %(name)s/%(version)s"
                           % self.product)
        self.logger.info(finalize)
        if finalize_ps:
            self.logger.info(finalize_ps)

    def execute_command(self, command=None, argument=None):
        '''Execute the passed terminal command.'''
        (out, err, proc_returncode) = (None, None, None)
        if command:
            proc = Popen(command, stdout=PIPE, stderr=PIPE)
            if proc:
                (out, err) = proc.communicate() if proc else (None, None)
                proc_returncode = proc.returncode if proc else None
                if argument:
                    out = out.decode(
                        "utf-8", argument) if isinstance(out, bytes) else out
                    err = err.decode(
                        "utf-8", argument) if isinstance(err, bytes) else err
                else:
                    out = out.decode(
                        "utf-8") if isinstance(out, bytes) else out
                    err = err.decode(
                        "utf-8") if isinstance(err, bytes) else err
            else:
                self.ready = False
                self.logger.error('Unable to execute_command. ' +
                                  'proc: {}'.format(proc))
        else:
            self.ready = False
            self.logger.error('Unable to execute_command. ' +
                              'command: {}'.format(command))
        return (out, err, proc_returncode)
