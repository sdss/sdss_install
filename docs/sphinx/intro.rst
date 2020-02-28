
.. _intro:

Introduction to sdss_install
===============================

`sdss_install` is a product for installing SDSS software and data repositories versioned by svn, or git as hosted on Github.

Prerequisites
-------------

`sdss_install` requires a modules environment manager to work, either `TCLSH modules <https://modules.readthedocs.io/en/latest/>`_ 
or `LUA modules (LMOD) <https://lmod.readthedocs.io/en/latest/>`_.  Download and install either `TCLSH <http://modules.sourceforge.net/>`_ 
or `LMOD <https://sourceforge.net/projects/lmod/>`_ before proceeding further.     

Installing sdss_install
-----------------------

Installation of `sdss_install` involves checking out a temporary copy of `sdss_install` and running a configuration setup script. 

Checkout Product
^^^^^^^^^^^^^^^^

First checkout the git repo from the `SDSS Github organization <https://github.com/sdss/>`_ into any temporary directory.
::

    git clone https://github.com/sdss/sdss_install.git sdss_install

Navigate to the ``bin`` directory and run the `sdss_install_bootstrap` bash script.
::

    cd sdss_install/bin
    ./sdss_install_bootstrap

This will prompt you for environment configuration (see below) and proceed to install the latest tagged version of `sdss_install` into your
specified software folder.

Environment Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

During the initial installation of `sdss_install`, a series of prompts will ask you to set up some environment variables which tells
`sdss_install` where to install new products and module files.  If you are a new user, or unfamiliar to modules, it is recommended 
to accept all defaults (hit 'enter' on each prompt).     

**Configuration Prompts**:

1. **Set $SDSS_INSTALL_PRODUCT_ROOT environment variable.  [Default: $HOME/software/sdss]**

This asks you to set the base directory path for all SDSS software.  The default is in a new `software/sdss` folder in your home directory. 

2. **Set $SDSS_GIT_ROOT environment variable.  [Default: $SDSS_INSTALL_PRODUCT_ROOT/github]**

This asks you to set the path for all `git` installed products.  The default is within the `$SDSS_INSTALL_PRODUCT_ROOT` directory. 
The `$SDSS_GIT_ROOT` path supercedes the `$SDSS_INSTALL_PRODUCT_ROOT` path. 

3. **Set $SDSS_SVN_ROOT environment variable.  [Default: $SDSS_INSTALL_PRODUCT_ROOT/svn]**

This asks you to set the path for all `svn` installed products.  The default is within the `$SDSS_INSTALL_PRODUCT_ROOT` directory.
The `$SDSS_SVN_ROOT` path supercedes the `$SDSS_INSTALL_PRODUCT_ROOT` path. 

4. **Set $SDSS_GIT_MODULES environment variable.  [Default: $SDSS_GIT_ROOT/modulefiles]**

This asks you to set the path for all module files of `git` installed products.  The default is a directory within your
`$SDSS_GIT_ROOT`.

5. **Set $SDSS_SVN_MODULES environment variable.  [Default: $SDSS_SVN_ROOT/modulefiles]**

This asks you to set the path for all module files of `svn` installed products.  The default is a directory within your
`$SDSS_SVN_ROOT`.

6. **Set temporary $SDSS_INSTALL_DIR environment variable.  [Default: the current path to the temporary checkout]**

This asks you to set the path to where `sdss_install` is installed, which should be the temporary `sdss_install` checkout directory
as the default.  It is **recommended** to leave this as the default and hit enter.      

7. **Add modulefile paths to $MODULEPATH? (Y/N) [Default: Y]**

This step attempts to add your specified git/svn module paths into the existing terminal shell with `module use xxxx`.  To permanently add the 
module paths into your system, you will need to add each `module use xxxx` command into your `bashrc` or `tcshrc` file.  Once added, 
`modules` will search these paths for any available loadable modules.    

8. **Add environment variables to custom sdss_install yaml file? (Y/N) [Default: Y]**

This steps adds the newly defined environment variables into a custom configuration YAML file located at `$HOME/.sdss_install/sdss_install.yml`.
`sdss_install` will load these path definitions.  This allows you to modify path locations after the installation of `sdss_install`, e.g. if
you are restructuring your filesystem but don't want to reinstall `sdss_install`.  A standard example config file will look like::

    envs:
      SDSS_GIT_MODULES: /Users/bcherinka/software/sdss/github/modulefiles
      SDSS_GIT_ROOT: /Users/bcherinka/software/sdss/github
      SDSS_INSTALL_PRODUCT_ROOT: /Users/bcherinka/software/sdss
      SDSS_SVN_MODULES: /Users/bcherinka/software/sdss/svn/modulefiles
      SDSS_SVN_ROOT: /Users/bcherinka/software/sdss/svn

To check for a successful installation, look for the following:

- The last ``stdout`` log line should be `sdss_install - INFO - Install.py - line 1005 - Ready to load module sdss_install/x.x.x`
- Check inside the `$SDSS_GIT_ROOT` folder for a new `sdss_install` product using the latest tag, e.g. ``1.0.7``.
- Check inside the `$SDSS_GIT_MODULES` folder for a new `sdss_install` module file, named as the latest tag, e.g. ``1.0.7``.
- Run `module use $SDSS_GIT_ROOT` and check that you can load the module: `module load sdss_install`  

Once the installation of `sdss_install` is complete, and if successful, you can now safely delete your temporary checkout. 

Advanced Config
^^^^^^^^^^^^^^^

For advanced users, or users with existing git/svn product and module setups, you can specify separate custom 
paths to match your existing setup.  Here is an example of a default `svn` setup but custom directories for `git` repos and 
module files:: 

    envs:
      SDSS_INSTALL_PRODUCT_ROOT: /Users/bcherinka/software/sdss
      SDSS_GIT_ROOT: /Users/bcherinka/Work/git/sdss
      SDSS_SVN_ROOT: /Users/bcherinka/software/sdss/svn
      SDSS_GIT_MODULES: /Users/bcherinka/Work/git/modulefiles
      SDSS_SVN_MODULES: /Users/bcherinka/software/sdss/svn/modulefiles

`sdss_install` will now use this setup to install new SDSS products. 

Product Installation with sdss_install
--------------------------------------

Once installed and the module is loaded, `sdss_install` provides a command-line tool with which to install all other SDSS products.  
See the :ref:`sdss_install tool<usage>` for all available command-line options.  The general syntax for use is
::

    sdss_install [product_name] [product_version]

where **[product_name]** is any SDSS versioned product, and **[product_version]** is any version/branch/tag name, 
e.g. `master`, `trunk`, `1.0.6`.  To see help for the tool, type `sdss_install -h`. 

To install the `master` branch of the `sdss_access` package from its SDSS git repository from Github
::

    # install master branch of sdss_access
    sdss_install --github sdss_access master

The default action is to install `git` products inside version-named sub-directories.  The above command installs 
the `sdss_access` product inside `$SDSS_GIT_ROOT/sdss_access/master`.  This allows one to checkout multiple versions of the same product
at a time.  To instead skip the use of version-named sub-directories, use the `skip-git-verdirs` option.  
::

    # install tag 0.3.0 of the sdssdb product 
    sdss_install --github --skip-git-verdirs sdssdb 0.3.0

The above command installs `sdssdb` at `$SDSS_GIT_ROOT/sdssdb` and checks out the tag `0.3.0` within it. 

When the `github` option is not specified, `sdss_install` installs from the SVN repository instead. To install 
the `trunk` of the `idlutils` package from SVN
::

    # install main trunk of idlutils
    sdss_install sdss/idlutils trunk

Note the **product_name** here is ``sdss/idlutils``.  SVN requires the full SVN path specification to the product from the top level
`repo` or `data` directories.  The `idlutils` product lives inside the top-level ``sdss`` 
sub-directory at `https://svn.sdss.org/repo/sdss/idlutils`.  To install the MaNGA Data Reduction Pipeline, ``mangadrp``, 
which lives at, `https://svn.sdss.org/repo/manga/mangadrp`, one would specifiy
::

    # install main trunk of the MaNGA DRP
    sdss_install manga/mangadrp trunk 

You can also install `svn` products from the public SVN site, using the ``public`` keyword.  
::

    # install tag v1_1_0 for firefly product from public SVN
    sdss_install --public sdss/firefly v1_1_0

which installs the product from `https://svn.sdss.org/public/repo/sdss/firefly/tags/v1_1_0`. 
