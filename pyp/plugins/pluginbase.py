import logging

class Pluginbase(object):

    # Decoder plugins can set this for input plugins to consume
    response = None

    def __init__(self, config, callback=None):
        self.config = config
        self.logger = logging.getLogger(self.__module__)
        self.loglevel = int(config.get('loglevel'))
        self.logger.debug('Plugin %s loglevel: %d' % (self.__module__, self.loglevel))

        # Convert known config keys to object attributes
        try:
            for key in self.defaults:
                val = config.get(key, self.defaults[key])
                self.logger.info('Setting attribute: %s = %s' % (key, val))
                setattr(self, key, val)
        except AttributeError:
            pass

        if callback is not None:
            self.set_callback(callback)

        # If this plugin has an initialization method, call it
        try:
            self.initialize()
        except AttributeError:
            pass
        except PluginError as e:
            self.logger.error(e)
        except Exception as e:
            self.logger.exception(e)
            raise

    def set_callback(self, callback):
        self.callback = callback

class PluginError(Exception):

    def __init__(self, message):

        # Call base class constructor
        super().__init__(message)

        self.message = message
