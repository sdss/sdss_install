# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_sdss_install.py
# Project: tests
# Author: Brian Cherinka
# Created: Tuesday, 19th November 2019 11:02:59 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Thursday, 21st November 2019 4:44:11 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import pytest
import logging
import os


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
    root = 'repo' if repo == 'svn' else None
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
    def test_svn_install(self, monkey_diffdir, work):
        work.set_build_type()
        work.build()
        assert os.listdir(work.directory['install'])
        assert os.environ.get("SDSS_SVN_ROOT") in work.directory['install']
        

class TestNoVerDirs(object):
    ''' Tests for not setting a version sub-directory for git installs '''

    @pytest.mark.parametrize('install', [('-t', '--skip-git-verdirs', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_no_version_dir(self, setup):
        assert setup.options.skip_git_verdirs is True
        _assert_dirs(setup, 'git', 'sdssdb', 'master',
                     noverdir=setup.options.skip_git_verdirs)

    @pytest.mark.parametrize('install', [('-t', '--skip-git-verdirs', 'sdss/transfer', 'trunk')], ids=['transfer'], indirect=True)
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
    def test_svn_install(self, work):
        # assert work dir stuff
        self._assert_work(work, 'svn', 'transfer')

        # assert the proper build type
        self._assert_build(work)

        # assert the install directory gets populated
        self._assert_install(work)


class TestModules(object):
     
     @pytest.mark.parametrize('install', [('--module-only', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
     def test_git_module_only(self, module_nowork):
         pass
