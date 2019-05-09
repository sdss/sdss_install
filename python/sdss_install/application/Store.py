from sdss_install.application import Client
from json import dumps

class Store:
    
    def __init__(self,logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.set_ready()
        self.set_attributes()

    def set_logger(self,logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        self.ready = bool(self.logger)
        if not self.ready:
            print('ERROR: %r> Unable to set_logger.' % self.__class__)

    def set_options(self,options=None):
        '''Set command line argument options'''
        self.options = options if options else None
        if not self.options:
            if self.logger: self.logger.error('Unable to set_options')
            else:           print('ERROR: Unable to set_options')

    def set_ready(self):
        '''Set error indicator.'''
        self.ready = bool(self.logger   and
                          self.options
                          )

    def set_attributes(self):
        '''Set class attributes.'''
        if self.ready:
            self.verbose = self.options.verbose if self.options else None

    def set_organization_name(self):
        '''Set the GitHub organization.'''
        self.organization_name = 'sdss'

    def set_client(self,api='graphql',
                         endpoint='https://api.github.com/graphql',
                         method='post'):
        '''Set an authenticated class Client instance.'''
        self.client = None
        if self.ready:
            self.client = Client(logger=self.logger,
                                 options=self.options,
                                 api=api,
                                 endpoint=endpoint)
            if self.client.ready: self.client.set_method(method=method)
            if self.client.ready: self.client.set_authorization()
            self.ready = self.client.ready

    def set_data(self,query_parameters=None):
        '''Set GraphQL query payload data.'''
        if self.ready:
            self.query_parameters = query_parameters if query_parameters else None
            self.client.set_query(parameters=self.query_parameters)
            self.ready = self.client.ready
            if self.ready:
                query_string = self.client.query.string
#                if self.verbose:
#                    self.logger.debug('query_string:\n' +
#                        dumps(query_string,indent=1))
#                    self.logger.debug('query_string:\n' +
#                        dumps(query_string % self.query_parameters,indent=1))
                self.client.set_data(query_string = query_string %
                    self.query_parameters)
                self.ready = self.client.ready

