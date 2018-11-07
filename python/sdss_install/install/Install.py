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
    '''Main class which calls Install4 and Install5 for SVN and GitHub installations, respectively'''

    def __init__(self, options=None):
        self.set_options(options=options)
        self.set_logger(options=options)
        self.initialize_data()

    def set_options(self, options=None):
        '''Set self.options wrapper'''
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    def set_logger(self, options=None):
        '''Set the logger used by all classes in the package.'''
        if options and logging:
            debug = self.options.test or self.options.verbose
            self.logger = logging.getLogger('sdssinstall')
            if self.logger:
                if debug: self.logger.setLevel(logging.DEBUG)
                else: self.logger.setLevel(logging.INFO)
                handler = logging.StreamHandler()
                formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            else: print('ERROR: Unable to set_logger')
        else: print('ERROR: Unable to set_logger. options=%r, logging=%r'
                    % (options,logging))

    def initialize_data(self):
        '''Initialize class Install data.'''
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
        '''Set a class Install4 instance.'''
        self.install4 = Install4(logger=self.logger, options=self.options)
        if not self.install4: self.logger.error('Unable to set self.install4')

    def set_install5(self):
        '''Set a class Install5 instance.'''
        self.install5 = Install5(logger=self.logger, options=self.options)
        if not self.install5: self.logger.error('Unable to set self.install5')

    def import_data(self):
        '''Sync data from class Import4 or class Import5 to class Import.'''
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
        '''Sync class Import data to class Import4 or class Import5.'''
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
        '''Call set_ready() of class Install4 or class Install5.'''
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
        '''Call set_product() of class Install4 or class Install5.'''
        if self.ready:
            if self.options.github: self.install5.set_product()
            else:                   self.install4.set_product()
            self.import_data()

    def set_directory(self):
        '''Initialize dict self.directory and set value for key 'original' to current working directory.'''
        if self.ready:
            self.directory = dict()
            try: self.directory['original'] = getcwd()
            except OSError as ose:
                self.logger.error("Check current directory: {0}".format(ose.strerror))
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
            if self.options.root.endswith('/'): self.options.root = dirname(self.options.root)
            if self.options.root is not None: environ['SDSS_INSTALL_PRODUCT_ROOT'] = self.options.root
            if self.options.longpath is not None: environ['SDSS4TOOLS_LONGPATH'] = 'True'
            self.directory['root'] = join(self.options.root, self.product['root']) if self.product['root'] else self.options.root
            self.directory['install'] = join(self.directory['root'],self.product['name'],self.product['version'])
            self.export_data()

    def set_directory_work(self):
        '''Set dict self.directory value for key 'work', used to install product and/or module file. Remove existing work directory.'''
        if self.ready:
            self.import_data()
            if self.options.module_only:
                self.directory['work']=self.directory['install']
            else:
                self.directory['work'] = join(self.directory['original'],"%(name)s-%(version)s" % self.product)
                if isdir(self.directory['work']):
                    self.logger.info("Detected old working directory, %(work)s. Deleting..." % self.directory)
                    rmtree(self.directory['work'])
            self.export_data()

    def clean_directory_install(self):
        '''Remove existing install directory if exists and if option --force.'''
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
        '''Wrapper for method Install5.set_github_remote_url()'''
        if self.ready and self.options.github and self.install5:
            self.install5.set_github_remote_url()
            self.import_data()

    def set_svncommand(self):
        '''Wrapper for method Install4.set_svncommand()'''
        if self.ready and not self.options.github: self.install4.set_svncommand()

    def set_exists(self):
        '''Call set_exists() of class Install4 or class Install5'''
        if self.ready:
            if not self.options.github: self.install4.set_exists()
            self.import_data()

    def fetch(self):
        '''Call set_fetch() of class Install4 or class Install5'''
        if self.ready:
            if self.options.github: self.install5.fetch()
            else:                   self.install4.fetch()
            self.import_data()

    def set_github_remote_url(self):
        '''Set the set_github_remote_url() of class Install5'''
        if self.ready and self.options.github: self.install5.set_github_remote_url()

    def reset_options_from_config(self):
        '''Set absent command-line options from etc/config.ini file, if it exists.'''
        # NOTE: Initially, config files only have the option [sdss4install].
        #       These options need to be duplicated for [sdss_install] in order to transition
        #       from sdss4install to sdss_install.
        # Some products may contain an optional etc/config.ini file to determine the config self.options to build
        if self.ready:
            config_filename = join('etc','config.ini')
            config_file = join(self.directory['work'],config_filename)
            if exists(config_file):
                config = SafeConfigParser()
                try: config.optionxform = unicode
                except: config.optionxform = str
                if len(config.read(config_file))==1:
                    if config.has_section('sdss4install'):
                        for option in config.options('sdss4install'):
                            if option=='no_build' and not self.options.no_build:
                                try:
                                    self.options.no_build = config.getboolean('sdss4install',option)
                                    if self.options.no_build: self.logger.info("Using {0} to set --no-build option".format(config_filename))
                                except: pass
                            elif option=='skip_module' and not self.options.skip_module:
                                try:
                                    self.options.skip_module = config.getboolean('sdss4install',option)
                                    if self.options.skip_module: self.logger.info("Using {0} to set --skip_module option".format(config_filename))
                                except: pass
                            elif option=='no_python_package' and not self.options.no_python_package:
                                try:
                                    self.options.no_python_package = config.getboolean('sdss4install',option)
                                    if self.options.no_python_package: self.logger.info("Using {0} to set --no_python_package option".format(config_filename))
                                except: pass
                            elif option=='make_target' and not self.options.make_target:
                                try:
                                    self.options.make_target = config.get('sdss4install',option)
                                    if self.options.make_target: self.logger.info("Using {0} to set --make_target {1} option".format(config_filename,self.options.make_target))
                                except: pass
                            elif option=='evilmake' and not self.options.evilmake:
                                try:
                                    self.options.evilmake = config.getboolean('sdss4install',option)
                                    if self.options.evilmake: self.logger.info("Using {0} to set --evilmake option".format(config_filename))
                                except: pass
                    else: self.logger.info('NOTE: In the product config.ini file, sdss4install might need to be replaced with sdss_install')

                    if config.has_section('envs'):
                        missing = [env for key,env in config.items('envs') if not getenv(env,None)]
                        for env in missing: self.logger.error("Required environment variable {0} must be set prior to sdss_install".format(env))
                        if missing: self.ready = False

    def set_build_type(self):
        '''Analyze the code to determine the build type'''
        self.build_message = None
        if self.ready:
            self.build_type = list()
            if self.options.no_build: self.build_message = "Proceeding without build..."
            else:
                if exists(join(self.directory['work'],'Makefile')) and self.options.evilmake:
                    self.build_message = "Installing via evilmake"
                    self.build_type.append('evilmake')
                elif exists(join(self.directory['work'],'setup.py')) and not self.options.force_build_type:
                    self.build_type.append('python')
                    if exists(join(self.directory['work'],'Makefile')): self.build_type.append('c')
                elif exists(join(self.directory['work'],'Makefile')): self.build_type.append('c')
                if not self.build_type: self.build_message = "Proceeding without a setup.py or Makefile..."

    def logger_build_message(self):
        '''Log the build message.'''
        if self.build_message: self.logger.info(self.build_message)

    def make_directory_install(self):
        '''Make install directory.'''
        # If this is a trunk or branch install or nothing to build,
        # this directory will be created by other means.
        if self.ready:
            if not (self.product['is_master_or_branch'] or self.options.no_python_package or self.options.evilmake or not self.build_type or self.options.test):
                try:
                    makedirs(self.directory['install'])
                except OSError as ose:
                    self.logger.error(ose.strerror)
                    self.ready = False

    def set_modules(self):
        '''Set a class Modules instance.'''
        self.modules = Modules(options=self.options, logger=self.logger, product=self.product, directory=self.directory, build_type=self.build_type)

    def set_environ(self):
        '''Set environment variables WORKING_DIR and INSTALL_DIR.'''
        if self.ready:
            environ['WORKING_DIR'] = self.directory['work']
            environ['INSTALL_DIR'] = self.directory['install']

    def build(self):
        '''Build the installed product.'''
        if self.ready:
            if self.product['is_master_or_branch'] or self.options.no_python_package or self.options.evilmake or not self.build_type:
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
                        (out, err) = proc.communicate() if proc else (None,None)
                        self.logger.debug(out)
                        if proc.returncode != 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(err)
                        command = ['evilmake']
                        if self.options.make_target: command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'.format(' '.join(command),self.directory['install']))
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        (out, err) = proc.communicate() if proc else (None,None)
                        self.logger.debug(out)
                        if proc.returncode != 0:
                            self.logger.error("Evilmake response:")
                            self.logger.error(unicode(err, errors='ignore'))
                    elif 'c' in self.build_type:
                        if not self.options.skip_module: self.modules.load(product=self.product['name'],version=self.product['version'])
                        command = ['make','-C', 'src'] if exists(join(self.directory['work'],'src')) else ['make']
                        if self.options.make_target: command += [self.options.make_target]
                        self.logger.info('Running "{0}" in {1}'.format(' '.join(command),self.directory['install']))
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        (out, err) = proc.communicate() if proc else (None,None)
                        self.logger.debug(out)
                        if proc.returncode != 0:
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
                        (out, err) = proc.communicate() if proc else (None,None)
                        self.logger.debug(out)
                        if proc.returncode != 0:
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

    def build_documentation(self):
        '''Build the documentaion of the installed product.'''
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
                        copyfile(join(getenv('sdss_install_DIR'),'etc','doc','sphinx','Makefile'),
                            join('doc','Makefile'))
                    if not exists(join('doc','conf.py')):
                        with open(join(getenv('sdss_install_DIR'),'etc','doc','sphinx','conf.py')) as conf:
                            newconf = conf.read().format(**sphinx_keywords)
                        with open(join('doc','conf.py'),'w') as conf2:
                            conf2.write(newconf)
                    command = [executable, 'setup.py', 'build_sphinx']
                    self.logger.debug(' '.join(command))
                    if not self.options.test:
                        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        (out, err) = proc.communicate() if proc else (None,None)
                        self.logger.debug(out)
                        if proc.returncode != 0:
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
                        'description':"Documentation for %(name)s built by sdss_install." % self.product}
                    if not exists(join('doc','Makefile')):
                        copyfile(join(getenv('sdss_install_DIR'),'etc','doc','doxygen','Makefile'),
                            join('doc','Makefile'))
                    if not exists(join('doc','Docyfile')):
                        with open(join(getenv('sdss_install_DIR'),'etc','doc','doxygen','Doxyfile')) as conf:
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
        '''Build the C/C++ product.'''
        if self.ready and 'c' in self.build_type and self.package:
            environ[self.product['name'].upper()+'_DIR'] = self.directory['work']
            command = ['make', 'install']
            self.logger.debug(' '.join(command))
            if not self.options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                (out, err) = proc.communicate() if proc else (None,None)
                self.logger.debug(out)
                if proc.returncode != 0:
                    self.logger.error("Error during compile:")
                    self.logger.error(err)
                    self.ready = False

    def clean(self):
        '''Remove the work directory tree.'''
        if self.ready:
            try: rmtree(self.directory['work'])
            except: pass

    def finalize(self):
        '''Log installation final result message.'''
        if self.directory['original']: chdir(self.directory['original'])
        finalize = "Done" if self.ready else "Fail"
#        if self.options.github and self.options.module_only:
#            rmtree(join(self.product['name'],self.product['version']))
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
