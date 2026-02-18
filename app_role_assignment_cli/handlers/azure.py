import time
from random import random

from app_role_assignment_cli.interfaces.azure.msgraph_api import MSGraphAPIWrapper, Application
from app_role_assignment_cli.logging_settings import logging
from app_role_assignment_cli.exceptions import AppRoleAssignmentBaseException

logger = logging.getLogger(__name__)


class MSGraphRequestHandlerError(AppRoleAssignmentBaseException):
    pass


class MSGraphRequestHandler:
    def __init__(self, api: MSGraphAPIWrapper):
        self.api = api

    async def get_group_id_if_exists(self, group_display_name: str) -> str | None:
        try:
            _group = await self.api.get_group(group_display_name)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the GET Group request. Occurred {e}')
        else:
            if _group is not None:
                return _group.id

    async def get_application_if_exists(self, application_display_name: str) -> Application | None:
        try:
            _application = await self.api.get_application(application_display_name)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the GET Application request. Occurred {e}')
        else:
            if _application is not None:
                return _application

    async def get_all_user_ids(self, group_id: str) -> list[str]:
        try:
            users = await self.api.get_all_group_members(group_id)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the GET Members request. Occurred {e}')
        else:
            if users is not None:
                return [u.id for u in users]

    async def get_app_role_assignment_id(self, user_id: str, application_display_name) -> str:
        try:
            app_role_assignment = await self.api.get_app_role_assignment_for_user(user_id, application_display_name)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the GET AppRoleAssignment request. Occurred {e}')
        else:
            if app_role_assignment is not None:
                return str(app_role_assignment.id)

    async def grant_app_role_assignment_to_user(self, user_id: str, app_id: str, app_role_id: str):
        logger.info(f'Granting AppRole({app_role_id}) to User({user_id})')
        try:
            _res = await self.api.grant_app_role_assignment_to_user(user_id, app_id, app_role_id)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the POST AppRoleAssignment request. Occurred {e}')
        else:
            time.sleep(round(random(), 2))

    async def remove_app_role_assignment_from_user(self, user_id: str, app_role_assignment_id: str):
        logger.info(f'Removing AppRoleAssignment({app_role_assignment_id}) from User({user_id})')
        try:
            _res = await self.api.delete_app_role_assignment(user_id, app_role_assignment_id)
        except Exception as e:
            raise MSGraphRequestHandlerError(f'Could not handle the DELETE AppRoleAssignment request. Occurred {e}')
        else:
            time.sleep(round(random(), 2))
