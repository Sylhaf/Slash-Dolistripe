from distutils.debug import DEBUG
import logging
from logging.handlers import RotatingFileHandler

global logger_name
logger_name = "slash-dolistripe"
__is_init__ = False





def init() :

    global __is_init__
    if __is_init__ :
        return
    #create log folder at execution path"
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create a custom logger
    logger = logging.getLogger(logger_name)

    #TODO create Categories here
    # of this style : logger = logging.getLogger(logger_name + ".persistence")

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = RotatingFileHandler('logs/slash-dolistripe.log',encoding = "UTF-8",backupCount=5,maxBytes=20000000) # 2mo per log
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)
    f_handler.doRollover()

    # Create formatters and add it to handlers
    c_format = logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    logger.setLevel(logging.DEBUG)

    logger.debug("logging engine started")
    __is_init__ = True
