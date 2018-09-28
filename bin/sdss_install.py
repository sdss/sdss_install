#!/usr/bin/env python3
# encoding: utf-8
#
# @Author: N Benjamin Murphy
# @Date: Sep 22, 2017
# @Filename: sdss_install
# @License: BSD 3-Clause
# @Copyright: N Benjamin Murphy

from sdss_install.application import Argument
from sdss_install.install import Install

options = Argument('sdss_install').options
install = Install(options=options) if options else None
