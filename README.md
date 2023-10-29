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

- AWS Credentials: See [AWS Readme](./.aws/README.md) for configuring AWS credentials.
- Devcontainer Configuration: Refer to `./.devcontainer/devcontainer.json` for information on installed tools and how to individualize your setup.

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

The `cloud-nuke` exemption configuration file, located at [terraform/cloud-nuke.yaml](https://github.com/fex01/thesis-tf/blob/main/cloud-nuke.yaml), is instrumental for safeguarding essential resources during both automated pipeline cleanup and manual `cloud-nuke` executions. Specifically, the account credentials used for deployment should be included in this exemption list. In our particular setup, these credentials are associated with an account named `admin`. If your deployment uses a different account name, it is imperative to update this configuration file accordingly to prevent unintentional deletions.

Whether you are running the "Nuke" stage in the test pipeline or executing `cloud-nuke` manually, this exemption configuration ensures a more secure cleanup process, minimizing the risk of accidental resource removal.
