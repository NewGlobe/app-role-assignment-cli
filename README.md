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

## Running The Commands

To authenticate the Microsoft Graph API requests the main interface `MSGraphAPIWrapper` class needs to be instantiated
with `tenant_id`,`client_id`, and `client_secret_value`. At the moment, the secret holding these values is fetched from 
AWS Secrets Manager, and the `SECRET_ID` environment variable holds the secret name to fetch.
At the moment this defaults to `app-role-assignment-cli/dap/<environment>/azure_credentials`, where `<environment>` is
a placeholder for the lowercase version of the `ENVIRONMENT` environment variable.

The AWS Secrets Manager client is created via the `boto3` library, which implicitly looks for `AWS_ACCESS_KEY_ID` 
and `AWS_SECRET_ACCESS_KEY` environment variables. Locally, the configuration is held in the `local.env` file and, as
explained below, [localstack](https://github.com/localstack/localstack) is used to store and retrieve the secret.

### Local Set Up

To run the commands locally, make sure `localstack` is up and running. This emulates the AWS cloud environment, and
it can therefore be used to store the necessary secret that'll be retrieved at run time.

This project is equipped with the necessary `docker-compose.yml` to run `localstack`. Before that, populate the
environment with the variables in `local.env`:

    set -a && source local.env && set +a

Then start the container with:

    docker compose -f docker-compose.yml up -d

To store the secret you can use the [aws cli](https://aws.amazon.com/cli/) like:

    aws secretsmanager create-secret --name "app-role-assignment-cli/dap/local/azure_credentials"   \
    --secret-string '{"client_secret_value":"<client_secret_value>","client_id":"<client_id>","tenant_id":"<tenant_id>"}' \
    --endpoint-url=http://localhost:4566 --region eu-west-1

once you've created the secret in the App Registration page in Azure portal.
