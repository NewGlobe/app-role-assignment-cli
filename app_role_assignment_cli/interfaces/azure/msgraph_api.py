from uuid import UUID

from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.application import Application
from msgraph.generated.models.group import Group
from msgraph.generated.models.user import User
from msgraph.generated.models.app_role_assignment import AppRoleAssignment
from msgraph.generated.models.service_principal import ServicePrincipal
from msgraph.generated.groups.item.app_role_assignments.app_role_assignments_request_builder \
    import AppRoleAssignmentsRequestBuilder
from msgraph.generated.groups.item.members.members_request_builder import MembersRequestBuilder
from msgraph.generated.service_principals.service_principals_request_builder import ServicePrincipalsRequestBuilder
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder
from msgraph.generated.applications.applications_request_builder import ApplicationsRequestBuilder
from kiota_abstractions.api_error import APIError

from app_role_assignment_cli.logging_settings import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://graph.microsoft.com/.default']


class MSGraphAPIWrapper:
    """
    Wrapper class for the Microsoft Graph API.
    """
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, scopes: list | None = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes if scopes is not None else SCOPES
        self.credential = self._get_client_credential()
        self.client = self._get_client()

    def _get_client_credential(self) -> ClientSecretCredential:
        """
        Get the client secret credential given a pair the client_id/client_secret pair.

        Returns:
            ClientSecretCredential: an instance of the ClientSecretCredential class.
        """
        return ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)

    def _get_client(self) -> GraphServiceClient:
        """
        Get the GraphServiceClient interface.

        Returns:
            GraphServiceClient: an instance of the GraphServiceClient class.
        """
        return GraphServiceClient(credentials=self.credential, scopes=self.scopes)

    async def get_group(self, group_display_name: str) -> Group | None:
        """
        Get the group by display name invoking the Microsoft Graph API.

        Args:
            group_display_name: the group display name to search for.

        Returns:
            Group: the group object or None if the group is not found.
        """
        query_params = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
            filter=f"displayName eq '{group_display_name}'",
            count=True,
            expand=["members"]
            # expand=["appRoleAssignments",] only returns 20 results of the expanded entity
            # it could have been an option to avoid one API call.
            # See https://developer.microsoft.com/en-us/graph/known-issues/?search=13635
        )
        request_config = GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        try:
            groups = await self.client.groups.get(request_configuration=request_config)
        except APIError as e:
            logger.error(f'{e}')
        else:
            if not groups.value:
                logger.warning(f'No groups found for filter={query_params.filter}')
                return
            assert len(groups.value) == 1, f'Unexpected response: {groups=}'
            return groups.value[0]

    async def get_all_user_group_members(self, group_id: str) -> list[User]:
        """
        Get all the id's of the members of a group (by group id).

        Args:
            group_id: the group id to search for.

        Returns:
            list[str]: the list of user-principal-names of the members of the group.
        """
        async def _extend_user_members(fetched_members: list[DirectoryObject]):
            for member in fetched_members:
                match member:
                    case User():
                        members.append(member)
                    case Group():
                        members.extend(await self.get_all_user_group_members(member.id))
                    case _:
                        logger.warning(f'Skipping {member.__class__} as not supported')

        query_params = MembersRequestBuilder.MembersRequestBuilderGetQueryParameters(top=999)
        request_configuration = MembersRequestBuilder.MembersRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        members = []
        try:
            res = await self.client.groups.by_group_id(group_id).members.\
                get(request_configuration=request_configuration)
        except APIError as e:
            logger.error(f'{e}')
        else:
            if res.value:
                await _extend_user_members(res.value)
                next_link = res.odata_next_link
                while next_link:
                    try:
                        next_members = await self.client.groups.with_url(next_link).get()
                    except APIError as e:
                        logger.error(f'Could not fetch more members: {e}')
                        return members
                    else:
                        next_link = next_members.odata_next_link
                        await _extend_user_members(next_members.value)

        return members

    async def get_application(self, application_display_name: str) -> Application | None:
        """
        Get the Application by displayName.

        Args:
            application_display_name: the displayName of the Application

        Returns:
            Application or None: the application object of None if not found or request error.
        """
        query_params = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetQueryParameters(
            filter=f"displayName eq '{application_display_name}'"
        )
        request_config = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        try:
            applications = await self.client.applications.get(request_configuration=request_config)
        except APIError as e:
            logger.error(f'{e}')
        else:
            if not applications.value:
                logger.warning(f'\'{application_display_name}\' not found!')
                return
            assert len(applications.value) == 1, f'More than one application found!: {applications=}'
            return applications.value[0]

    async def get_app_service_principal(self, app_id: str) -> ServicePrincipal | None:
        """
        Retrieve the appRoles for the subset of resources and appRole id's in input coming from the appRoleAssignments.
        First the resource (application) ids are used to filter the service-principal request.
        Then the application-role ids are used to filter the response.

        Args:
            app_id: the appId of the application resource.

        Returns:
            ServicePrincipal or None: the ServicePrincipal object or None if not found or request error.
        """
        query_params = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
            filter=f"appId eq '{app_id}'",
        )
        request_configuration = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        try:
            res = await self.client.service_principals.get(request_configuration=request_configuration)
        except APIError as e:
            logger.error(f'{e}')
            return
        else:
            if not res.value:
                logger.warning(f'ServicePrincipal for \'{app_id=}\' not found!')
                return
            assert len(res.value) == 1, f'More than one servicePrincipal found: {res=}'
            return res.value[0]

    async def get_app_role_assignments_for_user(
            self, user_id: str, resource_display_name: str
    ) -> list[AppRoleAssignment] | None:
        """
        Retrieve the appRoleAssignments of a group for a specific resource (application). The appRoleAssignment object
        holds the `resource_id` (the id of the application realizing the assignment) and the `app_role_id`, the id
        of the appRole assigned to the group. Unfortunately the appRole value is not present in the response.

        Args:
            user_id: the id of the group we want to retrieve the appRoleAssignments.
            resource_display_name: the display name of the resource (application) assigning the app roles to the group.

        Returns:
            list | None: a list of AppRoleAssignment objects or none.
        """
        query_params = AppRoleAssignmentsRequestBuilder.AppRoleAssignmentsRequestBuilderGetQueryParameters(
            filter=f"resourceDisplayName eq '{resource_display_name}'",
            count=True,
        )
        request_configuration = AppRoleAssignmentsRequestBuilder.\
            AppRoleAssignmentsRequestBuilderGetRequestConfiguration(query_parameters=query_params)
        request_configuration.headers.add("ConsistencyLevel", "eventual")
        try:
            res = await self.client.users.by_user_id(user_id).app_role_assignments.\
                get(request_configuration=request_configuration)
        except APIError as e:
            logger.error(f'{e}')
        else:
            logger.info(f'Found {len(res.value)} AppRoleAssignment(s) for {resource_display_name=}')
            return [r for r in res.value if r.principal_type == 'User']

    async def grant_app_role_assignment_to_user(
            self,
            user_id: str,
            resource_id: str,
            app_role_id: str
    ) -> None:
        """
        Assign an app role to a user, creating an appRoleAssignment object.
        To grant an app role assignment to a user, we need the three identifiers in args.
        See https://learn.microsoft.com/en-us/graph/api/user-post-approleassignments?view=graph-rest-1.0&tabs=python

        Args:
            user_id: The id of the user to whom you are assigning the app role.
            resource_id: The id of the resource servicePrincipal that has defined the app role.
            app_role_id: The id of the appRole (defined on the resource service principal) to assign to the user.

        Returns:
            None.
        """
        request_body = AppRoleAssignment(
            principal_id=UUID(user_id),
            resource_id=UUID(resource_id),
            app_role_id=UUID(app_role_id),
        )
        try:
            result = await self.client.users.by_user_id(user_id).app_role_assignments.post(request_body)
        except APIError as e:
            logger.error(f'{e}')
        else:
            logger.info(f'Granted {result.resource_display_name} to {user_id=}')

    async def delete_app_role_assignment(self, user_id: str, app_role_assignment_id: str) -> None:
        """
        See https://learn.microsoft.com/en-us/graph/api/user-delete-approleassignments?view=graph-rest-1.0&tabs=python

        Args:
            user_id:
            app_role_assignment_id:

        Returns:
            None.
        """
        try:
            _ = await self.client.users.by_user_id(user_id).app_role_assignments.\
                by_app_role_assignment_id(app_role_assignment_id).delete()
        except APIError as e:
            logger.error(f'{e}')
        else:
            logger.info(f'Deleted AppRoleAssignment({app_role_assignment_id}) from {user_id=}')
