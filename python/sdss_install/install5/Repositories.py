from sdss_install.application import Store
from json import dumps
import datetime
#from datetime import datetime.strptime as strptime


class Repositories:

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.query_file_name = 'repositories'
        self.store = None
        self.repository_list = None


    def set_logger(self, logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        if not self.logger: print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        '''Set command line argument options'''
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    def get_repository_names(self):
        self.set_repositories()
        repository_names = self.repositories if self.repositories else None
        return repository_names

    def set_repositories(self):
        '''
        Set a list of dictionaries with all GitHub repository information
        for the requested product
        '''
        self.repositories = list()
        self.set_store()
        self.set_query_parameters()
        self.set_repository_data()
        self.repositories.extend(self.repository_list)
#        print('self.repositories:\n' + dumps(self.repositories,indent=1))
#        print('self.query_parameters:\n' + dumps(self.query_parameters,indent=1))
#        print('len(self.repositories): %r' % len(self.repositories))
        pagination_flag = True
        while pagination_flag:
            if self.page_info['hasNextPage']:
                self.logger.debug('********** Paginating **********')
                self.set_pagination_parameters()
                self.set_repository_data()
                self.repositories.extend(self.repository_list)
#                print('self.repositories:\n' + dumps(self.repositories,indent=1))
#                print('self.query_parameters:\n' + dumps(self.query_parameters,indent=1))
#                print('len(self.repositories): %r' % len(self.repositories))
            else: pagination_flag = False
        if not self.repositories: self.logger.error('ERROR: Failed to set_repositories')
#        print('self.repositories:\n' + dumps(self.repositories,indent=1))

    def set_store(self):
        if self.options and not self.store:
            self.store = Store(logger=self.logger, options=self.options)
            self.store.set_organization_name()
            self.store.set_client()
        else: self.logger.error('ERROR: Unable to set_store')

    def set_query_parameters(self):
        '''Set GraphQL query parameters.'''
        if self.options and self.store and self.query_file_name:
            self.query_parameters = {
                    'organization_name' :   self.store.organization_name,
                    'repository_name'   :   self.options.product,
                    'version'           :   self.options.version,
                    'query_file_name'   :   self.query_file_name,
                    'pagination_flag'   :   None,
                    'end_cursor'        :   None,
                    'has_next_page'     :   None,
                                    }
        else:
            self.logger.error('ERROR: Unable to set query_parameters. self.store = %r' % self.store)

    def set_repository_data(self):
        '''Set query payload data and extract field edges and pagination information.'''
        self.set_repository_payload()
        self.set_repository_edges_and_page_info()
        self.set_repository_list()
    
    def set_repository_payload(self):
        self.repository_payload = None
        if self.store.client and self.query_parameters:
            self.store.set_data(query_parameters=self.query_parameters)
            self.repository_payload = self.store.client.data if self.store.client.data else None
        else: self.logger.error('ERROR: Unable to set_repository_data')

    def set_repository_edges_and_page_info(self, data=None):
        '''Set a dictionary of page information and a list of dictionaries containing repository fields.'''
        self.repository_edges = None
        self.page_info = None
        data = self.repository_payload if self.repository_payload else None
#        print('data:\n' + dumps(data,indent=1))
        if data:
            data = data['organization']['repositories'] if data else None
            self.repository_edges = data['edges']                   if data else None
            self.page_info = data['pageInfo']                 if data else None
#            print('self.repository_payload: \n' + dumps(self.repository_payload,indent=1))
#            print('self.page_info: \n' + dumps(self.page_info,indent=1))
        else: self.logger.error('ERROR: Unable to set_repository_edges_and_page_info')

    def set_repository_list(self):
        self.repository_list = list()
        if self.repository_edges:
            for repository in self.repository_edges:
                repository_name = repository['node']['name']
                self.repository_list.append(repository_name)
#                print('repository: \n' + dumps(repository,indent=1))
#                print('self.repository_dict: \n' + dumps(self.repository_dict,indent=1))
#                print('self.repository_list: \n' + dumps(self.repository_list,indent=1))
        else: self.logger.error('ERROR: Unable to set_repository_list')

    def set_pagination_parameters(self):
        '''Set pagination parameters for next page.'''
        if self.query_parameters and self.page_info:
            self.query_parameters['pagination_flag']    = True
            self.query_parameters['end_cursor']         = self.page_info['endCursor']
            self.query_parameters['has_next_page']      = self.page_info['hasNextPage']
        else:
            s1 = 'ERROR: pagination parameters could not be set.\n'
            s2 = 'query_parameters = %s\npage_info = %s' % (self.query_parameters, self.page_info)
            self.logger.error(s1+s2)

    def pause(self):
        input('Press enter to continue')
