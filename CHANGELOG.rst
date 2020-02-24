.. _sdss_install-changelog:

==========
Change Log
==========

This document records the main changes to the sdss_install code.

.. _changelog-1.0.7:
1.0.7 (unreleased)
------------------

Added
^^^^^
- New configuration bash sript to aid setup during sdss_install bootstrap
- New environment variables to customize GIT and SVN product and modulefile locations
- Use of custom sdss_install.yml config file for loading of parameters and environment variables
- Added new --skip-git-verdirs option to turn off use of version sub-directories for git repos
- Initial test suite for better failure tracking and robustness
- Updated changelog
- Set up testing on Travis-CI
- Added new --github-url option to optionally set a different public git url

Fixed
^^^^^
- synchronized package version with tag versions

.. _changelog-1.0.6:
1.0.6 (2019-12-09)
------------------

Added
^^^^^
- The new command line option --https enables the user to use sdss_install with either https or ssh.

Fixed
^^^^^
- Fixes Issue :issue:`#46` - no option for git install from https

.. _changelog-1.0.5:
1.0.5 (2019-11-13)
------------------

Added
^^^^^
- New sdss_install_version script to check version of the currently checked out Git branch or tag. 
- Support for installation of external dependencies

.. _changelog-1.0.4:
1.0.4 (2019-07-02)
------------------

Added
^^^^^
- Support for Mac Brew installed modules

Changed
^^^^^^^
- Improved backwards compatibility with brew or legacy installed modules

.. _changelog-1.0.3:
1.0.3 (2019-05-16)
------------------

Added
^^^^^
- Custom Module(s) class for improved system handling of module files

.. _changelog-1.0.2:
1.0.2 (2019-05-13)
------------------

Added
^^^^^
- Implememnted subprocessing of git commands for version validation
- Grab latest tag of sdss_install during install for robustness

Changed
^^^^^^^
- Removed GraphQL implementation of version validation

.. _changelog-1.0.1:
1.0.1 (2019-05-13)
------------------

Added
^^^^^
- Initial release of sdss_install
- GraphQL product/version validation of Github repos