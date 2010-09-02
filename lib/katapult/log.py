import logging

_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def basic_config():
    # basicConfig has no effect in appengine, but it's useful when running unit tests locally
    logging.basicConfig(level=logging.DEBUG, format=_format)
    logging.getLogger().setLevel(logging.DEBUG)


class LoggerFactory:
    
    @classmethod
    def logger(cls, name):
        return Logger(name)


class Logger:
    
    def __init__(self, name):
        self.__name = name
    
    def __msg(self, msg):
        return "[%s] %s" % (self.__name, msg)
        
    def debug(self, msg):
        logging.debug(self.__msg(msg))
    
    def info(self, msg):
        logging.info(self.__msg(msg))
        
    def warn(self, msg):
        logging.warn(self.__msg(msg))
        
    def error(self, msg):
        logging.error(self.__msg(msg))

    def fatal(self, msg):
        logging.fatal(self.__msg(msg))