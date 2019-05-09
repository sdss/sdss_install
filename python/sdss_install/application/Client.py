from sdss_install.application import Query
import requests
from json import loads, dumps
from os import environ

class Client():
    
    request_methods = {
               'post'    : requests.post,
               'put'     : requests.put,
               'delete'  : requests.delete,
               'head'    : requests.head,
               'options' : requests.options,
               'get'     : requests.get
               }
 
    def __init__(self,logger=None,options=None,api=None,endpoint=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.set_api(api=api)
        self.set_endpoint(endpoint=endpoint)
        self.set_ready()
        self.set_attributes()

    def set_logger(self,logger=None):
        '''Set class logger.'''
        self.logger = logger if logger else None
        self.ready = bool(self.logger)
        if not self.ready:
            print('ERROR: %r> Unable to set_logger.' % self.__class__)

    def set_options(self,options=None):
        '''Set command line argument options'''
        self.options = None
        if self.ready:
            self.options = options if options else None
            if not self.options:
                self.ready = False
                self.logger.error('Unable to set_options' +
                                  'self.options: {}'.format(self.options))

    def set_api(self,api=None):
        '''Set the api class attribute.'''
        if self.ready:
            self.api = api if api else None
            if not self.api:
                self.ready = False
                self.logger.error('Unable to set_api')

    def set_endpoint(self,endpoint=None):
        '''Set the endpoint class attribute.'''
        if self.ready:
            self.endpoint = endpoint if endpoint else None
            if not self.endpoint:
                self.ready = False
                self.logger.error('Unable to set_endpoint')

    def set_ready(self):
        '''Set error indicator.'''
        self.ready = bool(self.logger   and
                          self.api      and
                          self.endpoint
                          )

    def set_attributes(self):
        '''Set class attributes.'''
        if self.ready:
            self.verbose = self.options.verbose if self.options else None

    def set_method(self,method=None):
        '''Set HTTP request method.'''
        if self.ready:
            if method:
                self.method = (self.request_methods[method]
                               if self.request_methods and method in self.request_methods
                               else None)
                if not self.method:
                    self.logger.error(
                    'Unknown HTTP request method: {}, '.format(self.method) +
                    'Known request_methods: {}'.format(self.request_methods.keys())
                    )
            else:
                self.ready = False
                self.logger.error('Unable to set_method. ' +
                                  'method: {}.'.format(method))

    def set_authorization(self,authorization=None):
        '''Set GitHub authorization token.'''
        self.authorization = None
        if self.ready:
            if authorization:
                self.authorization = authorization
            else:
                env = None
                if   self.api == 'graphql': env = 'SDSS_INSTALL_GITHUB_KEY'
                elif self.api == 'rest':    env = 'SDSSSANDBOX_KEY'
                else:
                    self.ready = False
                    self.logger.error('Unable to set_authorization. ' +
                                      "self.api must be 'graphql' or 'rest'. " +
                                      'self.api: {}.'.format(self.api)
                                      )
                if env:
                    try: self.authorization = environ[env]
                    except Exception as e:
                        self.ready = False
                        self.logger.error('Failed to get authorization token from ' +
                                          'environmental variable env: {}. '.format(e) 
                                          )
                else:
                    self.ready = False
                    self.logger.error('Unable to authorize the GrqphQL client ' +
                                      'using the env {}.'.format(e) )

    def set_query(self,parameters=None):
        '''Set GraphQL query with passed parameters.'''
        self.query = None
        if self.ready:
            self.query = Query(logger=self.logger,
                               options=self.options,parameters=parameters)
            if self.query:
                if self.query.ready: self.query.set_graphql_dir()
                if self.query.ready: self.query.set_file()
                if self.query.ready: self.query.set_string()
                self.ready = self.query.ready
            else:
                self.ready = False
                self.logger.error('Unable to set_query. ' +
                                  'self.query: {}'.format(self.query)
                                  )

    def set_data(self,query_string=None):
        '''Set GraphQL query or REST GET response data.'''
        self.data = None
        payload = {'query': query_string} if query_string else None
        if self.method and self.endpoint and self.authorization:
            r = self.method(url=self.endpoint,
                            json=payload,
                            headers={'Authorization': 'token {}'
                                        .format(self.authorization)})
            try:
                content = loads(r.content)
                if content:
                    if query_string:
                        self.data = (content['data']
                                     if 'data' in content
                                     else None)
                    else: self.data = content
                else: self.logger.error('Unable to set data content.')
            except ValueError as e:
                self.data = None
                self.logger.error('Unable to set data content. ' +
                                    'Exception: %s.' % e)
        else:
            self.logger.error(
                'Unable to set client data.\n' +
                'method = %r\nendpoint = %r\nauthorization = %r'
                % (self.method, self.endpoint, self.authorization))

