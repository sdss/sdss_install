# encoding: utf-8
#
# @Author: Joel Brownstein
# @Date: May 13, 2019
# @Filename: module.py
# @License: BSD 3-Clause
# @Copyright SDSS 2019

from __future__ import absolute_import, division, print_function, unicode_literals

from os import environ
from subprocess import Popen, PIPE
from os.path import join, exists
import re


class Module:
    '''Class for system module's shell in python.
    Replaces system module's python shell, which
    has poor pipe handling.'''

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.set_modules()
        self.set_version()
        self.set_version_major_minor_patch()

    def set_logger(self, logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        self.ready = bool(self.logger)
        if not self.ready:
            print('ERROR: %r> Unable to set_logger.' % self.__class__)

    def set_options(self, options=None):
        '''Set command line argument options'''
        self.options = None
        if self.ready:
            self.options = options if options else None
            if not self.options:
                self.ready = False
                self.logger.error('Unable to set_options' +
                                  'self.options: {}'.format(self.options))

    def set_modules(self):
        self.set_modules_home()
        self.set_modules_lang()
        self.set_tclsh()
        self.set_ready()

    def set_modules_home(self):
        '''Set modules_home.'''
        self.modules_home = dict()
        if self.ready:
            modules_home = None
            if self.options.modules_home:
                modules_home = self.options.modules_home
            else:
                try:
                    modules_home = environ['MODULESHOME']
                except:
                    modules_home = dict()
            if modules_home:
                self.modules_home = {'dir': modules_home}
                self.modules_home['lmod'] = join(modules_home, "libexec", "lmod")
                self.modules_home['lua'] = join(modules_home, "init", "lmodrc.lua")
                self.modules_home['tcl'] = join(modules_home, "modulecmd.tcl")
                if not exists(self.modules_home['tcl']):
                    self.modules_home['tcl'] = join(modules_home, "libexec", "modulecmd.tcl")
            else:
                self.ready = False
                self.logger.error('Unable to set_modules_home. ' +
                                  'modules_home: {}.'.format(modules_home))

    def set_modules_lang(self):
        self.modules_lang = dict()
        self.modules_lang['lmod'] = self.modules_home['lmod'] and exists(self.modules_home['lmod'])
        self.modules_lang['lua'] = ( self.modules_lang['lmod'] and
                                     self.modules_home['lua'] and exists(self.modules_home['lua']) )
        self.modules_lang['tcl'] = self.modules_home['tcl'] and exists(self.modules_home['tcl'])

    def set_tclsh(self):
        '''Set tclsh exec directory.'''
        self.tclsh = None
        if self.ready and self.modules_lang['tcl']:
            try:
                self.tclsh = environ['TCLSH']
            except:
                for self.tclsh in ['/usr/bin/tclsh', '/bin/tclsh', None]:
                    if self.tclsh and exists(self.tclsh):
                        break
            if not self.tclsh:
                self.ready = False
                self.logger.error('Unable to set_tclsh. ' +
                                  'self.tclsh: {}.'.format(self.tclsh))

    def set_ready(self):
        '''Set self.ready after setting modules information.'''
        self.ready = (self.logger and
                      self.options and
                      self.modules_home and
                      self.modules_home['dir'] and exists(self.modules_home['dir']) and
                      (self.modules_lang['lua'] or
                      (self.tclsh and exists(self.tclsh) and self.modules_lang['tcl'])))

    def set_command(self, command=None, arguments=None):
        self.command = list()
        if self.ready:
            if command:
                self.command = ([self.modules_home['lmod'], 'bash', command]
                                if self.modules_lang['lua'] else
                                [self.tclsh, self.modules_home['tcl'], 'python', command]
                                if self.modules_lang['tcl'] else None)
                if self.command and arguments:
                    self.command.append(join(arguments))
            else:
                self.ready = False
                self.logger.error('Unable to set_command. ' +
                                  'command: {}.'.format(command))

    def execute_command(self):
        if self.command:
            proc = Popen(self.command, stdout=PIPE, stderr=PIPE)
            if proc:
                (self.stdout, self.stderr) = proc.communicate() if proc else (None, None)
                self.returncode = proc.returncode if proc else None
            else:
                self.ready = False
                self.logger.error('Unable to execute_command. ' +
                                  'proc: {}.'.format(proc))
        else:
            self.ready = False
            self.logger.error('Unable to execute_command. ' +
                              'self.command: {}.'.format(self.command))

    def set_version(self):
        '''Set the Modules Release Tcl version string returned by modules --version.'''
        self.version = str()
        if self.ready:
            self.set_command("--version")
            self.execute_command()
            self.version = (self.stderr.strip()
                            if self.returncode == 0 and self.stderr else None)

    def set_version_major_minor_patch(self):
        '''From the the Modules Release Tcl version string, set version major, minor, and patch.'''
        self.major = str()
        self.minor = str()
        self.patch = str()
        if self.ready:
            if self.version and self.modules_lang:
                self.type = ('Tcl' if self.modules_lang['tcl'] else
                             'Lua' if self.modules_lang['lua'] else
                             'Lmod' if self.modules_lang['lmod'] else str()
                             )
                version_string = str(self.version) if self.version else str()
                text = str()
                p1 = re.compile('\d+\.\d+\.\d+|\d+\.\d+')
                iterator = p1.finditer(version_string)
                for match in iterator:
                    text = version_string[match.start(): match.end()] if match else str()
                    if text:
                        break
                split = text.split('.') if text else list()
                self.major = split[0].strip() if split and len(split) >= 1 else str()
                self.minor = split[1].strip() if split and len(split) >= 2 else str()
                self.patch = split[2].strip() if split and len(split) >= 3 else str()
            else:
                self.ready = False
                self.logger.error('Unable to set_version. ' +
                                  'self.version: {}.'.format(self.version) +
                                  'self.verson_lang: {}.'.format(self.verson_lang)
                                  )




