from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from sys import argv
from os import environ, getenv
from os.path import basename
from argparse import ArgumentParser

class Argument:
    
    def __init__(self, name=None):
        self.get_options = globals()[name] if name in globals().keys() else None
        self.options = self.get_options() if self.get_options else None
        self.options._name = name if self.options else None

def sdss4install():
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
    return parser.parse_args()

def sdssinstall():
    xct = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=xct)
    parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
        help="Run in bootstrap mode to install the sdss_install product.")
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
        metavar='PYTHON',help="Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7).  This option is only relevant when installing sdss_install itself.")
    parser.add_argument('-r', '--root', action='store', dest='root',
        metavar='DIR', help='Set or override the value of $SDSS_INSTALL_PRODUCT_ROOT',
        default=getenv('SDSS_INSTALL_PRODUCT_ROOT'))
    try: longpath = eval(environ['SDSS_INSTALL_LONGPATH'])
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
    return parser.parse_args()

