# app-role-assignment-cli
A simple CLI tool for the Unix shell to assign or remove an `AppRole` to all members of a given Group in Microsoft Entra ID.
To interact with Microsoft Entra ID, you'll need to create an `AppRegistration` with the following API Permissions:
* Application.Read.All
* AppRoleAssignment.ReadWrite.All
* Group.Read.All
* GroupMember.Read.All
* User.ReadWrite.All 

Once the app is registered, you'll need to create a Client secret (created in the "Certificates & secrets" section
of the registered `Application`).

The `app-role` command exposes two interfaces for granting and deleting an AppRoleAssignment to the users:

* `assign`:
    ```
    Usage: app-role assign [OPTIONS] APP_ROLE_DISPLAY_NAME APPLICATION_DISPLAY_NAME GROUP_DISPLAY_NAME
    ```

* `remove`:
  ```
  Usage: app-role remove [OPTIONS] APP_ROLE_DISPLAY_NAME APPLICATION_DISPLAY_NAME GROUP_DISPLAY_NAME
  ```

## Running Locally

To authenticate the requests the main interface `MSGraphAPIWrapper` class, is instantiated with `tenant_id`,
`client_id`, and `client_secret_value`. At the moment, the secret holding these values is fetched from AWS Secrets Manager.

    aws secretsmanager create-secret --name "app-role-assignment-cli/dap/local/azure_credentials"   \
    --secret-string '{"client_secret_value":"<>","client_secret_id":"<>","client_id":"<>","tenant_id":"<>"}' \
    --endpoint-url=http://localhost:4566 --region eu-west-1