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

class Module:
    '''Class for system module's shell in python.
    Replaces system module's python shell, which
    has poor pipe handling.'''

    def __init__(self): # , logger=None, options=None
#        self.logger = logger
#        self.options = options
        self.set_modules()
        self.set_version()

    def set_modules(self):
        self.set_modules_home()
        self.set_tclsh()
        self.set_ready()

    def set_modules_home(self):
        try:
            modules_home = environ['MODULESHOME']
            self.modules_home = {'dir': modules_home}
        except: self.modules_home = {}
        if self.modules_home:
            self.modules_home['executable'] = join(modules_home, "modulecmd.tcl")

    def set_tclsh(self):
        try: self.tclsh = environ['TCLSH']
        except:
            for self.tclsh in ['/usr/bin/tclsh','/bin/tclsh', None]:
                if self.tclsh and exists(self.tclsh): break

    def set_ready(self):
        self.ready = (self.modules_home and self.tclsh and exists(self.tclsh)
                        and self.modules_home['dir'] and exists(self.modules_home['dir'])
                        and self.modules_home['executable'] and exists(self.modules_home['executable']))

    def set_command(self, command=None, arguments=None):
        if command and self.ready:
            self.command = [self.tclsh, self.modules_home['executable'], 'python', command]
            if arguments:
                self.command.append(string.join(arguments))
        else: self.command = None

    def old_crappy_method(self):
        self.set_command("-V")
        proc = Popen(self.command)

    def set_version(self):
        if self.ready:
            self.set_command("-V")
            proc = Popen(self.command, stdout=PIPE, stderr=PIPE)
            if proc:
                (stdout, stderr) = proc.communicate() if proc else (None,None)
                self.returncode = proc.returncode if proc else None
                self.version = stderr if self.returncode == 0 else None
            else:
                self.version = None
        else: self.version = None

