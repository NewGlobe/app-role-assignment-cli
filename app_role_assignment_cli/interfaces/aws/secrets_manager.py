import json
from os import environ

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app_role_assignment_cli.env import AWS_REGION, ENVIRONMENT
from app_role_assignment_cli.logging_settings import logging

logger = logging.getLogger(__name__)


def get_client() -> BaseClient:
    """
    Instantiate a Secrets Manager client interface.

    Returns:
        BaseClient: an AWS Secrets Manager client.
    """
    if ENVIRONMENT == 'local':
        logger.info('Returning local secretsmanager client')
        return boto3.client(
            'secretsmanager',
            endpoint_url=f'http://localhost:{environ['LOCAL_SECRETS_MANAGER_PORT']}',
            region_name=AWS_REGION
        )
    else:
        logger.info('Returning remote secretsmanager client')
        return boto3.client('secretsmanager', region_name=AWS_REGION)


def get_secret(client: BaseClient, secret_id: str) -> dict | None:
    try:
        secret = client.get_secret_value(SecretId=secret_id)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f'Requested secret={secret_id} does not exists.')
            return
        raise e
    else:
        return json.loads(secret['SecretString'])
