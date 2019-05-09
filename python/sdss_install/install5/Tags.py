from sdss_install.application import Store
from json import dumps
import datetime
#from datetime import datetime.strptime as strptime


class Tags:

    def __init__(self, logger=None, options=None):
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
            self.query_file_name = 'tags'
            self.store = None
            self.tag_list = None
            self.tags = None

    def most_recent_tag_name(self):
        '''Get the most recent GitHub tag name associated with the product'''
        tag_name = None
        if self.ready:
            if not self.tags: self.set_tags()
            if self.ready:
                self.set_most_recent_tag_name()
                tag_name = (self.most_recent_tag_name
                            if self.most_recent_tag_name
                            else None)
        return tag_name

    def get_tag_names(self):
        '''Get a list of tag names associated with the product.'''
        tag_names = None
        if self.ready:
            if not self.tags: self.set_tags()
            if self.ready:
                tag_names = ([tag['tag_name'] for tag in self.tags
                             if tag and 'tag_name' in tag]
                             if self.tags else None)
        return tag_names

    def set_tags(self):
        '''
            Concatenate a list of dictionaries from all GraphQL pages
            containing tag information.
        '''
        self.tags = list()
        if self.ready:
            if self.ready: self.set_store()
            if self.ready: self.set_query_parameters()
            if self.ready: self.set_tag_data()
            if self.ready: self.tags.extend(self.tag_list)
            if self.ready:
                pagination_flag = True
                while pagination_flag:
                    if self.page_info['hasNextPage']:
                        self.logger.debug('********** Paginating **********')
                        self.set_pagination_parameters()
                        self.set_tag_data()
                        self.tags.extend(self.tag_list)
                    else: pagination_flag = False
                    if not self.ready: break
        if not self.tags:
            self.logger.debug('Unable to set_tags. No tags found. ' +
                              'self.tags: {}'.format(self.tags))

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

    def set_tag_data(self):
        '''
            Set GraphQL query payload data then extract field edges
            and pagination information.
        '''
        if self.ready: self.set_tag_payload()
        if self.ready: self.set_tag_edges_and_page_info()
        if self.ready: self.set_tag_list()
    
    def set_tag_payload(self):
        '''Set GraphQL tag query payload data.'''
        if self.ready:
            self.set_payload()
            if self.payload:
                self.tag_payload = self.payload
            else:
                self.ready = False
                self.logger.error('Unable to set_tag_payload.')

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

    def set_tag_edges_and_page_info(self, data=None):
        '''
            From the GraphQL query payload data, set a pagination information
            dictionary and a list of dictionaries containing tag fields.
        '''
        self.tag_edges = None
        self.page_info = None
        if self.ready:
            data = self.tag_payload if self.tag_payload else None
            if data:
                data = data['organization']['repository']['tags'] if data else None
                self.tag_edges = data['edges']                    if data else None
                self.page_info = data['pageInfo']                 if data else None
            else:
                self.ready = False
                self.logger.error('Unable to set_tag_edges_and_page_info.' +
                                  'data: {}'.format(data))

    def set_tag_list(self):
        '''
            Set a list of dictionaries from the tag field list of dictionaries.
        '''
        self.tag_list = list()
        if self.ready:
            if self.tag_edges:
                for tag_edge in self.tag_edges:
                    if self.ready:
                        tag = tag_edge['tag'] if tag_edge else dict()
                        if tag:
                            self.initialize_tag_dict()
                            self.tag_dict['tag_name'] = (tag['name']
                                                         if tag and 'name' in tag else None)
                            if   tag['target']['__typename'] == 'Commit': key = 'author'
                            elif tag['target']['__typename'] == 'Tag':    key = 'tagger'
                            else:
                                self.ready = False
                                self.logger.error('Unexpected __typename')
                            self.tag_dict['tag_date']    = tag['target'][key]['date']
                            self.tag_dict['tagger_name'] = tag['target'][key]['name']
                            self.tag_list.append(self.tag_dict)
            else:
                self.logger.debug('Unable to set_tag_list. No tag_edges found. ' +
                                  'self.tag_edges: {}'.format(self.tag_edges))

    def initialize_tag_dict(self):
        '''(Re)initialize the tag field dictionary'''
        if self.options:
            self.tag_dict = {
                'product'       :   self.options.product,
                'tag_name'      :   None,
                'tag_date'      :   None,
                'tagger_name'   :   None,
                            }
        else:
            self.ready = False
            self.logger.error('Unable to initialize_tag_dict')
    
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

    def set_most_recent_tag_name(self):
        '''Set the tag name of the most recent tag.'''
        if self.ready:
            if not self.tag_list: self.set_tag_data()
            self.set_datetime_list()
            self.process_datetime_list()
            self.set_sorted_datetime_list()
            self.set_most_recent_tag()
            self.most_recent_tag_name = self.most_recent_tag['tag_name']

    def set_datetime_list(self):
        '''
            Set a datetime list from the list of dictionaries
            containing tag information.
        '''
        self.datetime_list = None
        if self.ready:
            if self.tags:
                self.datetime_list = [dl['tag_date'] for dl in self.tags
                                      if dl and 'tag_date' in dl]
            else:
                self.logger.debug('Unable to set_datetime_list. No tags found. ' +
                                  'self.tags: {}'.format(self.tags))

    def process_datetime_list(self):
        '''
            Replace the datetime list with only the datetime,
            extracted from the two datetime formats.
        '''
        # There are two possible datetime formats:
        # datetime = 2015-10-12T14:53:11Z
        # datetime = 2017-06-12T15:48:49-04:00
        datetime_list = [dt[0:19] for dt in self.datetime_list]
        self.datetime_list = datetime_list if datetime_list else None

    def set_sorted_datetime_list(self):
        '''Set a sorted datetime list.'''
        self.sorted_datetime_list = list()
        if self.ready:
            if self.datetime_list:
                dtl = self.datetime_list
                dates = [datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
                         for date in dtl]
                dates.sort()
                sorted_dates = [datetime.datetime.strftime(ts, "%Y-%m-%dT%H:%M:%S")
                                for ts in dates]
                self.sorted_datetime_list = sorted_dates
            else:
                self.logger.debug('Unable to set_sorted_datetime_list. No datetime_list found. ' +
                                  'self.datetime_list: {}'.format(self.datetime_list))

    def set_most_recent_tag(self):
        '''Extract the tag dictionary with the most recent datetime.'''
        self.most_recent_tag = None
        if self.ready:
            if self.sorted_datetime_list and self.tags:
                most_recent_datetime = self.sorted_datetime_list[-1]
                tag = [tag for tag in self.tags
                        if most_recent_datetime in tag['tag_date']]
                self.most_recent_tag = tag[0] if tag and len(tag)==1 else None
            else:
                self.logger.debug('Unable to set_most_recent_tag. ' +
                                  'No sorted_datetime_list or tags found. ' +
                                  'self.sorted_datetime_list: {}'.
                                        format(self.sorted_datetime_list) +
                                  'self.tags: {}'.format(self.tags)
                                  )

