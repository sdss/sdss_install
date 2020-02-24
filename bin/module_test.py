#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: sdss4install 70491 2016-06-15 19:16:07Z joelbrownstein $
#
from sdss_install import __version__
from sdss_install.application import Argument
from sdss_install.install import Install
from sdss_install.install.modules import Modules
from sdss_install.utils.module import Module


options = Argument('sdss_install').options
install = Install(options=options)
logger = install.logger
module = Module(logger=logger,options=options)
ready = bool(options and install and logger and module)

if not ready:
    print('An error occurred. ready: {}' % ready)
else:
    command = 'unload'
    arguments = 'sdss_github'
    module.set_command(command=command,arguments=arguments)
    module.execute_command()

    print('module.stdout: %r'% module.stdout)
    print('module.stderr: %r'% module.stderr)
    print('module.returncode: %r'% module.returncode)
    print('command: %r'% command)
    print('arguments: %r'% arguments)

    command = 'load'
    arguments = 'sdss_github'
    module.set_command(command=command,arguments=arguments)
    module.execute_command()

    print('module.stdout: %r'% module.stdout)
    print('module.stderr: %r'% module.stderr)
    print('module.returncode: %r'% module.returncode)
    print('command: %r'% command)
    print('arguments: %r'% arguments)
