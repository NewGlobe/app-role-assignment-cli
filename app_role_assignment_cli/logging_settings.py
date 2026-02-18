import logging
import os

logging.basicConfig(
    level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(module)s - %(funcName)s - %(message)s',
    handlers=[logging.StreamHandler(),]
)
