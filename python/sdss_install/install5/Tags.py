from sdss_install.application import Store
from json import dumps
import datetime
#from datetime import datetime.strptime as strptime


class Tags:

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.query_file_name = 'tags'
        self.store = None
        self.tag_list = None


    def set_logger(self, logger=None):
        '''Set the class logger'''
        self.logger = logger if logger else None
        if not self.logger:
            print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        '''Set command line argument options'''
        self.options = options if options else None
        if not self.options: self.logger.error('Unable to set_options')

    def most_recent_tag_name(self):
        '''Get the most recent GitHub tag name associated with the product'''
        self.set_tags()
        self.set_most_recent_tag_name()
        tag_name = (self.most_recent_tag_name
                    if self.most_recent_tag_name
                    else None)
        return tag_name

    def get_tag_names(self):
        '''Get a list of tag names associated with the product.'''
        self.set_tags()
        tag_names = ([tag['tag_name'] for tag in self.tags]
                     if self.tags
                     else None)
        return tag_names

    def set_tags(self):
        '''
            Concatenate a list of dictionaries from all GraphQL pages
            containing tag information.
        '''
        self.tags = list()
        self.set_store()
        self.set_query_parameters()
        self.set_tag_data()
        self.tags.extend(self.tag_list)
        pagination_flag = True
        while pagination_flag:
            if self.page_info['hasNextPage']:
                self.logger.debug('********** Paginating **********')
                self.set_pagination_parameters()
                self.set_tag_data()
                self.tags.extend(self.tag_list)
            else: pagination_flag = False
        if not self.tags: self.logger.debug('No tags: self.tags=%r' % self.tags)

    def set_store(self):
        '''
            Set a class Store instance and its attributes:
            organization name and a class Client instance.
        '''
        if self.options and not self.store:
            self.store = Store(logger=self.logger, options=self.options)
            self.store.set_organization_name()
            self.store.set_client()
        else: self.logger.error('Unable to set_store')

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
            self.logger.error('Unable to set query_parameters. ' +
                                'self.store = %r' % self.store)

    def set_tag_data(self):
        '''
            Set GraphQL query payload data then extract field edges
            and pagination information.
        '''
        self.set_tag_payload()
        self.set_tag_edges_and_page_info()
        self.set_tag_list()
    
    def set_tag_payload(self):
        '''Set GraphQL query payload data.'''
        self.tag_payload = None
        if self.store.client and self.query_parameters:
            self.store.set_data(query_parameters=self.query_parameters)
            self.tag_payload = (self.store.client.data
                                if self.store.client.data
                                else None)
        else: self.logger.error('Unable to set_tag_data')

    def set_tag_edges_and_page_info(self, data=None):
        '''
            From the GraphQL query payload data, set a pagination information
            dictionary and a list of dictionaries containing tag fields.
        '''
        self.tag_edges = None
        self.page_info = None
        data = self.tag_payload if self.tag_payload else None
        if data:
            data = data['organization']['repository']['tags'] if data else None
            self.tag_edges = data['edges']                    if data else None
            self.page_info = data['pageInfo']                 if data else None
        else: self.logger.error('Unable to set_tag_edges_and_page_info')

    def set_tag_list(self):
        '''
            Set a list of dictionaries from the tag field list of dictionaries.
        '''
        self.tag_list = list()
        if self.tag_edges:
            for tag_ in self.tag_edges:
                tag = tag_['tag']
                self.initialize_tag_dict()
                self.tag_dict['tag_name'] = tag['name']
                if   tag['target']['__typename'] == 'Commit': key = 'author'
                elif tag['target']['__typename'] == 'Tag': key = 'tagger'
                else: self.logger.error('Unexpected __typename')
                self.tag_dict['tag_date']    = tag['target'][key]['date']
                self.tag_dict['tagger_name'] = tag['target'][key]['name']
                self.tag_list.append(self.tag_dict)
        else:
            self.logger.debug('No tag_edges: self.tag_edges=%r'
                                % self.tag_edges)

    def initialize_tag_dict(self):
        '''(Re)initialize the tag field dictionary'''
        if self.options:
            self.tag_dict = {
                'product'       :   self.options.product,
                'tag_name'      :   None,
                'tag_date'      :   None,
                'tagger_name'   :   None,
                            }
        else: self.logger.error('Unable to initialize_tag_dict')
    
    def set_pagination_parameters(self):
        '''
            Set pagination parameters for next page
            from pagination infomation dictionary.
        '''
        if self.query_parameters and self.page_info:
            self.query_parameters['pagination_flag'] = True
            self.query_parameters['end_cursor'] = self.page_info['endCursor']
            self.query_parameters['has_next_page'] = (
                self.page_info['hasNextPage'])
        else:
            self.logger.error(
            'ERROR: pagination parameters could not be set.\n' +
            'query_parameters = %s\npage_info = %s'
            % (self.query_parameters, self.page_info))


    def set_most_recent_tag_name(self):
        '''Set the tag name of the most recent tag.'''
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
        if self.tags:
            self.datetime_list = [dl['tag_date'] for dl in self.tags]
        else: self.logger.error('Unable to set_list_from_dict_list_key')

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
        if self.datetime_list:
            dtl = self.datetime_list
            dates = [datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
                        for date in dtl]
            dates.sort()
            sorted_dates = [datetime.datetime.strftime(ts, "%Y-%m-%dT%H:%M:%S")
                            for ts in dates]
            self.sorted_datetime_list = sorted_dates
        else: self.logger.error('Unable to set_sorted_datetime_list')

    def set_most_recent_tag(self):
        '''Extract the tag dictionary with the most recent datetime.'''
        self.most_recent_tag = None
        if self.sorted_datetime_list and self.tags:
            most_recent_datetime = self.sorted_datetime_list[-1]
            tag = [tag for tag in self.tags
                    if most_recent_datetime in tag['tag_date']]
            self.most_recent_tag = tag[0] if tag and len(tag)==1 else None
        else: self.logger.error('Unable to set_most_recent_tag')
