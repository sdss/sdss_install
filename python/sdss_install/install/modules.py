# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from sys import path, version_info
from os import environ, makedirs, sep
from os.path import basename, dirname, exists, isdir, join
from subprocess import Popen, PIPE
from sdss_install.utils import Module

class Modules:

    def __init__(self,
                 options=None,
                 logger=None,
                 product=None,
                 directory=None,
                 build_type=None):
        self.options = options
        self.logger = logger
        self.product = product
        self.directory = directory
        self.build_type = build_type
        self.ready = False
        self.dependencies = None
        self.built = None
        self.module = None

    def set_module(self):
        self.module = Module(logger=self.logger,options=self.options)

    def set_ready(self):
        '''Set up Modules.'''
        self.ready = (self.logger and
                      self.options and
                      self.product and
                      self.directory and
                      self.module)
        if self.ready and not self.module.ready:
            self.ready = False
            self.logger.error("You do not appear to have Modules set up.")

    def set_file(self, ext='.module'):
        '''Set product module file path.'''
        if self.ready:
            alt = "_%s" % self.options.alt_module if self.options.alt_module else ""
            filename = (self.product['name']+alt+ext
                        if 'name' in self.product and ext
                        else None)
            self.file = (join(self.directory['work'],'etc',filename)
                         if filename and 'work' in self.directory
                         else None)

    def load_dependencies(self):
        '''Load dependencies.'''
        if self.ready:
            self.set_dependencies()
            for (product,version) in self.dependencies:
                self.load(product=product,version=version)

    def set_dependencies(self):
        '''Set the dependencies by looking for modules loaded in the modules file'''
        self.dependencies = list()
        if self.ready:
            if exists(self.file):
                with open(self.file) as file: lines = file.readlines()
                from json import dumps
                for product_version in [l.strip().split()[2] for l in lines if l.startswith('module load')]:
                    self.dependencies.append(product_version.split('/',1)
                                             if '/' in product_version
                                             else (product_version, None))

    def load(self,product=None,version=None):
        '''Hook to module load function.'''
        if self.ready:
            if product:
                product_version = join(product,version) if version else product
                try:
                    self.module.set_command('load',arguments=product_version)
                    self.module.execute_command()
                    self.logger.info("module load %s (dependency)" % product_version)
                except:
                    self.logger.warning("unable to module load %s (dependency)"
                                        % product_version)
            else:
                self.logger.error("module load command requires a " +
                                    "product [version optional]")

    def set_keywords(self, build_type=None):
        '''Set keywords to configure module.'''
        if self.ready:
            self.keywords = dict()
            self.keywords['name'] = self.product['name']
            self.keywords['version'] = self.product['version']
            self.keywords['root'] = self.directory['root']
            self.keywords['needs_bin'] = '# '
            self.keywords['needs_python'] = '# '
            self.keywords['needs_trunk_python'] = '# '
            self.keywords['needs_ld_lib'] = '# '
            self.keywords['needs_idl'] = '# '
            self.keywords['pyversion'] = "python{0:d}.{1:d}".format(*version_info)
            if isdir(join(self.directory['work'],'bin')):
                self.keywords['needs_bin'] = ''
            if isdir(join(self.directory['work'],'lib')):
                self.keywords['needs_ld_lib'] = ''
            if isdir(join(self.directory['work'],'pro')):
                self.keywords['needs_idl'] = ''
            if 'python' in self.build_type:
                if (self.product['is_branch'] or
                    self.product['is_master'] or
                    self.options.no_python_package):
                    self.keywords['needs_trunk_python'] = ''
                else:
                    self.keywords['needs_python'] = ''
                    lib_dir = join(self.directory['install'],
                                   'lib',
                                   self.keywords['pyversion'],
                                   'site-packages')
                    #
                    # If this is a python package,
                    # we need to manipulate the PYTHONPATH and
                    # include the install directory
                    #
                    if not self.options.test:
                        try:
                            makedirs(lib_dir)
                        except OSError as ose:
                            self.logger.error(ose.strerror)
                            self.ready = False
                        try:
                            newpythonpath = (lib_dir +
                                             ':' +
                                             environ['PYTHONPATH'])
                        except KeyError:
                            newpythonpath = lib_dir
                        environ['PYTHONPATH'] = newpythonpath
                        path.insert(int(path[0] == ''),lib_dir)
            elif isdir(join(self.directory['work'],'python')):
                self.keywords['needs_trunk_python'] = ''

            if basename(self.options.product)=='sdss_install':
                self.keywords['sdss_install_root'] = self.options.root
                self.keywords['sdss_install_longpath'] = '# '
            elif basename(self.options.product)=='sdss4tools':
                self.keywords['sdss4tools_root'] = self.options.root
                self.keywords['sdss4tools_longpath'] = self.options.longpath

    def set_directory(self):
        '''Make module file installation directory.'''
        self.check_options()
        if self.ready:
            self.directory['modules'] = join(self.options.moduledir,
                                             self.product['name'])
            if self.ready and not self.options.test:
                if not isdir(self.directory['modules']):
                    self.logger.info("Creating Modules directory %(modules)s"
                                        % self.directory)
                    try:
                        makedirs(self.directory['modules'])
                    except OSError as ose:
                        self.logger.error(ose.strerror)
                        self.ready = False

    def check_options(self):
        '''
            Check for / create a modulefile directory
            (if there is an etc/product.module file or for the tree product)
        '''
        if self.ready:
            if exists(self.file) or basename(self.options.product)=='tree':
                if not self.options.moduledir:
                    repo_type = 'github' if self.options.github else 'svn'
                    self.options.moduledir = join(self.options.root,
                                                  repo_type,
                                                  'modulefiles')
                    if not self.options.test:
                        if not isdir(self.options.moduledir):
                            self.logger.info("Creating Modules directory {0}"
                                            .format(self.options.moduledir))
                            try: makedirs(self.options.moduledir)
                            except OSError as ose:
                                self.ready = False
                                self.logger.error(ose.strerror)

    def build(self):
        '''
            Install the product modulefile
            (and versionfile if --default is specified).
        '''
        if self.ready:
            if exists(self.file):
                self.product['modulefile'] = join(self.directory['modules'],
                                                  self.product['version'])
                with open(self.file) as file:
                    mod = file.read().format(**self.keywords)
                if self.options.test:
                    self.logger.debug(mod)
                else:
                    self.logger.info("Adding module file %(modulefile)s"
                                        % self.product)
                    with open(self.product['modulefile'],'w') as file:
                        file.write(mod)
                    if self.options.default:
                        versionfile = ["#%Module1.0\n",
                                       "set ModulesVersion \"%(version)s\"\n"
                                       % self.product]
                        self.product['versionfile'] = (
                            join(self.directory['modules'],'.version'))
                        with open(self.product['versionfile'],'w') as file:
                            file.writelines(versionfile)
                    self.built = True
            elif basename(self.options.product)!='tree': self.built = False


