# AWS CLI Configuration for DevContainer

This document provides a comprehensive guide for configuring the AWS Command Line Interface (CLI) within the DevContainer.
Two distinct approaches are outlined: utilizing a custom configuration exclusive to the container, and leveraging the host machine's existing AWS configuration.

If you do not have AWS credentials yet, reopen the project in the container and follow the instructions in the section [Account Initialization Procedure](#account-initialization-procedure).

## Custom Container Configuration

The `.aws` directory in this repository serves as a mount point for AWS CLI configurations and credentials within the DevContainer.
The content of this folder is configured to be ignored by the version control system, ensuring that your credentials will remain exclusively on your local machine.

## Host Configuration Integration

Should you prefer to use your host machine's AWS configuration, the `.devcontainer/devcontainer.json` file can be modified to achieve this. Under the `mounts` section, amend the corresponding AWS entry as illustrated below:

```json
{
  ...
  // Configure mounts from host to container.
  "mounts": [
    ...
    // To use the host's AWS configuration, replace the following line:
    // "source=${localEnv:HOME}/.aws,target=/home/vscode/.aws,type=bind"
    "source=${localWorkspaceFolder}/.aws,target=/home/vscode/.aws,type=bind"
  ]
}
```

## Account Initialization Procedure

If you do not currently have an AWS account, the following is a concise outline for setting up an initial account and user, distilled from AWS's more comprehensive [Getting Started Guide](https://aws.amazon.com/getting-started/guides/setup-environment/).

1. **Initial Setup**: Create an AWS account, which automatically establishes a [root user](https://docs.aws.amazon.com/signin/latest/userguide/account-root-user-type.html).

    - **Security Measures**: It is advisable to enable Multi-Factor Authentication (MFA) for the root user immediately for basic security. Navigate to `IAM -> Add MFA`.

2. **IAM User Creation**: For operational tasks, avoid using the root user. Instead, create a secondary IAM user with administrative privileges.

    - Navigate to `IAM -> Users -> Create user` and proceed to attach the `AdministratorAccess` policy.

3. **API Credentials**: Subsequent to user creation, generate the necessary API credentials.

    - Click on the username and select `Create access key`. Note that although temporary credentials are recommended for heightened security, permanent credentials are deemed sufficient for the purpose of this guide. Ensure that you store the `Access key` and `Secret access key` in a secure location.

4. **Local CLI Configuration**: Lastly, configure your local AWS CLI via the `aws configure` command. You will be prompted to enter the `Access key ID` and `Secret access key` generated earlier, as well as your preferred AWS region (e.g., `eu-west-3`). This action will create `~/.aws/credentials` and `~/.aws/config` files, completing the setup.
