# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from sys import path, version_info
from os import environ, makedirs, sep
from os.path import basename, dirname, exists, isdir, join

class Modules:

    def __init__(self, options=None, logger=None, product=None, directory=None, build_type=None):
        self.options = options
        self.logger = logger
        self.product = product
        self.directory = directory
        self.build_type = build_type
        self.ready = None
        self.dependencies = None
        self.built = None
    
    #
    # Set up Modules
    #
    def set_ready(self):
        self.ready = True
        if self.options.moduleshome is None or not isdir(self.options.moduleshome):
            self.logger.error("You do not appear to have Modules set up.")
            self.ready = False
        initpy_found = False
        for modpy in ('python','python.py'):
            initpy = join(self.options.moduleshome,'init',modpy)
            if exists(initpy):
                initpy_found = True
                try: execfile(initpy,globals())
                except NameError:
                    with open(initpy) as execfile:
                        code = compile(execfile.read(), initpy, 'exec')
                        exec(code, globals())
                break
        if not initpy_found:
            self.logger.error("Could not find the Python file in {0}/init!".format(self.options.moduleshome))
            self.ready = False
    
    #
    #  hook to module load function
    #
    def load(self,product=None,version=None):
        if product:
            product_version = join(product,version) if version else product
            try:
                module('load',product_version)
                self.logger.info("module load %s (dependency)" % product_version)
            except: self.logger.warn("unable to module load %s (dependency)" % product_version)
        else: self.logger.error("module load command requires a product [version optional]")

    def set_file(self, ext='.module'):
        alt = "_%s" % self.options.alt_module if self.options.alt_module else ""
        filename = self.product['name']+alt+ext if 'name' in self.product and ext else None
        self.file = join(self.directory['work'],'etc',filename) if filename and 'work' in self.directory else None
    #
    # Set the dependencies by looking for modules loaded in the modules file
    #
    def set_dependencies(self):
        self.dependencies = []
        if exists(self.file):
            with open(self.file) as file: lines = file.readlines()
            for product_version in [l.strip().split()[2] for l in lines if l.startswith('module load')]:
                self.dependencies.append(product_version.split('/',1) if '/' in product_version else (product_version, None))

    #
    # Load dependencies
    #
    def load_dependencies(self):
        if self.ready:
            self.set_dependencies()
            for product,version in self.dependencies: self.load(product=product,version=version)

    #
    # Set keywords to configure module
    #
    def set_keywords(self, build_type=None):
        if self.ready:
            self.keywords = {}
            self.keywords['name'] = self.product['name']
            self.keywords['version'] = self.product['version']
            self.keywords['root'] = self.directory['root']
            self.keywords['needs_bin'] = '# '
            self.keywords['needs_python'] = '# '
            self.keywords['needs_trunk_python'] = '# '
            self.keywords['needs_ld_lib'] = '# '
            self.keywords['needs_idl'] = '# '
            self.keywords['pyversion'] = "python{0:d}.{1:d}".format(*version_info)
            if isdir(join(self.directory['work'],'bin')): self.keywords['needs_bin'] = ''
            if isdir(join(self.directory['work'],'lib')): self.keywords['needs_ld_lib'] = ''
            if isdir(join(self.directory['work'],'pro')): self.keywords['needs_idl'] = ''
            if 'python' in self.build_type:
                if self.product['is_branch'] or self.product['is_trunk'] or self.options.no_python_package:
                    self.keywords['needs_trunk_python'] = ''
                else: self.keywords['needs_python'] = ''
                if not (self.product['is_branch'] or self.product['is_trunk'] or self.options.no_python_package):
                    lib_dir = join(self.directory['install'],'lib',self.keywords['pyversion'],'site-packages')
                    #
                    # If this is a python package, we need to manipulate the PYTHONPATH and
                    # include the install directory
                    #
                    if not self.options.test:
                        try:
                            makedirs(lib_dir)
                        except OSError as ose:
                            self.logger.error(ose.strerror)
                            self.ready = False
                        try:
                            newpythonpath = lib_dir + ':' + environ['PYTHONPATH']
                        except KeyError:
                            newpythonpath = lib_dir
                        environ['PYTHONPATH'] = newpythonpath
                        path.insert(int(path[0] == ''),lib_dir)
            elif isdir(join(self.directory['work'],'python')):
                self.keywords['needs_trunk_python'] = ''
            
            if basename(self.options.product)=='sdss4tools':
                self.keywords['sdss4tools_root'] = self.options.root
                self.keywords['sdss4tools_longpath'] = self.options.longpath

    #
    # check for / create a modulefile directory (if there is an etc/product.module file or for the tree product)
    #
    def check_options(self):
        if exists(self.file) or basename(self.options.product)=='tree':
            if not self.options.moduledir:
                #
                # We didn't set a module dir, so derive it from self.options.root
                #
                if self.options.longpath:
                    self.product['root'] = dirname(self.options.product) if self.options.longpath else None
                    productroot = self.product['root'][:self.product['root'].index(sep)] if self.product['root'] and sep in self.product['root'] else self.product['root']
                else: productroot = None
                self.options.moduledir = join(join(self.options.root, productroot) if productroot else self.options.root,'modulefiles')
                if not self.options.test:
                    if not isdir(self.options.moduledir):
                        self.logger.info("Creating Modules directory {0}".format(self.options.moduledir))
                        try: makedirs(self.options.moduledir)
                        except OSError as ose:
                            self.logger.error(ose.strerror)
                            self.ready = False

    #
    # Install the module file.
    #
    def set_directory(self):
        self.check_options()
        self.directory['modules'] = join(self.options.moduledir,self.product['name'])
        if self.ready and not self.options.test:
            if not isdir(self.directory['modules']):
                self.logger.info("Creating Modules directory %(modules)s" % self.directory)
                try:
                    makedirs(self.directory['modules'])
                except OSError as ose:
                    self.logger.error(ose.strerror)
                    self.ready = False


    #
    # Install the product modulefile (and versionfile if --default is specified).
    #
    def build(self):
        if self.ready:
            if exists(self.file):
                self.product['modulefile'] = join(self.directory['modules'],self.product['version'])
                with open(self.file) as file: mod = file.read().format(**self.keywords)
                if self.options.test: self.logger.debug(mod)
                else:
                    self.logger.info("Adding module file %(modulefile)s" % self.product)
                    with open(self.product['modulefile'],'w') as file: file.write(mod)
                    if self.options.default:
                        versionfile = ["#%Module1.0\n","set ModulesVersion \"%(version)s\"\n" % self.product]
                        self.product['versionfile'] = join(self.directory['modules'],'.version')
                        with open(self.product['versionfile'],'w') as file: file.writelines(versionfile)
                    self.built = True
            elif basename(self.options.product)!='tree': self.built = False

