# Thesis Workspace

## Overview

This repository serves as a supporting workspace for the proof-of-concept (PoC) implementation related to the Master Thesis titled "Quantitative Cost Assessment of IaC Testing".
While the actual PoC is encapsulated within a submodule, this repository contains the essential guides and tooling required to set up and run the PoC.

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