# This plugin implements a TCP socket server that takes 1 concurrent connection

from .pluginbase import Pluginbase
from socketserver import BaseRequestHandler, TCPServer

class SockHandler(BaseRequestHandler):

    def __init__(self, plugin, callback, *args, **kwargs):
        self.callback = callback
        self.plugin = plugin
        super().__init__(*args, **kwargs)

    def handle(self):
        # On accepting the connection, store the client socket on the plugin
        # object, so it can send data to the client
        self.plugin.clientsocket = self.request
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024)
            if not self.data:
                break
            self.callback(self.data)

class Listen(Pluginbase):

    defaults = {
        'host': '0.0.0.0',
        'port': 22222,
        'callback': None,
    }

    def handler_factory(self, callback):
        def createHandler(*args, **keys):
            return SockHandler(self, callback, *args, **keys)
        return createHandler

    def run(self):
        server = TCPServer((self.host, int(self.port)), self.handler_factory(self.callback))
        server.serve_forever()

    # This method is called at the end of the input callback, with response
    # data from the decoder
    def respond(self, resp):
        self.logger.debug('Sending response: %s' % resp)
        self.clientsocket.sendall(resp.encode('utf-8'))
        self.clientsocket.sendall(b'\r\n')
