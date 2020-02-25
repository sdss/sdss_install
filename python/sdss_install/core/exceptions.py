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


class SdssInstallError(Exception):
    """A custom core SdssInstall exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(SdssInstallError, self).__init__(message)


class SdssInstallNotImplemented(SdssInstallError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(SdssInstallNotImplemented, self).__init__(message)


class SdssInstallAPIError(SdssInstallError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from SdssInstall API'
        else:
            message = 'Http response error from SdssInstall API. {0}'.format(message)

        super(SdssInstallAPIError, self).__init__(message)


class SdssInstallApiAuthError(SdssInstallAPIError):
    """A custom exception for API authentication errors"""
    pass


class SdssInstallMissingDependency(SdssInstallError):
    """A custom exception for missing dependencies."""
    pass


class SdssInstallWarning(Warning):
    """Base warning for SdssInstall."""


class SdssInstallUserWarning(UserWarning, SdssInstallWarning):
    """The primary warning class."""
    pass


class SdssInstallSkippedTestWarning(SdssInstallUserWarning):
    """A warning for when a test is skipped."""
    pass


class SdssInstallDeprecationWarning(SdssInstallUserWarning):
    """A warning for deprecated features."""
    pass
