import asyncio
from os import getenv
import sys

import click

from .constants import CLIENT_ID, CLIENT_SECRET_VALUE, TENANT_ID
from .env import ENVIRONMENT
from .logging_settings import logging
from .helpers import get_azure_credentials, get_app_role_if_exists
from .interfaces.aws.secrets_manager import get_client
from .interfaces.azure.msgraph_api import MSGraphAPIWrapper
from .handlers.azure import MSGraphRequestHandler, MSGraphRequestHandlerError

logger = logging.getLogger(__name__)

SECRET_ID = getenv('SECRET_ID', f'app-role-assignment-cli/dap/{ENVIRONMENT.lower()}/azure_credentials')


@click.group()
def cli():
    """The app-role main interface"""
    pass


group_arg = click.argument(
    'group_display_name', nargs=1, type=click.STRING, metavar='GROUP_DISPLAY_NAME'
)
application_arg = click.argument(
    'application_display_name', nargs=1, type=click.STRING, metavar='APPLICATION_DISPLAY_NAME'
)
app_role_arg = click.argument(
    'app_role_display_name', nargs=1, type=click.STRING, metavar='APP_ROLE_DISPLAY_NAME'
)


@cli.command()
@app_role_arg
@application_arg
@group_arg
def assign(app_role_display_name: str, application_display_name: str, group_display_name: str):
    """
    The `assign` command grants an AppRoleAssignment to all the users of
    """
    az_creds = get_azure_credentials(get_client(), SECRET_ID)

    msgraph_api = MSGraphAPIWrapper(az_creds[TENANT_ID], az_creds[CLIENT_ID], az_creds[CLIENT_SECRET_VALUE])
    msgraph_api_handler = MSGraphRequestHandler(msgraph_api)

    runner = asyncio.Runner()
    group_id = runner.run(msgraph_api_handler.get_group_id_if_exists(group_display_name))
    if group_id is None:
        sys.exit(f'\'{group_display_name}\' most likely misspelled!')

    app = runner.run(msgraph_api_handler.get_application_if_exists(application_display_name))
    if app is None:
        sys.exit(f'\'{application_display_name}\' most likely misspelled!')

    app_role = get_app_role_if_exists(app_role_display_name, app)
    if app_role is None:
        sys.exit(f'\'{app_role_display_name}\' most likely misspelled!')

    service_principal = runner.run(msgraph_api.get_app_service_principal(app.app_id))
    ret = runner.run(msgraph_api_handler.get_all_user_ids(group_id))
    for u_id in ret:
        try:
            runner.run(
                msgraph_api_handler.grant_app_role_assignment_to_user(u_id, service_principal.id, str(app_role.id))
            )
        except MSGraphRequestHandlerError:
            continue

    logger.info(
        f'Done with granting \'{app_role_display_name}\' defined by \'{application_display_name}\' '
        f'to all users member of \'{group_display_name}\''
    )


@cli.command()
@app_role_arg
@application_arg
@group_arg
def remove(app_role_display_name: str, application_display_name: str, group_display_name: str):
    """
    The `remove` command
    """
    az_creds = get_azure_credentials(get_client(), SECRET_ID)

    msgraph_api = MSGraphAPIWrapper(az_creds[TENANT_ID], az_creds[CLIENT_ID], az_creds[CLIENT_SECRET_VALUE])
    msgraph_api_handler = MSGraphRequestHandler(msgraph_api)

    runner = asyncio.Runner()
    group_id = runner.run(msgraph_api_handler.get_group_id_if_exists(group_display_name))
    if group_id is None:
        sys.exit(f'\'{group_display_name}\' most likely misspelled!')

    app = runner.run(msgraph_api_handler.get_application_if_exists(application_display_name))
    if app is None:
        sys.exit(f'\'{application_display_name}\' most likely misspelled!')

    app_role = get_app_role_if_exists(app_role_display_name, app)
    if app_role is None:
        sys.exit(f'\'{app_role_display_name}\' most likely misspelled!')

    ret = runner.run(msgraph_api_handler.get_all_user_ids(group_id))
    for u_id in ret:
        try:
            app_role_assignment_id = \
                runner.run(
                    msgraph_api_handler.get_app_role_assignment_id(u_id, application_display_name, str(app_role.id))
                )
        except MSGraphRequestHandlerError:
            continue
        else:
            runner.run(msgraph_api_handler.remove_app_role_assignment_from_user(u_id, app_role_assignment_id))

    logger.info(
        f'Done with removing \'{app_role_display_name}\' defined by \'{application_display_name}\' '
        f'from all user members of \'{group_display_name}\''
    )


if __name__ == '__main__':
    cli()
