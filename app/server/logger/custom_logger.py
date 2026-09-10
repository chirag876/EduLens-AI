import logging
import sys

from loguru import logger

from app.server.config import config
from app.server.static import constants

logging.getLogger('uvicorn').handlers.clear()

FORMAT = '{level} | {time} | {message} | {extra[service]} | {extra[environment]}'

logger.remove(0)
logger.add(sys.stdout, level='DEBUG', format=FORMAT, enqueue=True, backtrace=False, diagnose=False, serialize=False)
logger.add('logs/app.log', rotation='10 MB', retention=5, format=FORMAT, enqueue=True, backtrace=False, diagnose=False, serialize=False)
logger.add(sys.stderr, level='ERROR', format=FORMAT, enqueue=True, backtrace=False, diagnose=False, serialize=False)
logger = logger.bind(service=constants.LOGGER_SERVICE_NAME, environment=config.ENV_NAME)