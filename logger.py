import logging


logging.basicConfig(format='[%(levelname)s %(asctime)s] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='restapi.log',
                    encoding='utf-8',
                    level=logging.DEBUG)


# create logger
logger = logging.getLogger('restapi_logger')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    '[%(levelname)s %(asctime)s] %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

logger.info("Hello")
logger.error("Hello")
