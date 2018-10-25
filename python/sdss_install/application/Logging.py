from os import makedirs, environ, listdir
from os.path import join, exists
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from socket import getfqdn
from datetime import datetime

class Logging:
    
    mode = 0o775
    time_format = "%Y-%m-%dT%H:%M:%S %Z"
    
    def __init__(self, name=None, section=None, level='warning', nolog=False):
        self.name = name
        self.section = section
        self.level = level
        self.nolog = nolog
        self.logger = None
        self.filehandler = None
        self.smtphandler = None
        self.set_dir()
        self.set_mailhost()
        self.set_recipients()
        self.set_email()
        self.set_file()
        self.set_ready()
    
    
    def set_mailhost(self):
        try: self.mailhost = environ['WIKI_MAILHOST']
        except: self.mailhost = None
    
    def set_recipients(self):
        try: self.recipients = [recipient.strip() for recipient in environ['WIKI_RECIPIENTS'].split(',')]
        except: self.recipients = None
    
    def set_email(self):
        try: self.email = "%s@%s" % (environ['USER'], getfqdn())
        except: self.email = None
    
    def set_dir(self):
        try: self.dir = join(environ['SDSS_INSTALL_LOGS_DIR'], self.section) if self.section else environ['SDSS_INSTALL_LOGS_DIR']
        except: self.dir = None
        if self.dir and not exists(self.dir): makedirs(self.dir)
    
    def set_file(self):
        format = {'now' : datetime.now().strftime('%Y%m%d'), 'name': self.name} if self.name else None
        self.file = join(self.dir, "%(name)s_%(now)s.log" % format) if self.dir and format else None
    
    def set_ready(self):
        if self.logger is None: self.set_logger()
        elif self.logger.handlers and not self.nolog:
            if self.filehandler in self.logger.handlers: self.logger.removeHandler(self.filehandler)
            if self.smtphandler in self.logger.handlers: self.logger.removeHandler(self.smtphandler)
        if not self.nolog:
            self.set_filehandler()
            self.set_mailhosthandler()
        self.ready = True if self.dir is not None and self.logger is not None else False
    
    def set_logger(self):
        self.logger = logging.getLogger('sdss_install')
        if self.logger:
            if      self.level == 'debug':   self.logger.setLevel(logging.DEBUG)
            elif    self.level == 'info':    self.logger.setLevel(logging.INFO)
            elif    self.level == 'warning': self.logger.setLevel(logging.WARNING)
            else:                            self.logger.setLevel(logging.ERROR)

    def set_filehandler(self):
        if self.logger and self.file:
            needs_rollover = exists(self.file)
            self.filehandler = RotatingFileHandler(self.file, backupCount=9999)
            if needs_rollover: self.filehandler.doRollover()
            format = "[%(asctime)s] %(module)s> %(message)s"
            formatter = logging.Formatter(format, self.time_format)
            self.filehandler.setFormatter(formatter)
            self.logger.addHandler(self.filehandler)
            if self.level=='info': print("LOGGING> %s" % self.file)

    def set_mailhosthandler(self):
        if self.logger and self.mailhost and self.email and self.recipients and self.stage:
            self.smtphandler = SMTPHandler(self.mailhost, self.email, self.recipients, "Critical error reported by %s for MJD=%r." % (self.stage, self.mjd))
            format = "At %(asctime)s, {stage} failed with this message:\n\n%(message)s\n\nSincerely, sdssadmin on behalf of the SDSS data team!".format(stage=self.stage)
            formatter = logging.Formatter(format, self.time_format)
            self.smtphandler.setFormatter(formatter)
            self.smtphandler.setLevel(logging.CRITICAL)
            self.logger.addHandler(self.smtphandler)
