# Quantitative Cost Assessment of IaC Testing: PoC Workspace

## Overview

This repository serves as a supporting workspace for the proof-of-concept (PoC) implementation related to the Master Thesis titled "Quantitative Cost Assessment of IaC Testing".
While the actual PoC is encapsulated within a submodule, this repository contains the essential guides and tooling required to set up and run the PoC.

This separation is done to facilitate streamlined testing, as the test pipeline can directly check out only the executable code - see [Submodule thesis-tf](#submodule-thesis-tf) for more information.

## Devcontainer

The inclusion of a devcontainer definition in this repository serves as an optional, yet standardized, development environment primarily intended for the research and development phases of this project. Visitors interested in hands-on exploration of the proof of concept (PoC) may utilize this environment to bypass manual setup procedures. Those primarily concerned with the test pipeline may proceed directly to the [Test Pipeline](#test-pipeline) section.

Supported by platforms such as [VS Code](https://code.visualstudio.com/docs/devcontainers/containers) and [GitHub Codespaces](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers), devcontainers encapsulate required tools and libraries, simplifying the setup process.

To use the devcontainer, first clone this repository along with its submodule using the following command:

```bash
git clone --recurse-submodules https://github.com/fex01/thesis-ws.git
```

Next, follow the steps below to set up and run the devcontainer locally with VS Code.

### Devcontainer Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) or a compatible Docker alternative
- [VS Code](https://code.visualstudio.com)
- [VS Code Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

For more details, consult the [VS Code Guide](https://code.visualstudio.com/docs/devcontainers/tutorial).

### Devcontainer Configuration

#### Credentials Configuration

- **AWS Credentials**: You have two options for configuring AWS credentials within the DevContainer:
  1. **.env File**: Create a `.env` file based on the [.env_template](/.env_template) available in the project root directory. Populate `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with your actual AWS credentials.
  2. **AWS Host Configuration Integration**: You can also use the host machine's AWS configuration by following the instructions under [AWS Host Configuration Integration](#aws-host-configuration-integration).

- **InfraCost Credentials**: To configure InfraCost, create a `.env` file based on the [.env_template](/.env_template)  available in the project root directory. Populate `INFRACOST_API_KEY` with your actual InfraCost API key.

#### Devcontainer Configuration Details

Refer to `./.devcontainer/devcontainer.json` for information on installed tools and how to individualize your setup.

### Running the Devcontainer

1. Verify that Docker is running: `docker --version`
2. Open the `thesis-ws` repository in VS Code.
3. Use the Command Palette (F1) and select `Dev Containers: Reopen in Container`.
4. The initial container build might take up to 15 minutes. Subsequent launches with an existing container will open within seconds.

Now you are all set to explore the PoC within the devcontainer.

## Test Pipeline

The submodule includes a `Jenkinsfile` defining the test pipeline.
This pipeline can be executed on your own Jenkins installation or through our provided dockerized Jenkins setup.
In either case, certain prerequisites like credentials and job configurations are necessary.
For a comprehensive guide on these prerequisites and on setting up a dockerized Jenkins installation, please consult [Jenkins Setup](./jenkins/README.md).

## Submodule thesis-tf

The submodule is an independent repository that houses the core elements of the PoC.
It includes the IaC configuration written in Terraform, a Jenkinsfile for defining the test pipeline, and the actual test implementations.
This separation allows for streamlined testing, as the test pipeline can directly check out only the executable code.

For more information on the specifics of the submodule, please refer to its [README](./terraform/README.md).

## Cleanup

During the course of extended testing or in the event of partial failures of `terraform destroy`, there may be residual AWS resources that are not properly removed. To address this, we have employed the use of [cloud-nuke](https://github.com/gruntwork-io/cloud-nuke) throughout the implementation phase. 

The `cloud-nuke` tool is incorporated in our [devcontainer](#devcontainer) and can be utilized as follows:

- `cloud-nuke aws`: This command will attempt to remove all AWS resources. Exercise caution while using this command, especially in production environments. It is imperative to be fully aware of the ramifications of this action.
  - `--config terraform/cloud-nuke.yaml`: Utilizing this flag will incorporate the exemption rules as explained in the [Cloud-Nuke Exemption Configuration](#cloud-nuke-exemption-configuration) subsection. This safeguards essential resources like the manually-created initial IAM user and any preexisting AWS roles from unintended deletion.
  - `--force`: This flag enables non-interactive execution, bypassing the confirmation dialog.
  - `AWS_PROFILE=thesis cloud-nuke aws`: To specify a particular AWS profile, precede the `cloud-nuke` command with the `AWS_PROFILE` variable set to the desired profile name.

Note that usage of `cloud-nuke` is a powerful action that should be taken with full understanding and caution.

### Additional Cleanup Feature: The "Nuke" Stage in Test Pipeline

In addition to manual invocation, our test pipeline includes a dedicated stage named "nuke" that is designed to automate the cleanup process. If `cloud-nuke` is installed on the Jenkins server, this stage will execute `cloud-nuke` using the AWS credentials provided. You have the option to enable or disable this stage by setting the pipeline parameter `use_cloud_nuke`.

If you are utilizing our custom Dockerfile for Jenkins, then `cloud-nuke` comes preinstalled on the Jenkins server, enabling immediate use of this feature.

### Cloud-Nuke Exemption Configuration

The `cloud-nuke` exemption configuration file, located at [terraform/cloud-nuke.yaml](/terraform/cloud-nuke.yaml), is instrumental for safeguarding essential resources during both automated pipeline cleanup and manual `cloud-nuke` executions. Specifically, the account credentials used for deployment should be included in this exemption list. In our particular setup, these credentials are associated with an account named `admin`. If your deployment uses a different account name, it is imperative to update this configuration file accordingly to prevent unintentional deletions.

Whether you are running the "Nuke" stage in the test pipeline or executing `cloud-nuke` manually, this exemption configuration ensures a more secure cleanup process, minimizing the risk of accidental resource removal.


## Account Creation

### AWS

If you do not currently have an AWS account, the following is a concise outline for setting up an initial account and user, distilled from AWS's more comprehensive [Getting Started Guide](https://aws.amazon.com/getting-started/guides/setup-environment/).

1. **Initial Setup**: Create an AWS account, which automatically establishes a [root user](https://docs.aws.amazon.com/signin/latest/userguide/account-root-user-type.html).

    - **Security Measures**: It is advisable to enable Multi-Factor Authentication (MFA) for the root user immediately for basic security. Navigate to `IAM -> Add MFA`.

2. **IAM User Creation**: For operational tasks, avoid using the root user. Instead, create a secondary IAM user with administrative privileges.

    - Navigate to `IAM -> Users -> Create user` and proceed to attach the `AdministratorAccess` policy.

3. **API Credentials**: Subsequent to user creation, generate the necessary API credentials.

    - Click on the username and select `Create access key`. Note that although temporary credentials are recommended for heightened security, permanent credentials are deemed sufficient for the purpose of this guide. Ensure that you store the `Access key` and `Secret access key` in a secure location.

4. **Local CLI Configuration**: Lastly, configure your local AWS CLI via the `aws configure` command. You will be prompted to enter the `Access key ID` and `Secret access key` generated earlier, as well as your preferred AWS region (e.g., `eu-west-3`). This action will create `~/.aws/credentials` and `~/.aws/config` files, completing the setup.

#### AWS Host Configuration Integration

Should you prefer to use your host machine's AWS configuration, the `.devcontainer/devcontainer.json` file can be modified to achieve this. Under the `mounts` section, amend the corresponding AWS entry as illustrated below:

```json
{
  ...
  // Configure mounts from host to container.
  "mounts": [
    ...
    // To use the host's AWS configuration, uncomment the following line:
    // "source=${localEnv:HOME}/.aws,target=/home/vscode/.aws,type=bind"
  ]
}
```

### Infracost

TODO