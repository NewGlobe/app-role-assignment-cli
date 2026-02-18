import os

from .logging_settings import logging

logger = logging.getLogger(__name__)

ENVIRONMENT = os.environ['ENVIRONMENT']

# AWS
AWS_REGION = os.getenv('AWS_REGION')
if AWS_REGION is None:
    AWS_REGION = 'eu-west-1'
    logger.warning(f'AWS_REGION environment variable not found, defaulting to {AWS_REGION}')

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

logger.info('Loaded environment variables')
