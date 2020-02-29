
Changelog
=========

This document records the main changes to the ``sdss_install`` code.

* :release:`1.1.0 <unreleased>`
* :support:`7` Added sphinx documentation for readthedocs
* :feature:`48` new ``--github-url`` option to optionally set a different public git url
* :support:`48` Updated changelog
* :feature:`12` Added new configuration bash sript to aid setup during sdss_install bootstrap
* :feature:`12` Added new environment variables to customize GIT and SVN product and modulefile locations
* :feature:`48` Use of custom `sdss_install.yml` config file for loading of parameters and environment variables
* :feature:`45` New ``--skip-git-verdirs`` option to turn off use of version sub-directories for git repos
* :support:`48` Initial test suite for better failure tracking and robustness
* :support:`48` Set up testing on Travis-CI
* :bug:`48 major` synchronized package version with tag versions

* :release:`1.0.6 <2019-12-09>`
* :feature:`47` Added new command line option ``--https`` enables the user to use sdss_install with either https or ssh.
* :bug:`46` - no option for git install from https

* :release:`1.0.5 <2019-11-13>`
* :feature:`39 backported`  Added support for installation of external dependencies

* :release:`1.0.4 <2019-07-02>`
* :feature:`42 backported` Added new ``sdss_install_version`` script to check version of the currently checked out Git branch or tag.
* :feature:`25 backported` Added support for Mac Brew installed modules

* :release:`1.0.3 <2019-05-16>`
* :feature:`- backported` Added custom `Module(s)` class for improved system handling of module files

* :release:`1.0.2 <2019-05-13>`
* :feature:`- backported` Implemented subprocessing of git commands for version validation
* :feature:`29 backported` Grab latest tag of sdss_install during install for robustness
* :bug:`21` Removed GraphQL implementation of version validation

* :release:`1.0.1 <2019-05-13>`
* :feature:`-` Initial release of `sdss_install`
* :feature:`-` GraphQL product/version validation of Github repos
