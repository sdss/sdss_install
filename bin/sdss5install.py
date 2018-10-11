#!/usr/bin/env python3
# encoding: utf-8
#
# @Author: N Benjamin Murphy
# @Date: Sep 22, 2017
# @Filename: sdss_install
# @License: BSD 3-Clause
# @Copyright: N Benjamin Murphy

from sdss_install import __version__
from sdss_install.application import Argument
from sdss_install.install import Install
from sdss_install.install5 import Install5

options = Argument('sdssinstall').options
install = Install(options=options)
install5 = Install5(logger=install.logger, options=options)
if options and options.version: print(__version__)
else:
    install5.set_ready()
    install5.set_product()
    install5.set_directory()
    install5.set_directory_install()
    install5.set_directory_work()

    if not options.module_only:
        install5.clean_directory_install()
        install5.set_github_remote_url()
        install5.fetch()
        install5.checkout()




