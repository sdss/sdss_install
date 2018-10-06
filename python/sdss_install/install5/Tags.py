from sdss_install.application import Store
from json import dumps

class Tags:

    def __init__(self, logger=None, options=None):
        self.set_logger(logger=logger)
        self.set_options(options=options)
        self.query_file_name = 'tags'


    def set_logger(self, logger=None):
        self.logger = logger if logger else None
        if not self.logger: print('ERROR: %r> Unable to set logger.' % self.__class__)

    def set_options(self, options=None):
        self.options = options if options else None
        if not self.options: self.logger.error('ERROR: Unable to set_options')

    def most_recent_tag(self):
        self.set_tags()
        
    def set_tags(self):
        self.set_store()
        self.set_data()

    def set_store(self):
        if self.options:
            self.store = Store(logger=self.logger, options=self.options)
            self.store.set_organization_name()
            self.store.set_client()
        else: self.logger.error('ERROR: Unable to set_store')

    def set_data(self):
        '''Set query payload data and extract field edges and pagination information.'''
        self.set_tag_payload()
        self.set_tag_edges_and_page_info()
        self.set_tag_data()
        
    def set_tag_payload(self):
        self.tag_payload = None
        self.set_query_parameters()
        if self.store.client and self.query_parameters:
            self.store.set_data(query_parameters=self.query_parameters)
            self.tag_payload = self.store.client.data if self.store.client.data else None
        else: self.logger.error('ERROR: Unable to set_data')

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

    def set_tag_edges_and_page_info(self, data=None):
        '''Set a dictionary of page information and a list of dictionaries containing tag fields.'''
        self.tag_edges = None
        self.page_info = None
        data = self.tag_payload if self.tag_payload else None
        if data:
            data = data['organization']['repository']['tags'] if data else None
            self.tag_edges = data['edges']                   if data else None
            self.page_info = data['pageInfo']                 if data else None
            print('self.tag_payload: \n' + dumps(self.tag_payload,indent=1))
            print('self.page_info: \n' + dumps(self.page_info,indent=1))
        else: self.logger.error('ERROR: Unable to set_tag_edges_and_page_info')

    def set_tag_data(self):
        self.tag_data = list()
        self.initialize_tag_dict()
#        if self.tag_edges:
#            for tag_ in self.tag_edges:
#                tag = tag_['tag']
#                print('tag: \n' + dumps(tag,indent=1))
#                self.pause()
#                self.tag_dict['tag_name'] = tag['name']
#                if tag['target']['__typename'] == 'Commit': key = 'author'
#                elif tag['target']['__typename'] == 'Tag': key = 'tagger'
#                print('key: %s :' % key)
#                self.pause()
#                self.tag_dict['tagger_name'] = tag[key]['name']
#                self.tag_dict['tagger_date'] = tag[key]['name']
#                self.tag_data.append(self.tag_dict)
#        else: self.logger.error('ERROR: Unable to set_tag_data')
#        print('self.tag_data: \n' + dumps(self.tag_data,indent=1))
#        self.pause()

    def initialize_tag_dict(self):
        self.tag_dict = {
            'tag_name'      :   None,
            'tagger_name'   :   None,
            'tagger_date'   :   None,
                        }
    


    def pause(self):
        input('Press enter to continue')
