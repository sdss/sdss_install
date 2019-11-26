# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_sdss_install.py
# Project: tests
# Author: Brian Cherinka
# Created: Tuesday, 19th November 2019 11:02:59 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Tuesday, 26th November 2019 11:54:19 am
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import pytest
import logging
import subprocess
import os
import sys
from sdss_install.install.modules import Modules
from sdss_install.utils.module import Module

#
#  34.7 seconds to run w/ "pytest" using orig_conftest.py 
#
# by class
# TestOptions (0.04s)
# TestGitSetup (1.26s)
# TestSvnSetup (0.06s)
# TestDiffDirs (13.21s)
# TestNoVerDirs (1.46s)
# TestInstall (10.74s)
# TestModules (8.97s)


class TestOptions(object):

    @pytest.mark.parametrize('install', [('-v', '-t', '--github')], ids=['options'], indirect=True)
    def test_correct_options(self, install):
        ''' test that core options can be set '''
        assert install.options.verbose is True
        assert install.options.test is True
        assert install.options.github is True
        assert install.ready is False
        assert install.options.root == os.environ.get('SDSS_INSTALL_PRODUCT_ROOT')
        assert 'pytest' in install.options.root


def _assert_product(install, repo, name, version, tag=False, branch=False):
    ''' assert a set of product stuff '''
    root = os.path.dirname(install.options.product) if repo == 'svn' else None
    assert install.product['root'] == root
    assert install.product['name'] == name
    assert install.product['version'] == version
    is_master = version in ['master', 'trunk']
    assert install.product['is_master'] is is_master
    assert install.product['checkout_or_export'] == 'checkout' if not tag else 'export'
    assert install.product['is_branch'] is branch or is_master
    if repo == 'git':
        assert install.product['is_tag'] is tag


def _assert_dirs(install, repo, name, version, diff=None, noverdir=None):
    ''' assert a set of directory stuff '''
    assert install.product['name'] == name
    assert install.directory['original'] == os.getcwd()
    # handle the product root directory
    envvar = os.environ.get('SDSS_{0}_ROOT'.format(repo.upper()))
    root = os.path.join(envvar, install.product['root']) if install.product['root'] else envvar
    assert install.directory['root'] == root
    # handle whether version is attached or not for install directory
    skipver = noverdir and repo == 'git'
    installdir = os.path.join(root, name, version) if not skipver else os.path.join(root, name) 
    assert install.directory['install'] == installdir
    # handle work directory
    curdir = os.path.join(os.getcwd(), '{0}-{1}'.format(name, version))
    assert install.directory['work'] == curdir
    # assert that root directory not part of product root or not
    if diff:
        assert not install.directory['root'].startswith(install.options.root)
    else:
        assert install.directory['root'].startswith(install.options.root)
    # assert if no version sub-directory or not
    if skipver:
        assert version not in install.directory['install']
    else:
        assert version in install.directory['install']


@pytest.mark.parametrize('install', [('-t', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
class TestGitSetup(object):
    ''' tests the initial setup when installing a git product '''

    def test_ready(self, install):
        install.set_ready()
        assert isinstance(install.ready, logging.Logger)
        assert hasattr(install, 'install5')

    def test_product(self, install):
        install.set_ready()
        install.set_product()
        _assert_product(install, 'git', 'sdssdb', 'master')

    def test_directories(self, setup):
        _assert_dirs(setup, 'git', 'sdssdb', 'master')


@pytest.mark.parametrize('install', [('-t', 'sdss/transfer', 'trunk')], ids=['transfer'], indirect=True)
@pytest.mark.privatesvn
class TestSvnSetup(object):
    ''' tests the initial setup when installing an svn product '''

    def test_ready(self, install):
        install.set_ready()
        assert isinstance(install.ready, logging.Logger)
        assert hasattr(install, 'install4')

    def test_product(self, install):
        install.set_ready()
        install.set_product()
        _assert_product(install, 'svn', 'transfer', 'trunk')

    def test_directories(self, setup):
        _assert_dirs(setup, 'svn', 'transfer', 'trunk')


class TestDiffDirs(object):
    ''' tests when GIT_ROOT and SVN_ROOT are different than SDSS_INSTALL_PRODUCT_ROOT '''
    
    @pytest.mark.parametrize('install', [('-t', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_root(self, monkey_diffdir, setup):
        root = setup.options.root
        assert root not in setup.directory['root']
        _assert_dirs(setup, 'git', 'sdssdb', 'master', diff=True)


    @pytest.mark.parametrize('install', [('-t', 'transfer', 'trunk')], ids=['transfer'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_root(self, monkey_diffdir, setup):
        root = setup.options.root
        assert root not in setup.directory['root']
        _assert_dirs(setup, 'svn', 'transfer', 'trunk', diff=True)

    @pytest.mark.parametrize('install', [('--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_install(self, monkey_diffdir, work):
        work.set_build_type()
        work.build()
        assert os.listdir(work.directory['install'])
        assert os.environ.get("SDSS_GIT_ROOT") in work.directory['install']

    @pytest.mark.parametrize('install', [('sdss/transfer', 'trunk')], ids=['sdssdb'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_install(self, monkey_diffdir, work):
        work.set_build_type()
        work.build()
        assert os.listdir(work.directory['install'])
        assert os.environ.get("SDSS_SVN_ROOT") in work.directory['install']

    @pytest.mark.parametrize('install', [('--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_mod(self, monkey_diffdir, module):
        ''' test that git modules get placed in custom directory '''
        _assert_mod_setup(module, 'git', 'sdssdb', 'master', work=True)
        _assert_mod_build(module, 'git', 'sdssdb', 'master')

    @pytest.mark.parametrize('install', [('sdss/template', 'trunk')], ids=['template'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_mod(self, monkey_diffdir, module):
        ''' test that svn modules get placed in custom directory '''
        # note transfer product has old etc/module.in; use template product instead for etc/template.module
        _assert_mod_setup(module, 'svn', 'template', 'trunk', work=True)
        _assert_mod_build(module, 'svn', 'template', 'trunk')


class TestNoVerDirs(object):
    ''' Tests for not setting a version sub-directory for git installs '''

    @pytest.mark.parametrize('install', [('-t', '--skip-git-verdirs', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_no_version_dir(self, setup):
        assert setup.options.skip_git_verdirs is True
        _assert_dirs(setup, 'git', 'sdssdb', 'master',
                     noverdir=setup.options.skip_git_verdirs)

    @pytest.mark.parametrize('install', [('-t', '--skip-git-verdirs', 'sdss/transfer', 'trunk')], ids=['transfer'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_no_version_dir(self, setup):
        ''' ensure version is still set for svn installs '''
        assert setup.options.skip_git_verdirs is True
        _assert_dirs(setup, 'svn', 'transfer', 'trunk',
                     noverdir=setup.options.skip_git_verdirs)

    @pytest.mark.parametrize('install', [('--skip-git-verdirs', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_nover_install(self, work):
        ''' test for correct checkout of git repo not in version sub-directory'''
        work.set_build_type()
        work.build()
        idirs = os.listdir(work.directory['install'])
        assert os.listdir(work.directory['work'])
        assert idirs
        assert 'master' not in idirs
        assert 'python' in idirs
        assert os.path.isdir(os.path.join(work.directory['install'], 'python/sdssdb'))

    @pytest.mark.parametrize('install', [('--skip-git-verdirs', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_nover_modulefile(self, module):
        _assert_mod_setup(module, 'git', 'sdssdb', 'master', work=True)
        _assert_mod_build(module, 'git', 'sdssdb', 'master')
        _assert_mod_version(module, 'sdssdb', 'master', skipver=True)

    @pytest.mark.parametrize('install', [('--skip-git-verdirs', 'sdss/template', 'trunk')], ids=['template'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_nover_modulefile(self, module):
        _assert_mod_setup(module, 'svn', 'template', 'trunk', work=True)
        _assert_mod_build(module, 'svn', 'template', 'trunk')
        _assert_mod_version(module, 'template', 'trunk')


class TestInstall(object):
    ''' Test various installation steps for Git install '''

    def _assert_work(self, install, repo, name):
        if repo == 'svn':
            assert 'svn' in install.svncommand
        assert install.product['name'] == name
        assert os.listdir(install.directory['work'])

    def _assert_build(self, install):
        assert install.build_type is None
        install.set_build_type()
        assert 'python' in install.build_type

    def _assert_install(self, install):
        install.make_directory_install()
        assert not os.path.exists(install.directory['install'])
        install.build()
        assert os.listdir(install.directory['install'])

    @pytest.mark.parametrize('install', [('--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_install(self, work):
        # assert work dir stuff
        self._assert_work(work, 'git', 'sdssdb')

        # assert the proper build type
        self._assert_build(work)

        # assert the install directory gets populated
        self._assert_install(work)
        
    @pytest.mark.parametrize('install', [('sdss/transfer', 'trunk')], ids=['transfer'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_install(self, work):
        # assert work dir stuff
        self._assert_work(work, 'svn', 'transfer')

        # assert the proper build type
        self._assert_build(work)

        # assert the install directory gets populated
        self._assert_install(work)

    @pytest.mark.parametrize('install', [('--public', 'sdss/sdss4tools', 'trunk')], ids=['sdss4tools'], indirect=True)
    def test_public_svn(self, work):
        # assert work dir stuff
        self._assert_work(work, 'svn', 'sdss4tools')

        # assert the proper build type
        self._assert_build(work)

        # assert the install directory gets populated
        self._assert_install(work)

        assert 'public' in work.product['url']


def _assert_mod_setup(install, repo, name, version, work=False):
    ''' assert some stuff regarding modulefile setup '''
    assert isinstance(install.modules, Modules)
    assert isinstance(install.modules.module, Module)
    assert isinstance(install.modules.ready, Module)
    modname = '{0}/etc/{1}.module'.format(version, name)
    assert modname in install.modules.file
    assert install.modules.keywords['name'] == name
    assert install.modules.keywords['version'] == version
    moddir = os.environ.get('SDSS_{0}_MODULES'.format(repo.upper()))
    assert install.modules.directory['modules'] == name if not work else os.path.join(
        moddir, name)


def _assert_mod_build(install, repo, name, version):
    ''' assert some stuff regarding post built module file '''
    assert install.modules.built is True
    moddir = os.environ.get('SDSS_{0}_MODULES'.format(repo.upper()))
    modfile = os.path.join(moddir, name, version)
    assert install.modules.product['modulefile'] == modfile
    assert os.path.exists(modfile)


class TestModules(object):
    
    @pytest.mark.parametrize('install', [('--module-only', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_setup(self, module_setup):
        _assert_mod_setup(module_setup, 'git', 'sdssdb', 'master')

    @pytest.mark.parametrize('install', [('--module-only', 'sdss/transfer', 'trunk')], ids=['transfer'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_setup(self, module_setup):
        _assert_mod_setup(module_setup, 'svn', 'transfer', 'trunk')

    @pytest.mark.parametrize('install', [('--module-only', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_build_fail_no_work(self, module):
        ''' test that the build fails when the product is not already checked out '''
        _assert_mod_setup(module, 'git', 'sdssdb', 'master')
        assert module.modules.built is False
        assert 'modulefile' not in module.modules.product

    @pytest.mark.parametrize('install', [('--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_build(self, module):
        ''' test that the build works when the product is already checked out '''
        _assert_mod_setup(module, 'git', 'sdssdb', 'master', work=True)
        _assert_mod_build(module, 'git', 'sdssdb', 'master')
        _assert_mod_version(module, 'sdssdb', 'master')
        
    @pytest.mark.parametrize('install', [('sdss/template', 'trunk')], ids=['template'], indirect=True)
    @pytest.mark.privatesvn
    def test_svn_build(self, module):
        ''' test that the build works when the product is already checked out '''
        # note transfer product has old etc/module.in; use template product instead for etc/template.module
        _assert_mod_setup(module, 'svn', 'template', 'trunk', work=True)
        _assert_mod_build(module, 'svn', 'template', 'trunk')
        _assert_mod_version(module, 'template', 'trunk')


def _find_string(data_string, data):
    ''' Find a substring in some data
    
    Parameters:
        data_string (str):
            A sub_string to search for
        data (str):
            The full string data to search in
    '''
    vstart = data.find(data_string)
    vend = data.find('\n', vstart)
    vstring = data[vstart:vend]
    return vstring
    
    
def _assert_mod_version(install, name, version, skipver=None):
    ''' asserts version inside output module file '''

    modfile = install.modules.product['modulefile']
    # open file
    with open(modfile, 'r') as file:
        data = file.read()

    # find strings
    name_string = _find_string('set product', data)
    version_string = _find_string('set version', data)
    product_string = _find_string('set PRODUCT_DIR', data)
    
    assert name in name_string
    assert version in version_string

    if skipver:
        assert '$version' not in product_string
    else:
        assert '$version' in product_string
            

class TestBuild(object):
    
    @pytest.mark.parametrize('install', [('-D', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_build(self, build):
        assert os.listdir(build.directory['install'])


def git(*args):
    ''' run a git command '''
    if sys.version_info.major == 3 and sys.version_info.minor >= 7:
        kwargs = {'capture_output': True}
    else:
        kwargs = {'stdout': subprocess.PIPE}
    return subprocess.run(['git'] + list(args), **kwargs)


def get_tag():
    ''' get the latest git tag '''
    tmp = git('describe', '--tags')
    tag = tmp.stdout.strip().decode('utf-8').split('-')[0]
    return tag


class TestBootstrap(object):
    ''' Test for bootstrap install of sdss_install '''
    tag = get_tag()

    @pytest.mark.parametrize('install', [('--github', '--module-only', '--bootstrap')], ids=['sdss_install'], indirect=True)
    def test_setup(self, setup_sdss_install, setup):
        assert setup.options.product == 'sdss_install'
        assert setup.product['name'] == 'sdss_install'
        assert setup.product['version'] == self.tag
        assert setup.product['is_tag'] is True
        assert setup.directory['install'] == setup.directory['work']
        assert os.path.exists(setup.directory['install'])
        os.chdir(setup.directory['install'])
        status = git('status')
        assert 'On branch master' in str(status.stdout)

    @pytest.mark.parametrize('install', [('--github', '--module-only', '--bootstrap')], ids=['sdss_install'], indirect=True)
    def test_module(self, setup_sdss_install, module):
        assert module.modules.built is True
        assert os.path.isfile(module.modules.product['modulefile'])
        assert os.environ.get("SDSS_GIT_MODULES") in module.modules.product['modulefile']

        # test the modulefile
        _assert_mod_setup(module, 'git', 'sdss_install', self.tag, work=True)
        _assert_mod_build(module, 'git', 'sdss_install', self.tag)
        _assert_mod_version(module, 'sdss_install', self.tag)

    @pytest.mark.parametrize('install', [('--github', '--module-only', '--bootstrap')], ids=['sdss_install'], indirect=True)
    def test_bootstrap(self, setup_sdss_install, bootstrap):
        assert os.listdir(bootstrap.directory['install'])
        os.chdir(bootstrap.directory['install'])
        status = git('status')
        assert 'HEAD detached at {0}'.format(self.tag) in str(status.stdout)

    @pytest.mark.parametrize('setup_sdss_install', [('--skip-git-verdirs',)], ids=['novers'], indirect=True)
    @pytest.mark.parametrize('install', [('--github', '--module-only', '--bootstrap', '--skip-git-verdirs')], ids=['sdss_install'], indirect=True)
    def test_diffdirs_novers(self, monkey_diffdir, setup_sdss_install, bootstrap):
        assert os.listdir(bootstrap.directory['install'])
        os.chdir(bootstrap.directory['install'])
        status = git('status')
        assert 'HEAD detached at {0}'.format(self.tag) in str(status.stdout)
