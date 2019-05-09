from os import environ
from os.path import join, exists
import inspect

class Query():
    
    def __init__(self,logger=None,options=None,parameters=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.set_parameters(parameters=parameters)
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

    def set_parameters(self,parameters=None):
        '''Set the parameters class attribute.'''
        if self.ready:
            self.parameters = parameters if parameters else None
            if not self.parameters:
                self.ready = False
                self.logger.error('Unable to set_parameters')

    def set_ready(self):
        '''Set error indicator.'''
        self.ready = bool(self.logger       and
                          self.parameters
                          )

    def set_attributes(self):
        '''Set class attributes.'''
        if self.ready:
            self.verbose = self.options.verbose if self.options else None

    def set_graphql_dir(self):
        '''Set directory where QraphQL query files reside.'''
        self.graphql_dir = None
        if self.ready:
            try: self.graphql_dir = environ['SDSS_INSTALL_GRAPHQL_DIR']
            except Exception as e:
                self.ready = False
                self.logger.error('Unable to set_graphql_dir ' +
                                  'from the environmental variable ' +
                                  'SDSS_GITHUB_GRAPHQL_DIR. ' +
                                  'Exception: {}.'.format(e)
                                  )
    
    def set_file(self):
        '''
            Set file path for the GraphQL query
            with the passed query parameter(s).
        '''
        self.file = None
        if self.ready:
            if self.parameters and self.graphql_dir:
                if self.parameters['pagination_flag']:
                    self.file = join(self.graphql_dir,
                                     '%s_pagination.txt'
                                     % self.parameters['query_file_name'])
                else:
                    self.file = join(self.graphql_dir,
                                     '%s.txt'
                                     % self.parameters['query_file_name'])
                if not self.file:
                    self.ready = False
                    self.logger.error('Unable to set_file.')
            else:
                self.ready = False
                self.logger.error('Unable to set the GraphQL query file.\n' +
                                  'self.parameters: {}, '.format(self.parameters) +
                                  'self.graphql_dir: {}, '.format(self.graphql_dir)
                                  )
                          
    def set_string(self):
        '''Load GraphQL query string from the identified file path.'''
        self.string = None
        if self.ready:
            if self.file and exists(self.file):
                with open(self.file, 'r') as file:
                    self.string = file.read()
            else:
                self.ready = False
                self.logger.error('The file named {0} '.format(self.file) +
                                   'does not exist in the directory {1}.'
                                   .format(self.graphql_dir))
            if not self.string:
                self.ready = False
                self.logger.error('Unable to set the GraphQL query string.')

