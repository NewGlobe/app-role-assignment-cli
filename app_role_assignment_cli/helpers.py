from msgraph.generated.models.app_role import AppRole
from msgraph.generated.models.application import Application

from .logging_settings import logging
from .interfaces.aws.secrets_manager import BaseClient, get_secret
from .exceptions import AppRoleAssignmentBaseException

logger = logging.getLogger(__name__)


class CredentialsRetrievalError(AppRoleAssignmentBaseException):
    pass


def get_azure_credentials(aws_secrets_manager_client: BaseClient, secret_id: str) -> dict | None:
    """Get Azure credentials from AWS Secrets Manager or fall-back to environment variables"""
    try:
        secret = get_secret(aws_secrets_manager_client, secret_id)
    except Exception as e:
        raise CredentialsRetrievalError(f'Unable to get secret from AWS Secrets Manager. Occurred {e}')
    else:
        if secret is not None:
            logger.info(f'Found {secret_id} in AWS Secrets Manager')
            return secret
        logger.error(f'Secret {secret_id} not found.')


def get_app_role_if_exists(app_role_display_name: str, application: Application) -> AppRole | None:
    try:
        app_role = next(
            filter(lambda x: x.display_name == app_role_display_name, application.app_roles)
        )
    except StopIteration:
        logger.error(f'\'{app_role_display_name}\' is not defined by \'{application.display_name}\'')
        return
    else:
        return app_role
