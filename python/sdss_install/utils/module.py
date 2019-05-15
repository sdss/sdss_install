# encoding: utf-8
#
# @Author: Joel Brownstein
# @Date: May 13, 2019
# @Filename: module.py
# @License: BSD 3-Clause
# @Copyright SDSS 2019

from __future__ import absolute_import, division, print_function, unicode_literals

import string
from os import environ
from subprocess import Popen, PIPE
from os.path import join, exists
from re import search, compile


class Module:
    '''Class for system module's shell in python.
    Replaces system module's python shell, which
    has poor pipe handling.'''

    def __init__(self,logger=None):
        self.set_logger(logger=logger)
        self.set_modules()
        self.set_version()
        self.set_major_minor_patch()

    def set_logger(self,logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        self.ready = bool(self.logger)
        if not self.ready:
            print('ERROR: %r> Unable to set_logger.' % self.__class__)

    def set_modules(self):
        self.set_modules_home()
        self.set_modules_lang()
        if self.modules_lang['tcl']: self.set_tclsh()
        self.set_ready()

    def set_modules_home(self):
        '''Set modules_home.'''
        self.modules_home = dict()
        if self.ready:
            try:
                modules_home = environ['MODULESHOME']
                self.modules_home = {'dir': modules_home}
            except: self.modules_home = dict()
            if self.modules_home:
                self.modules_home['lua'] = join(modules_home, "init", "lmodrc.lua")
                self.modules_home['tcl'] = join(modules_home, "modulecmd.tcl")
            else:
                self.ready = False
                self.logger.error('Unable to set_modules_home. ' +
                                  'self.modules_home: {}.'.format(self.modules_home))
    def set_modules_lang(self):
        self.modules_lang = {}
        self.modules_lang['lua'] = self.modules_home['lua'] and exists(self.modules_home['lua'])
        self.modules_lang['tcl'] = self.modules_home['tcl'] and exists(self.modules_home['tcl'])

    def set_tclsh(self):
        '''Set tclsh exec directory.'''
        self.tclsh = str()
        if self.ready:
            try: self.tclsh = environ['TCLSH']
            except:
                for self.tclsh in ['/usr/bin/tclsh','/bin/tclsh', None]:
                    if self.tclsh and exists(self.tclsh): break
            if not self.tclsh:
                self.ready = False
                self.logger.error('Unable to set_tclsh. ' +
                                  'self.tclsh: {}.'.format(self.tclsh))

    def set_ready(self):
        '''Set self.ready after setting modules information.'''
        self.ready = (self.logger and 
                      self.modules_home and
                      self.modules_home['dir'] and exists(self.modules_home['dir']) and
                      (self.modules_lang['lua'] or
                      (self.tclsh and exists(self.tclsh) and self.modules_lang['tcl'])))

    def set_command(self, command=None, arguments=None):
        self.command = list()
        if self.ready:
            if command:
                self.command = ['module', command] if self.modules_lang['lua'] else [self.tclsh, self.modules_home['tcl'], 'python', command] if self.modules_lang['tcl'] else None
                if self.command and arguments:
                    self.command.append(string.join(arguments))
            else:
                self.ready = False
                self.logger.error('Unable to set_command. ' +
                                  'command: {}.'.format(command))


    def set_version(self):
        '''Set the Modules Release Tcl version string returned by modules --version.'''
        self.version = str()
        if self.ready:
            self.set_command("--version")
            if self.command:
                proc = Popen(self.command, stdout=PIPE, stderr=PIPE)
                if proc:
                    (stdout, stderr) = proc.communicate() if proc else (None,None)
                    self.returncode = proc.returncode if proc else None
                    self.version = stderr.strip() if self.returncode == 0 and stderr else None
                else:
                    self.ready = False
                    self.logger.error('Unable to set_version. ' +
                                      'proc: {}.'.format(proc))

    def set_major_minor_patch(self):
        '''From the the Modules Release Tcl version string, set version major, minor, and patch.'''
        self.major = str()
        self.minor = str()
        self.patch = str()
        if self.ready:
            version_string = str(self.version) if self.version else str()
            self.type = ('Tcl' if version_string and 'tcl' in version_string.lower()
                         else str())
            text = str()
            p1 = compile('\d*\.\d*\.\d*|\d*\.\d*')
            iterator = p1.finditer(version_string)
            for match in iterator:
                text = version_string[match.start() : match.end()] if match else str()
                if text: break
            split = text.split('.') if text else list()
            self.major = split[0].strip() if split and len(split) >= 1 else str()
            self.minor = split[1].strip() if split and len(split) >= 2 else str()
            self.patch = split[2].strip() if split and len(split) >= 3 else str()



