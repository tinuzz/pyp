from .pluginbase import Pluginbase, PluginError
import binascii
import time
import os

class Fileread(Pluginbase):

    defaults = {
        'filename': None,
        'statefile': '/var/lib/pyp/fileread.state',
        'unhexlify': 'no',
        'follow': 'no',
        'follow_delay': '2',
        'retry_reopen': '0',  # if FileNotFoundError on reopen, retry for this many seconds. 0 means 'fail immediately'.
    }

    filesize = 0

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
        # Seek to the end of the file
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(int(self.follow_delay))
                # If the second stat call raises a FileNotFoundError, run() will handle it.
                stat_fd = os.stat(f.fileno())
                stat_fn = os.stat(self.filename)
                if stat_fd.st_ino != stat_fn.st_ino:
                    self.filesize = 0
                    raise PluginError('File has been moved.')
                if stat_fd.st_size < self.filesize:
                    self.filesize = 0
                    raise PluginError('File has been truncated.')
                self.filesize = stat_fd.st_size
                continue
            yield line

    def run(self):
        if self.filename is not None:
            self.logger.info('Running fileread plugin with file: %s' % self.filename)
            reopen_tries = 0
            while True:
                try:
                    self.logger.info('Opening file: %s' % self.filename)
                    with open(self.filename) as f:
                        reopen_tries = 0
                        for line in f:
                            self.process_line(line)
                        if self.follow in [ 'yes', 'true' ]:
                            content = self.follow_file(f)
                            for line in content:
                                self.process_line(line)
                    f.close()
                    break   # only executed when follow == false
                except PluginError as e:
                    f.close()
                    self.logger.info(e.message)
                except FileNotFoundError as e:
                    self.logger.critical('File not found: %s' % e)
                    if int(self.retry_reopen) == 0 or reopen_tries > int(self.retry_reopen):
                        break
                    reopen_tries += 1
                    time.sleep(1)
            self.logger.info('Fileread plugin done.')
        else:
            self.logger.critical('No input file specified')
