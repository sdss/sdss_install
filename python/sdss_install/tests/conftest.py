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
from sdss_install.application import Argument
from sdss_install.install import Install


@pytest.fixture(scope='function', autouse=True)
def monkey_setup(monkeypatch, tmpdir):
    ''' Fixture that automatically sets up a temporary install directory '''
    tmproot = tmpdir.mkdir("software").mkdir("sdss")
    tmpgit = tmproot.mkdir("github")
    tmpsvn = tmproot.mkdir("svn")
    tmpgitmod = tmpgit.mkdir("modulefiles")
    tmpsvnmod = tmpsvn.mkdir("modulefiles")

    sdss_install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))

    monkeypatch.setenv("SDSS_INSTALL_PRODUCT_ROOT", str(tmproot))
    monkeypatch.setenv("SDSS_GIT_ROOT", str(tmpgit))
    monkeypatch.setenv("SDSS_SVN_ROOT", str(tmpsvn))
    monkeypatch.setenv("SDSS_GIT_MODULES", str(tmpgitmod))
    monkeypatch.setenv("SDSS_SVN_MODULES", str(tmpsvnmod))
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
def setup_install(install):
    ''' Fixture to generate an Install up to setup '''
    install.set_ready()
    install.set_product()
    install.set_directory()
    install.set_directory_install()
    install.set_directory_work()
    yield install
    install = None


@pytest.fixture()
def get_install(setup_install):
    ''' Fixture to generate an Install up to product checkout '''
    options = setup_install.options
    if not options.module_only:
        setup_install.clean_directory_install()
        if options.github:
            setup_install.set_sdss_github_remote_url()
        else:
            setup_install.set_svncommand()
            setup_install.set_exists()
        setup_install.fetch()
    yield setup_install
    setup_install = None


@pytest.fixture()
def mod_install(get_install):
    ''' Fixture to generate an Install up to modulefile generation '''
    get_install.reset_options_from_config()
    get_install.set_build_type()

    if get_install.ready:
        get_install.set_modules()
        get_install.modules.set_module()
        get_install.modules.set_ready()
        get_install.modules.set_file()
        get_install.modules.load_dependencies()
        get_install.modules.set_keywords()
        get_install.modules.set_directory()
        get_install.modules.build()

    yield get_install
    get_install = None

@pytest.fixture()
def full_install(mod_install):
    ''' Fixture to generate an Install for full install process '''
    options = mod_install.options

    # must be after mod_install.fetch()
    if options.external_dependencies:
        mod_install.install_external_dependencies()

    mod_install.set_environ()
    if not options.module_only:
        mod_install.build()
        mod_install.build_documentation()
        mod_install.build_package()
        if not options.keep:
            mod_install.clean()

    if options.bootstrap:
        mod_install.checkout()

    mod_install.finalize()

    yield mod_install
    mod_install = None
