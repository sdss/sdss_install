# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32

from __future__ import print_function, division, absolute_import


class Sdss_installError(Exception):
    """A custom core Sdss_install exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(Sdss_installError, self).__init__(message)


class Sdss_installNotImplemented(Sdss_installError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(Sdss_installNotImplemented, self).__init__(message)


class Sdss_installAPIError(Sdss_installError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from Sdss_install API'
        else:
            message = 'Http response error from Sdss_install API. {0}'.format(message)

        super(Sdss_installAPIError, self).__init__(message)


class Sdss_installApiAuthError(Sdss_installAPIError):
    """A custom exception for API authentication errors"""
    pass


class Sdss_installMissingDependency(Sdss_installError):
    """A custom exception for missing dependencies."""
    pass


class Sdss_installWarning(Warning):
    """Base warning for Sdss_install."""


class Sdss_installUserWarning(UserWarning, Sdss_installWarning):
    """The primary warning class."""
    pass


class Sdss_installSkippedTestWarning(Sdss_installUserWarning):
    """A warning for when a test is skipped."""
    pass


class Sdss_installDeprecationWarning(Sdss_installUserWarning):
    """A warning for deprecated features."""
    pass
