# License information goes here
# -*- coding: utf-8 -*-
"""
======================
sdss_install.install4
======================

This package contains code for installing SDSS-IV software products.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from .Install4 import Install4
from .get_svn_devstr import get_svn_devstr
from .most_recent_tag import most_recent_tag
from .version import version

