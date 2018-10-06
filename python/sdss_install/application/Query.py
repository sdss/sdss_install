from os import environ
from os.path import join, exists
import inspect
import json

class Query():
    
    def __init__(self, parameters = None, logger = None):
        self.parameters = parameters
        self.logger = logger

    def set_graphql_dir(self):
        '''Set directory where QraphQL query files reside.'''
        self.graphql_dir = None
        try: self.graphql_dir = environ['SDSS_INSTALL_GRAPHQL_DIR']
        except Exception as e:
            self.logger.error('ERROR: Unable to set the directory from the environmental variable %r.' % e)
    
    def set_file(self):
        '''Set file path for the GraphQL query with the passed query parameter(s).'''
        self.file = None
        if self.parameters:
            if self.graphql_dir:
                if self.parameters['pagination_flag']:
                    self.file = join(self.graphql_dir, '%s_pagination.txt' % self.parameters['query_file_name'])
                else:
                    self.file = join(self.graphql_dir, '%s.txt' % self.parameters['query_file_name'])
            if not self.file:
                s = 'ERROR: Unable to set the GraphQL query file.\n'
                s += 'graphql_dir = %r\n' % self.graphql_dir
                s += 'parameters = %s' % json.dumps(self.parameters, indent=1)
                self.logger.error(s)
        else: self.logger.error('ERROR: Unable to set the GraphQL query file.\nparameters = %s'
                                % json.dumps(self.parameters))
                          
    def set_string(self):
        '''Load GraphQL query string from the identified file path.'''
        self.string = None
        if self.file and exists(self.file):
            with open(self.file, 'r') as file:
                self.string = file.read()
        else: self.logger.error('ERROR: The file named %r does not exist in the directory %r.' %
                                (self.file,self.graphql_dir))
        if not self.string: self.logger.error('ERROR: Unable to set the GraphQL query string.')

    def pause(self):
        input('Press enter to continue')
