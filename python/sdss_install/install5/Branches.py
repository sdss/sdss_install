from sdss_install.application import Store
from json import dumps

class Branches:

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
        self.options = None
        if self.ready:
            self.options = options if options else None
            if not self.options:
                self.ready = False
                self.logger.error('Unable to set_options' +
                                  'self.options: {}'.format(self.options))

    def set_ready(self):
        '''Set error indicator.'''
        self.ready = bool(self.logger   and
                          self.options
                          )

    def set_attributes(self):
        '''Set class attributes.'''
        if self.ready:
            self.verbose = self.options.verbose if self.options else None
            self.query_file_name = 'branches'
            self.store = None
            self.branch_list = list()

    def get_branch_names(self):
        '''Get a list of branch names associated with the product.'''
        branch_names = None
        if self.ready:
            self.set_branches()
            branch_names = self.branches if self.branches else None
        return branch_names

    def set_branches(self):
        '''Concatenate branch names from all GraphQL pages.'''
        self.branches = list()
        if self.ready:
            if self.ready: self.set_store()
            if self.ready: self.set_query_parameters()
            if self.ready: self.set_branch_data()
            if self.ready: self.branches.extend(self.branch_list)
            if self.ready:
                pagination_flag = True
                while pagination_flag:
                    if self.page_info['hasNextPage']:
                        self.logger.debug('********** Paginating **********')
                        self.set_pagination_parameters()
                        self.set_branch_data()
                        self.branches.extend(self.branch_list)
                    else: pagination_flag = False
                    if not self.ready: break
        if not self.branches:
            self.logger.debug('Unable to set_branches. No branches found. ' +
                              'self.branches: {}'.format(self.branches))

    def set_store(self):
        '''
            Set a class Store instance and its attributes:
            organization name and a class Client instance.
        '''
        if self.ready:
            self.store = Store(logger=self.logger, options=self.options)
            if self.store.ready: self.store.set_organization_name()
            if self.store.ready: self.store.set_client()
            self.ready = self.store.ready

    def set_query_parameters(self):
        '''Set GraphQL query parameters.'''
        if self.ready:
            if self.store and self.options and self.query_file_name:
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
                self.ready = False
                self.logger.error('Unable to set_query_parameters. ' +
                                    'self.options: {}'.format(self.options) +
                                    'self.store: {}'.format(self.store) +
                                    'self.query_file_name: {}'
                                        .format(self.query_file_name)
                                    )

    def set_branch_data(self):
        '''
            Set GraphQL query payload data then extract field edges and
            pagination information.
        '''
        if self.ready: self.set_branch_payload()
        if self.ready: self.set_branch_edges_and_page_info()
        if self.ready: self.set_branch_list()
    
    def set_branch_payload(self):
        '''Set GraphQL branch query payload data.'''
        if self.ready:
            self.set_payload()
            if self.payload:
                self.branch_payload = self.payload
            else:
                self.ready = False
                self.logger.error('Unable to set_branch_payload.')

    def set_payload(self):
        '''Set GraphQL query payload data.'''
        self.payload = None
        if self.ready:
            if self.store and self.query_parameters:
                self.store.set_data(query_parameters=self.query_parameters)
                if self.store.ready:
                    self.payload = self.store.client.data
                self.ready = self.store.ready
            else:
                self.ready = False
                self.logger.error('Unable to set_payload. ' +
                                  'self.store: {}, '.format(self.store) +
                                  'self.query_parameters: {}. '.format(self.query_parameters)
                                  )

    def set_branch_edges_and_page_info(self,data=None):
        '''
            From the GraphQL query payload data, set a pagination information
            dictionary and a list of dictionaries containing branch fields.
        '''
        self.branch_edges = None
        self.page_info = None
        if self.ready:
            data = self.branch_payload if self.branch_payload else None
            if data:
                data = data['organization']['repository']['refs'] if data else None
                self.branch_edges = data['edges']                 if data else None
                self.page_info = data['pageInfo']                 if data else None
            else:
                self.ready = False
                self.logger.error('Unable to set_branch_edges_and_page_info.' +
                                  'data: {}'.format(data))

    def set_branch_list(self):
        '''
            Set a list of branch names from the branch
            field list of dictionaries.
        '''
        self.branch_list = list()
        if self.ready:
            if self.branch_edges:
                for branch in self.branch_edges:
                    branch_name = branch['node']['name'] if branch else None
                    if branch_name: self.branch_list.append(branch_name)
            else:
                self.logger.debug('Unable to set_branch_list. No branch_edges found. ' +
                                  'self.branch_edges: {}'.format(self.branch_edges))

    def set_pagination_parameters(self):
        '''
            Set pagination parameters for next page
            from pagination infomation dictionary.
        '''
        if self.ready:
            if self.query_parameters and self.page_info:
                self.query_parameters['pagination_flag'] = True
                self.query_parameters['end_cursor'] = self.page_info['endCursor']
                self.query_parameters['has_next_page'] = self.page_info['hasNextPage']
            else:
                self.ready = False
                self.logger.error('Unable to set_pagination_parameters.' +
                                  'self.query_parameters: {}'.format(self.query_parameters) +
                                  'self.page_info: {}'.format(self.page_info)
                                  )

