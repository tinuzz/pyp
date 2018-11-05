from .pluginbase import Pluginbase,PluginError
import datetime

class Noop(Pluginbase):

    def decode(self, data):
        self.response = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return { 'data': data }

