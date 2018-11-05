# An output plugin that prints data on stdout

from .pluginbase import Pluginbase
import binascii
import json
from pprint import pprint

class Print(Pluginbase):

    defaults = {
        'print_raw': 'yes',
        'hexlify_raw': 'no',
    }

    def handle_raw(self, data):
        if self.print_raw in [ 'yes', 'true' ]:
            self.logger.debug('Handling raw data')
            if self.hexlify_raw in [ 'yes', 'true' ]:
                print(binascii.hexlify(data).decode('ascii'))
            else:
                print(data)

    def handle_decoded(self, data):
        pprint(data)
#        if type(data) is dict:
#            print(json.dumps(data))
#        else:
#            print(data)
