# License information goes here
# -*- coding: utf-8 -*-
"""Install SDSS-IV software.
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
from .most_recent_tag import most_recent_tag
from .modules import Modules

class Install:

    def __init__(self):
        self.options = None
        self.logger = None
        self.ready = None
        self.package = None
        self.product = None
        self.url = None
        self.directory = None
        self.svncommand = None
        self.exists = None
        self.modules = None
        self.build_type = None

    #
    # Parse arguments
    #
    def set_options(self):
        xct = basename(argv[0])
        parser = ArgumentParser(description=__doc__,prog=xct)
        parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
            help="Run in bootstrap mode to install the sdss4tools product.")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('-C', '--compile-c', action='store_true', dest='force_build_type',
            help="Force C/C++ install mode, even if a setup.py file is detected (WARNING: this is for experts only).")
        mode.add_argument('-E', '--evilmake', action='store_true', dest='evilmake',
            help="Use evilmake to install product.")
        mode.add_argument('-T', '--make-target', action='store', dest='make_target',
            help="Target to make when installing product.")
        parser.add_argument('-d', '--default', action='store_true', dest='default',
            help='Make this version the default version.')
        parser.add_argument('-n', '--no-build', action='store_true', dest='no_build',
            help='Skip the automated build stage')
        parser.add_argument('-s', '--skip-module', action='store_true', dest='skip_module',
            help='Skip the module load product command')
        parser.add_argument('-L', '--module-only', action='store_true', dest='module_only',
            help='Install / Reinstall only the module file')
        parser.add_argument('-P', '--no_python_package', action='store_true', dest='no_python_package',
            help='Skip the python package stage for tagged products')
        parser.add_argument('-D', '--documentation', action='store_true', dest='documentation',
            help='Build any Sphinx or Doxygen documentation.')
        parser.add_argument('-F', '--force', action='store_true', dest='force',
            help='Overwrite any existing installation of this product/version.')
        parser.add_argument('-k', '--keep', action='store_true', dest='keep',
            help='Keep the exported build directory.')
        parser.add_argument('-m', '--module-home', action='store', dest='moduleshome',
            metavar='DIR',help='Set or override the value of $MODULESHOME',
            default=getenv('MODULESHOME'))
        parser.add_argument('-a', '--alt-module', action='store', dest='alt_module',
            metavar='ALT_MODULE',help='specify an alternate module file')
        parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
            metavar='DIR',help="Install module files in DIR.",default='')
        parser.add_argument('-p', '--python', action='store', dest='python',
            metavar='PYTHON',help="Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7).  This option is only relevant when installing sdss4tools itself.")
        parser.add_argument('-r', '--root', action='store', dest='root',
            metavar='DIR', help='Set or override the value of $SDSS4_PRODUCT_ROOT',
            default=getenv('SDSS4_PRODUCT_ROOT'))
        try: longpath = eval(environ['SDSS4TOOLS_LONGPATH'])
        except: longpath = False
        parser.add_argument('-l', '--longpath', action='store_true', dest='longpath',
            help='Keep the long path hierarchy in the install directory', default=longpath)
        parser.add_argument('-t', '--test', action='store_true', dest='test',
            help='Test mode.  Do not actually install anything.')
        parser.add_argument('-u', '--url', action='store',dest='url',
            metavar='URL',help="Download software from URL.",
            default='https://svn.sdss.org')
        parser.add_argument('-g', '--public', action='store_true',dest='public',
            help="Download software from public URL.")
        parser.add_argument('-U', '--username', action='store', dest='username',
            metavar='USER',help="Specify svn --username (if necessary).")
        parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
            help='Print extra information.')
        parser.add_argument('-V', '--version', action='store_true', dest='version',
            help='Print version information.')
        parser.add_argument('product',nargs='?',default='NO PACKAGE',
            help='Name of product to install, starts with [repo, data, deprecated] or assumed to start with repo.')
        parser.add_argument('product_version',nargs='?',default='NO VERSION',
            help='Version of product to install (trunk or specified tag or branch).')
        self.options = parser.parse_args()
 
    #
    # Set up self.logger
    #
    def set_logger(self):
        debug = self.options.test or self.options.verbose
        self.logger = logging.getLogger('sdss4install')
        if debug: self.logger.setLevel(logging.DEBUG)
        else: self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
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
    # Set the original and work directory
    #
    def set_directory(self):
        if self.ready:
            self.directory = {}
            try: self.directory['original'] = getcwd()
            except OSError as ose:
                self.logger.error("Check current directory: {0}".format(ose.strerror))
                self.ready = False

    #
    # Pick an install directory
    #
    def set_directory_install(self):
        if self.ready:
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
                        self.logger.error("Please set the --root keyword or SDSS4_PRODUCT_ROOT environmental variable to a valid directory.")
                        self.ready = False
                else:
                    self.logger.error("Please use the --root keyword or set a SDSS4_PRODUCT_ROOT environmental variable.")
                    self.ready = False

        if self.ready:
            if self.options.root is not None: environ['SDSS4_PRODUCT_ROOT'] = self.options.root
            if self.options.longpath is not None: environ['SDSS4TOOLS_LONGPATH'] = 'True'
            self.directory['root'] = join(self.options.root, self.product['root']) if self.product['root'] else self.options.root
            self.directory['install'] = join(self.directory['root'],self.product['name'],self.product['version'])

    #
    # Make a work directory
    #
    def set_directory_work(self):
        if self.ready:
            if self.options.module_only: self.directory['work']=self.directory['install']
            else:
                self.directory['work'] = join(self.directory['original'],"%(name)s-%(version)s" %self.product)
                if isdir(self.directory['work']):
                    self.logger.info("Detected old working directory, %(work)s. Deleting..." % self.directory)
                    rmtree(self.directory['work'])

    #
    # Remove existing directory (if exists if --force)
    #
    def clean_directory_install(self):
        if self.ready:
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
            self.exists = len(err)==0
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

    #
    # Some products may contain an optional etc/config.ini file to determine the config self.options to build
    #
    def reset_options_from_config(self):
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
                    if config.has_section('envs'):
                        missing = [env for key,env in config.items('envs') if not getenv(env,None)]
                        for env in missing: self.logger.error("Required environment variable {0} must be set prior to sdss4install".format(env))
                        if missing: self.ready = False


    #
    # Analyze the code to determine the build type
    #
    def set_build_type(self):
        self.build_message = None
        if self.ready:
            self.build_type = []
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
        if self.build_message: self.logger.info(self.build_message)

    #
    # make install directory. If this is a trunk or branch install or nothing to build,
    # this directory will be created by other means.
    #
    def make_directory_install(self):
        if self.ready:
            if not (self.product['is_trunk_or_branch'] or self.options.no_python_package or self.options.evilmake or not self.build_type or self.options.test):
                try:
                    makedirs(self.directory['install'])
                except OSError as ose:
                    self.logger.error(ose.strerror)
                    self.ready = False
    #
    # Set up Modules
    #
    def set_modules(self):
        self.modules = Modules(options=self.options, logger=self.logger, product=self.product, directory=self.directory, build_type=self.build_type)

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


