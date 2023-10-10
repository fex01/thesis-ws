# AWS CLI Configuration

Choose either a custom configuration for the container or use the host configuration.

If you do not have AWS credentials yet, reopen the project in the container and follow the instructions in section [Account Creation Quick and Dirty](#account-creation-quick-and-dirty).

## Custom Configuration

Use this folder to store custom credentials and configuration for the DevContainer. Folder is mounted to `~/.aws` in the container.
The content of this folder is ignored by git and will **only** stay on your local machine.

## Host Configuration

Adapt `.devcontainer/devcontainer.json` to mount the host AWS config.

Scroll down to section `mounts` and adapt the aws entry (see comment):

```json
// For format details, see https://aka.ms/devcontainer.json. For config options, see the
// README at: https://github.com/devcontainers/templates/tree/main/src/debian
{
  ...
 // Configure mounts from host to container.
 "mounts": [
  // host SSH key so you can connect to Git repos
  "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind",
  // AWS Config and Credentials so you can connect to AWS
  //   use "source=${localEnv:HOME}/.aws,target=/home/vscode/.aws,type=bind" for host aws config
  "source=${localWorkspaceFolder}/.aws,target=/home/vscode/.aws,type=bind"
 ]
}
```

## Account Creation Quick and Dirty

If you do not have an AWS account yet, you can create one quick and dirty:

- [Getting Started](https://aws.amazon.com/getting-started/guides/setup-environment/)
  - created account -> creates [root user](https://docs.aws.amazon.com/signin/latest/userguide/account-root-user-type.html)
    - enable MFA as basic security measure for root account: IAM -> Add MFA
  - we will not use the root user for automation, as such we go on to manually create the initial IAM user:
    - IAM -> Users -> Create user
      - Choose name -> Next
      - Attach policies directly -> AdministratorAccess -> Next
      - Create user
    - create API credentials
      - click user name -> Create access key
      - appreciate that we should use temporary credentials but that we **ignore that for a quick and dirty solution**
      - Other -> Next
      - Description: `quick-and-dirty` -> Create access key
      - save `Access key` and `Secret access key` securely
  - configure CLI credentials locally: `aws configure`
    - enter `Access key ID` and `Secret access key` from above
    - enter prefered region (e.g. `eu-central-1`)
    - skip output format
    - will create `~/.aws/credentials` and `~/.aws/config` files
