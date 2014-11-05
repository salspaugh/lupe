from logging import DEBUG, getLogger as get_logger
from logging.handlers import RotatingFileHandler
import logging

BYTES_IN_MB = 1048576
FIVE_MB = 5*BYTES_IN_MB

logger = get_logger("lupe")
logger.setLevel(DEBUG)
handler = RotatingFileHandler("lupe.log", maxBytes=FIVE_MB)
handler.setLevel(DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

