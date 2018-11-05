from .pluginbase import Pluginbase,PluginError
import binascii

class Unhexlify(Pluginbase):

    defaults = {
        'errors': 'halt'
    }

    def decode(self, data):
        self.logger.debug('Starting decode')
        try:
            return binascii.unhexlify(data)
        except binascii.Error as e:
            if self.errors == 'ignore':
                self.logger.warning('Ignoring binascii.Error: %s' % e)
                pass
            else:
                raise
