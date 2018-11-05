# An output plugin that writes data to a file

from .pluginbase import Pluginbase
import binascii
import os
import sys
import time
import json

class Datafile(Pluginbase):

    defaults = {
        'raw_data_dir': '/var/lib/pyp/raw',
        'raw_data_strftime': '%Y%m%d%H%M%S.raw',
        'decoded_data_dir': '/var/lib/pyp/decoded',
        'decoded_data_strftime': '%Y%m%d%H%M%S.data',
    }

    def initialize(self):
        self.logger.info('Initializing plugin %s' % __name__)
        raw_filename = os.path.join(self.raw_data_dir, '%s' % time.strftime(self.raw_data_strftime))
        try:
            self.raw_datafile = open(raw_filename, 'a', 1)
        except (IOError, PermissionError) as e:
            self.logger.critical('Cannot open raw data file: %s' % e)
            sys.exit(1)
        decoded_filename = os.path.join(self.decoded_data_dir, '%s' % time.strftime(self.decoded_data_strftime))
        try:
            self.decoded_datafile = open(decoded_filename, 'a', 1)
        except (IOError, PermissionError) as e:
            self.logger.critical('Cannot open decoded data file: %s' % e)
            sys.exit(1)

    def handle_raw(self, data):
        self.logger.debug('Handling raw data')
        self.raw_datafile.write(binascii.hexlify(data).decode('ascii') + "\n")
        # This seems necessary even though the file is opened using line-buffering
        self.raw_datafile.flush()

    def handle_decoded(self, data):
        self.logger.debug('Handling decoded data')
        try:
            json.dump(data, self.decoded_datafile, indent=4)
        except TypeError as e:
            self.logger.error('TypeError: %s, retrying with skipkeys enabled. Data may be incomplete.' % e)
            json.dump(data, self.decoded_datafile, skipkeys=True, indent=4)
