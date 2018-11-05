from .pluginbase import Pluginbase, PluginError
import binascii
import logging
import pysolaredge

class Solaredge(Pluginbase):

    defaults = {
        'privkey': None,
        'last_503_file': '/var/lib/pyp/503.data',
        'save503': 'yes',
    }

    decoder = None
    data_count = 0

    def initialize(self):
        self.logger.info('Initializing plugin %s' % __name__)
        self.decoder = pysolaredge.Decoder(privkey = self.privkey)
        logging.getLogger("pysolaredge").setLevel(self.loglevel)
        self.init_503()

    def init_503(self):
        try:
            with open(self.last_503_file) as f:
                data = f.readline().rstrip()
        except FileNotFoundError as e:
            self.logger.warning('File with previous 503 message not found: %s' % e)
            return
        if len(data) > 0:
            #self.decode(binascii.unhexlify(data), save503=False)
            data = binascii.unhexlify(data)
            decoded = self.decoder.set_last_503_msg(data)
            self.logger.debug('Decoded data: %s' % str(decoded))
            self.data_count = 0
        else:
            self.logger.warning('Last 503 message is empty')

    def decode(self, data):
        try:
            decoded = self.decoder.decode(data)
            self.data_count += 1
            if decoded['function'] == 0x0503:
                self.save_503(data)
        except pysolaredge.exceptions.CryptoNotReadyError as e:
            self.logger.error(e)
            return {}
        # Handle None from self.decoder.decode()
        except TypeError:
            return {}
        except pysolaredge.exceptions.SeError as e:
            self.logger.error(e)
            return {}
        except Exception:
            raise
        return decoded

    def save_503(self, data):
        if self.last_503_file:
            self.logger.info('Saving 0x0503 to file: %s' % self.last_503_file)
            try:
                with open(self.last_503_file, "w") as f:
                    f.write(binascii.hexlify(data).decode('ascii'))
                self.logger.debug('Finished saving 0x0503')
            except Exception as e:
                self.logger.exception(e)

