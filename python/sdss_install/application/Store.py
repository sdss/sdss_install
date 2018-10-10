from sdss_install.application import Client
from sdss_install.application import Logging
import json

class Store:
    
    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)

    def set_logger(self, logger=None):
        self.logger = logger if logger else None
        if not self.logger: print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    def set_organization_name(self):
        '''Set the GitHub organization.'''
        self.organization_name = 'sdss'

    def set_client(self, api='graphql', endpoint='https://api.github.com/graphql', method='post'):
        '''Set an authenticated GitHub Client.'''
        self.client = None
        self.client = Client(logger=self.logger, api=api, endpoint=endpoint)
        if self.client:
            self.client.set_method(method=method)
            self.client.set_authorization()
        if not self.client:
            self.logger.error('ERROR: Unable to instantiate a Client instance.')

    def set_data(self, query_parameters=None):
        '''Set GraphQL query payload data.'''
        self.query_parameters = query_parameters if query_parameters else None
        if self.query_parameters:
            self.set_query()
        else:
            s = 'ERROR: Unable to set GraphQL payload data.\n'
            s += 'query_parameters = %s.\n' % json.dumps(self.query_parameters, indent=1)
            s += 'NOTE: To avoid system crash, setting self.client.data = None.'
            self.client.data = None
            self.logger.error(s)

    def set_query(self):
        '''Set Query instance and GraphQL query string.'''
        self.client.set_query(parameters=self.query_parameters)
        if self.client.query:
            if self.client.query.string:
                self.set_payload_data()
            else:
                s = 'ERROR: Unable to set GraphQL query string.\n'
                s += 'query string = %r.\n' % self.client.query.string
                s += 'NOTE: Setting self.client.data = None to avoid system crash.'
                self.client.data = None
                self.logger.error(s)
        else:
            s = 'ERROR: Unable to instantiate a Query instance.\n'
            s += 'query = %r\n' % self.client.query
            s += 'NOTE: To avoid system crash, setting self.client.data = None.'
            self.client.data = None
            self.logger.error(s)
    
    def set_payload_data(self):
        '''Set GraphQL query payload data.'''
        query_string = self.client.query.string
        self.client.set_data(query_string % self.query_parameters)
        if not self.client.data:
            s = 'ERROR: Unable to set GraphQL payload data.\n'
            s += 'data = %r.' % self.client.data
            self.logger.error(s)
        else:
            self.logger.debug('DEBUG:\nquery_parameters:\n' + json.dumps(self.query_parameters, indent=2) )
            self.logger.debug('DEBUG:\nquery_string:\n' + str(query_string) )
            self.logger.debug('DEBUG:\nquery_string:\n' + str(query_string % self.query_parameters) )
 
    def pause(self): ### DEBUG ###
        input('Press enter to continue')
