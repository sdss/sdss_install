# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_module.py
# Project: tests
# Author: Brian Cherinka
# Created: Tuesday, 25th February 2020 9:28:37 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2020 Brian Cherinka
# Last Modified: Friday, 28th February 2020 2:00:03 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

import pytest
import os
from sdss_install.utils.module import Module


@pytest.fixture()
def module(install):
    module = Module(logger=install.logger, options=install.options)
    yield module
    module = None


@pytest.mark.parametrize('install', [('-v', '-t', '--github')], ids=['options'], indirect=True)
def test_module_ready(module):
    assert module.ready is True


@pytest.mark.skipif(os.getenv("TRAVIS") is not None, reason='skipping if on travis')
@pytest.mark.parametrize('install', [('-v', '-t', '--github')], ids=['options'], indirect=True)
def test_module_list(module):
    loaded_modules = module.list_modules()
    assert loaded_modules
