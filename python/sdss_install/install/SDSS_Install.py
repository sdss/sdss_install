from sdss_install.application import Logging

class SDSS_Install:
    
    def __init__(self,
                 options=None):
        self.options = options if options else None
        self.set_logging(options=options)

    def set_logging(self, options=None):
        self.logger = None
        if options:
            self.logging = Logging(name=options._name,
                                   section=options.section,
                                   level=options.level,
                                   nolog=options.nolog) if options else None
            self.logger = self.logging.logger if self.logging else None
        if not options or not self.logger: print('ERROR: %r> Unable to set_logging.' % self.__class__)


