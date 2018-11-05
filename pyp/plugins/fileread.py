from .pluginbase import Pluginbase, PluginError
import binascii
import time

class Fileread(Pluginbase):

    defaults = {
        'filename': None,
        'statefile': '/var/lib/pyp/fileread.state',
        'unhexlify': 'no',
        'follow': 'no',
        'follow_delay': '2',
    }

    def initialize(self):
        # Try to read state from a file. Writing a state file is not implemented yet.
        try:
            with open(self.statefile) as f:
                data = f.readline().rstrip()
        except FileNotFoundError as e:
            self.logger.warning("No old state found.")
            return

    def process_line(self, line):
        line = line.rstrip()
        if len(line) > 0:
            if self.unhexlify in [ 'yes', 'true' ]:
                line = binascii.unhexlify(line)
            self.callback(line)

    def follow_file(self, f):
        # Seek to the end of the gfile
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(int(self.follow_delay))
                continue
            yield line

    def run(self):
        if self.filename is not None:
            self.logger.info('Running fileread plugin with file: %s' % self.filename)
            try:
                with open(self.filename) as f:
                    for line in f:
                        self.process_line(line)
                    if self.follow in [ 'yes', 'true' ]:
                        content = self.follow_file(f)
                        for line in content:
                            self.process_line(line)
            except FileNotFoundError as e:
                self.logger.critical('File not found: %s' % e)
        else:
            self.logger.critical('No input file specified')
