# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_sdss_install.py
# Project: tests
# Author: Brian Cherinka
# Created: Tuesday, 19th November 2019 11:02:59 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Wednesday, 20th November 2019 6:40:42 pm
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


def _assert_dirs(install, repo, name, version, diff=None):
    ''' assert a set of directory stuff '''
    assert install.product['name'] == name
    assert install.directory['original'] == os.getcwd()
    envvar = os.environ.get('SDSS_{0}_ROOT'.format(repo.upper()))
    root = os.path.join(envvar, install.product['root']) if install.product['root'] else envvar
    assert install.directory['root'] == root
    installdir = os.path.join(root, name, version)
    assert install.directory['install'] == installdir
    curdir = os.path.join(os.getcwd(), '{0}-{1}'.format(name, version))
    assert install.directory['work'] == curdir
    if diff:
        assert not install.directory['root'].startswith(install.options.root)
    else:
        assert install.directory['root'].startswith(install.options.root)


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

    def test_directories(self, setup_install):
        _assert_dirs(setup_install, 'git', 'sdssdb', 'master')


# class TestInstall(object):
    
#     @pytest.mark.parametrize('install', [('-t', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
#     def test_git_install(self, full_install):
#         assert full_install.product['name'] == 'sdssdb'
        

@pytest.mark.parametrize('install', [('-t', 'transfer', 'trunk')], ids=['transfer'], indirect=True)
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

    def test_directories(self, setup_install):
        _assert_dirs(setup_install, 'svn', 'transfer', 'trunk')


class TestDiffDirs(object):
    ''' tests when GIT_ROOT and SVN_ROOT are different than SDSS_INSTALL_PRODUCT_ROOT '''
    
    @pytest.mark.parametrize('install', [('-t', '--github', 'sdssdb', 'master')], ids=['sdssdb'], indirect=True)
    def test_git_root(self, monkey_diffdir, setup_install):
        root = setup_install.options.root
        assert root not in setup_install.directory['root']
        _assert_dirs(setup_install, 'git', 'sdssdb', 'master', diff=True)


    @pytest.mark.parametrize('install', [('-t', 'transfer', 'trunk')], ids=['transfer'], indirect=True)
    def test_svn_root(self, monkey_diffdir, setup_install):
        root = setup_install.options.root
        assert root not in setup_install.directory['root']
        _assert_dirs(setup_install, 'svn', 'transfer', 'trunk', diff=True)
