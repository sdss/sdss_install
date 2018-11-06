from sdss_install.application import Query
import requests
import json
from os import environ

class Client():
    
    methods = {
               'post'    : requests.post,
               'put'     : requests.put,
               'delete'  : requests.delete,
               'head'    : requests.head,
               'options' : requests.options,
               'get'     : requests.get
               }
 
    def __init__(self, logger=None, api=None, endpoint=None):
        ''' Set Client logger, identify GraphQL or REST API, and set endpoint URL.'''
        self.logger   = logger
        self.endpoint = endpoint
        self.api = api
    
    def set_method(self, method=None):
        '''Set HTTP request method.'''
        if method in self.methods: self.method = self.methods[method]
        else: self.method = None
        if not self.method:
            s = 'ERROR: Unknown HTTP request method: %s\n' % self.method
            s += 'Known methods:\t' + json.dumps( str( self.methods.keys() ), indent=1 )
            self.logger.error(s)

    def set_authorization(self,authorization = None):
        '''Set GitHub authorization token.'''
        self.authorization = None
        if authorization:
            self.authorization = authorization
        else:
            key = None
            if self.api == 'graphql': key = 'SDSS_GITHUB_KEY'
            elif self.api == 'rest':  key = 'SDSSSANDBOX_KEY'
            else: self.logger.error('ERROR: Authorization key not set. Unknown API given: %s.' % self.api)
            if key:
                try: self.authorization = environ[key]
                except Exception as e:
                    self.authorization = None
                    self.logger.error('ERROR: Unable to authorize the GrqphQL client using the key %s.' % e)
            else: self.logger.error('ERROR: Unable to authorize the GrqphQL client using the key %s.' % key)

    def set_query(self, parameters = None):
        '''Set GraphQL query with passed parameters.'''
        self.query = None
        self.query = Query(parameters = parameters, logger=self.logger)
        if self.query:
            self.query.set_graphql_dir()
            self.query.set_file()
            self.query.set_string()
        else: self.logger.error('ERROR: Unable to instantiate a Query instance.')

    def set_data(self, query_string=None):
        '''Set GraphQL query or REST GET response data.'''
        self.data = None
        payload = {'query': query_string} if query_string else None
        if self.method and self.endpoint and self.authorization:
            r = self.method(url=self.endpoint,
                            json=payload,
                            headers={'Authorization': 'token {}'.format(self.authorization)})
            try:
                content = json.loads(r.content)
                if content:
                    if query_string: self.data = content['data'] if 'data' in content else None
                    else: self.data = content
                else: self.logger.error('ERROR: Unable to set data content.')
            except ValueError as e:
                self.data = None
                self.logger.error('ERROR: Unable to set data content. Exception: %s.' % e)
        else:
            s = 'ERROR: Unable to set client data.\n'
            s += 'method = %r\nendpoint = %r\nauthorization = %r' % (self.method, self.endpoint, self.authorization)
            self.logger.error(s)
