# encoding: utf-8
#
# conftest.py
#


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals


"""
Here you can add fixtures that will be used for all the tests in this
directory. You can also add conftest.py files in underlying subdirectories.
Those conftest.py will only be applies to the tests in that subdirectory and
underlying directories. See https://docs.pytest.org/en/2.7.3/plugins.html for
more information.
"""

import pytest
import sys
import os
import shutil
import subprocess
from sdss_install.application import Argument
from sdss_install.install import Install


@pytest.fixture(scope='function', autouse=True)
def monkey_setup(monkeypatch, tmpdir):
    ''' Fixture that automatically sets up a temporary install directory '''
    tmproot = tmpdir.mkdir("software").mkdir("sdss")
    tmpwork = tmproot.mkdir("work")
    tmpgit = tmproot.mkdir("github")
    tmpsvn = tmproot.mkdir("svn")
    tmpgitmod = tmpgit.mkdir("modulefiles")
    tmpsvnmod = tmpsvn.mkdir("modulefiles")
    # change to working directory
    os.chdir(tmpwork)

    sdss_install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    #shutil.copytree(sdss_install_dir, tmpgit / 'sdss_install/master')
    #sdss_install_dir = tmpgit / 'sdss_install/master'

    monkeypatch.setenv("SDSS_INSTALL_PRODUCT_ROOT", str(tmproot))
    monkeypatch.setenv("SDSS_GIT_ROOT", str(tmpgit))
    monkeypatch.setenv("SDSS_SVN_ROOT", str(tmpsvn))
    monkeypatch.setenv("SDSS_GIT_MODULES", str(tmpgitmod))
    monkeypatch.setenv("SDSS_SVN_MODULES", str(tmpsvnmod))
    monkeypatch.setenv("SDSS_INSTALL_DIR", str(sdss_install_dir))


@pytest.fixture(scope='function')
def setup_sdss_install(monkeypatch):

    def git(*args):
        return subprocess.check_call(['git'] + list(args))

    tmpgit = os.environ.get("SDSS_GIT_ROOT")
    install_dir = os.path.join(tmpgit, 'sdss_install')
    os.makedirs(install_dir)
    os.chdir(install_dir)
    git("clone", "https://github.com/sdss/sdss_install", "master")
    sdss_install_dir = os.path.join(install_dir, "master")
    monkeypatch.setenv("SDSS_INSTALL_DIR", str(sdss_install_dir))



@pytest.fixture(scope='function')
def monkey_diffdir(monkeypatch, tmpdir):
    ''' Fixture to monkeypatch different git and svn root directories '''
    tmproot = tmpdir / "software" / "sdss"
    tmpgit = (tmpdir / 'software').mkdir('Work').mkdir('git')
    tmpsvn = (tmpdir / 'software').mkdir('svn')
    tmpgitmod = (tmpdir / "software" / 'Work').mkdir("modulefiles")
    tmpsvnmod = tmpsvn.mkdir("modulefiles")

    monkeypatch.setenv("SDSS_INSTALL_PRODUCT_ROOT", str(tmproot))
    monkeypatch.setenv("SDSS_GIT_ROOT", str(tmpgit))
    monkeypatch.setenv("SDSS_SVN_ROOT", str(tmpsvn))
    monkeypatch.setenv("SDSS_GIT_MODULES", str(tmpgitmod))
    monkeypatch.setenv("SDSS_SVN_MODULES", str(tmpsvnmod))


def core_install(params):
    ''' sets up the core sdss_install object

    Parameters:
        params (list):
            A list of command-line options for sdss_install to use
    Returns:
        a core Install instance
    '''
    sys.argv[1:] = params
    options = Argument('sdss_install').options
    install = Install(options=options)
    return install


@pytest.fixture()
def install(request):
    ''' Fixture to generate a parameterized sdss_install instance '''
    params = request.param
    core = core_install(params)
    yield core
    core = None


@pytest.fixture()
def setup(install):
    ''' Fixture to generate an Install up to setup '''
    install.set_ready()
    install.set_product()
    install.set_directory()
    install.set_directory_install()
    install.set_directory_work()
    yield install
    install = None


@pytest.fixture()
def work(setup):
    ''' Fixture to generate an Install up to work-product checkout '''
    options = setup.options
    if not options.module_only:
        setup.clean_directory_install()
        if options.github:
            setup.set_sdss_github_remote_url()
        else:
            setup.set_svncommand()
            setup.set_exists()
        setup.fetch()
    yield setup
    setup = None


def _run_module(install):
    ''' run the module setup '''
    install.reset_options_from_config()
    install.set_build_type()

    if install.ready:
        install.set_modules()
        install.modules.set_module()
        install.modules.set_ready()
        install.modules.set_file()
        install.modules.load_dependencies()
        install.modules.set_keywords()
        install.modules.set_directory()
    return install


@pytest.fixture()
def module_setup(work):
    ''' Fixture to generate an Install up to modulefile setup but without build '''
    work = _run_module(work)
    yield work
    work = None


@pytest.fixture()
def module(work):
    ''' Fixture to generate an Install up to modulefile generation '''
    work = _run_module(work)
    work.modules.build()
    yield work
    work = None


@pytest.fixture()
def external(module):
    ''' Fixture to generate and Install up to external dependency installation '''
    options = module.options
    # must be after module.fetch()
    if options.external_dependencies:
        module.install_external_dependencies()
    yield module
    module = None


@pytest.fixture()
def build(external):
    ''' Fixture to generate an Install for full install process '''
    options = external.options

    external.set_environ()
    if not options.module_only:
        external.build()
        external.build_documentation()
        external.build_package()
        if not options.keep:
            external.clean()
    yield external
    external.clean_directory_install()
    external = None


@pytest.fixture()
def bootstrap(build):
    ''' Fixture for running bootstrap step for sdss_install '''
    build.checkout()
    yield build
    build = None


@pytest.fixture()
def finalize(build):
    build.finalize()

    yield build
    build = None
