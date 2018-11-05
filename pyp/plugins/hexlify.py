from .pluginbase import Pluginbase,PluginError
import binascii

class Hexlify(Pluginbase):

    def decode(self, data):
        return binascii.hexlify(data).decode('ascii')
