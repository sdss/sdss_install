
.. _testing:

Test Installations
==================

We aim to make ``sdss_install`` as robust as possible.  ``sdss_install`` has been designed to work on Linux
and Mac OSx, with Lua and Tcsh modules environments and bash terminal shells.  However ``sdss_install`` may behave
differently under specific combinations of operating systems, Python versions, Modules versions, etc.  If you encounter
any problems with the installation of ``sdss_install`` itself, or its use to install SDSS software products, please file
a new `Github Issue <https://github.com/sdss/sdss_install/issues/new>`_.  Currently, ``sdss_install`` has been
tested to work on the following systems:

==================   ==================  =============================  ======================
Operating System     Module Environment  Python(s)                      Shell
==================   ==================  =============================  ======================
Mac OS X 10.14.6     Tcsh Module 4.2.4   Anaconda 2.7.15, 3.6.7, 3.7.3  bash 3.2.57(1)-release
Mac OS X 10.13.6     Lua Modules 7.8     Anaconda 3.7.2                 bash 3.2.57(1)-release
GNU/Linux 3.10.0     Lua Modules 8.2.7   3.6.9                          bash 4.2.46(2)-release
==================   ==================  =============================  ======================

We also use Travis-CI to run our test suite, which includes tests for installation of ``sdss_install``, as well
as a few SDSS software products versioned in both `git` and `svn`.  The latest run of Travis can be found at
`<https://travis-ci.org/github/sdss/sdss_install>`_.  Travis can automate product testing on a variety of
`operating systems <https://docs.travis-ci.com/user/reference/overview/>`_,
`environment setups <https://docs.travis-ci.com/user/environment-variables/>`_, and
`Python environments <https://docs.travis-ci.com/user/languages/python/>`_.  More information on Travis's build
environments can be found `here <https://docs.travis-ci.com/user/build-environment-updates>`_.  While Travis
constantly updates its environment images, ``sdss_install`` is currently being tested on the following setups:

===================   ==================  =======================  ======================  ================
Operating System      Module Environment  Python(s)                Shell                   Module Installer
===================   ==================  =======================  ======================  ================
Ubuntu Xenial Linux   Lua Modules 5.8     2.7, 3.5, 3.6, 3.7, 3.8  bash 4.3.48(1)-release  apt-get 1.2.31
Mac OS X 10.14.6      Lua Modules 8.3.10  3.7.7                    bash 3.2.57(1)-release  homebrew 2.2.16
Mac OS X 10.13.6      Lua Modules 8.3.10  3.6.5                    bash 3.2.57(1)-release  homebrew 2.2.16
===================   ==================  =======================  ======================  ================

