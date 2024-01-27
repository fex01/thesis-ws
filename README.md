# Quantitative Cost Assessment of IaC Testing: PoC Workspace

This repository serves as a supporting workspace for the proof-of-concept (PoC) implementation related to the Master Thesis titled "Quantitative Cost Assessment of IaC Testing".
While the actual PoC is encapsulated within a submodule, this repository contains the essential guides and tooling required to set up and run the PoC.

This separation is done to facilitate streamlined testing, as the test pipeline can directly check out only the executable code - see [Submodule thesis-tf](#submodule-thesis-tf) for more information.

## Table of Contents

- [Devcontainer](#devcontainer): Optional setup for a standardized development environment supporting the PoC.
  - [Devcontainer Prerequisites](#devcontainer-prerequisites)
  - [Devcontainer Configuration](#devcontainer-configuration)
  - [Running the Devcontainer](#running-the-devcontainer)
- [Test Pipeline](#test-pipeline): Instructions for executing the test pipeline with the provided Jenkinsfile.
- [Submodule thesis-tf](#submodule-thesis-tf): The core elements of the PoC including Terraform configuration, Jenkinsfile, and test implementations.
- [Data Collection](#data-collection): The approach for collecting test metrics and cost data within the test pipeline.
  - [Test Execution and Data Capture](#test-execution-and-data-capture)
  - [Metrics Collection](#metrics-collection)
  - [Artifacts and Reports](#artifacts-and-reports)
  - [Data Aggregation, Analysis, and Transparency](#data-aggregation-analysis-and-transparency)
- [Cleanup](#cleanup): Guidelines for using `cloud-nuke` to clean up AWS resources post-testing.
  - [Additional Cleanup Feature: The "Nuke" Stage in Test Pipeline](#additional-cleanup-feature-the-nuke-stage-in-test-pipeline)
  - [Cloud-Nuke Exemption Configuration](#cloud-nuke-exemption-configuration)
- [Account Creation](#account-creation): Steps for setting up necessary accounts for using the PoC.
  - [AWS](#aws): Creating an AWS account and user.
  - [Infracost](#infracost): Acquiring an Infracost API key.

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

## Data Collection

The data collection process for the "Quantitative Cost Assessment of IaC Testing" PoC is methodically embedded within the test pipeline. Each execution of the pipeline is designed to capture detailed metrics regarding test runtimes and associated costs.

### Test Execution and Data Capture

The pipeline is configured to execute tests individually or in groups, gathering data for each run. Individual test executions are performed using:

```groovy
// /terraform/Jenkinsfile
...
steps {
    sh """scripts/run_test.sh \\
        --build-number ${BUILD_NUMBER} \\
        --defect-category ${DEFECT_CATEGORY} \\
        --test-approach ${TEST_APPROACH} \\
        --test-command '${TEST_COMMAND}' \\
        --csv-file ${CSV_FILE}"""
}
...
```

For grouped tests, the following command is used:

```groovy
// /terraform/Jenkinsfile
...
steps {
    sh """scripts/run_grouped_tests.sh \\
        --build-number ${BUILD_NUMBER} \\
        --test-folder ${TEST_FOLDER} \\
        --test-tool '${TEST_TOOL}' \\
        --test-command '${TEST_COMMAND}' \\
        --csv-file ${CSV_FILE}"""
}
...
```

Each build within the test pipeline generates a new Infracost breakdown report for the resources scheduled for deployment. Subsequently, the costs for each test are calculated and added to measured data:

```groovy
// /terraform/Jenkinsfile
...
steps {
    sh """scripts/extend_measurements_with_costs.py \\
        --infracost-json ${INFRACOST_JSON} \\
        --measurements-csv ${CSV_FILE}"""
}
...
```

This process ensures that the resulting dataset includes not only the performance metrics of the tests but also a financial dimension, reflecting the cost implications of the deployed infrastructure.

All scripts related to the test runs are located in the [`/terraform/scripts/`](/terraform/scripts/) directory within the repository.

### Metrics Collection

The collected metrics for each test include the build number, defect category, test case, test approach, test tool, and runtime in seconds. Furthermore, the cost associated with each test is calculated and appended to the data. This calculation accounts for the billing modalities of different resources and is based on the test runtime and an Infracost breakdown of resource prices. The cost calculation script can be found at [calculate_costs.py](/terraform/scripts/calculate_costs.py).

### Artifacts and Reports

The CSV file containing the measurements, along with the corresponding Infracost breakdown report, is saved as an artifact for each test pipeline build. These artifacts are retrievable via the Jenkins Job Portal, allowing for in-depth analysis of the collected data.

### Data Aggregation, Analysis, and Transparency

To assist with the aggregation and analysis of data across multiple builds, a [helper script](/measurements/collect_data.sh) is available. This script is designed to collect and merge data, which can be executed on the local Jenkins server or from the Docker host when employing our [dockerized Jenkins setup](/jenkins/README.md#setup-dockerized-jenkins). 

The repository includes the raw data that is the foundation of the analysis presented in the thesis.
In addition, the specific [Infracost breakdown report](/measurements/infracost_build_1.json) used to calculate the costs for these measurements is also provided.
This [dataset](/measurements/merged_measurements.csv) is openly shared to promote transparency and to enable peer validation of our research findings.
The availability of the raw data along with the cost calculations ensures full traceability, allowing others to understand and verify the data-driven conclusions that support our thesis.

By making this information publicly accessible, we underscore our commitment to an exhaustive and transparent approach to data collection, bolstering the reliability and reproducibility of our work on the costs associated with IaC testing.

## Cleanup

During the course of extended testing or in the event of partial failures of `terraform destroy`, there may be residual AWS resources that are not properly removed. To address this, we have employed the use of [cloud-nuke](https://github.com/gruntwork-io/cloud-nuke) throughout the implementation phase. 

The `cloud-nuke` tool is incorporated in our [devcontainer](#devcontainer) and can be utilized as follows:

- `cloud-nuke aws`: This command will attempt to remove all AWS resources. Exercise caution while using this command, especially in production environments. It is imperative to be fully aware of the ramifications of this action.
  - `--config terraform/cloud-nuke.yaml`: Utilizing this flag will incorporate the exemption rules as explained in the [Cloud-Nuke Exemption Configuration](#cloud-nuke-exemption-configuration) subsection. This safeguards essential resources like the manually-created initial IAM user and any preexisting AWS roles from unintended deletion.
  - `--force`: This flag enables non-interactive execution, bypassing the confirmation dialog.
  - `AWS_PROFILE=thesis cloud-nuke aws`: To specify a particular AWS profile, precede the `cloud-nuke` command with the `AWS_PROFILE` variable set to the desired profile name.

Note that usage of `cloud-nuke` is a powerful action that should be taken with full understanding and caution.

### Additional Cleanup Feature: The "Nuke" Stage in Test Pipeline

In addition to manual invocation, our test pipeline includes a dedicated `post` action that is designed to automate the cleanup process. You have the option to enable or disable this step by setting the pipeline parameter `nuke` (default: `false`). 

When enabled, this stage will run `cloud-nuke` with the exemption configuration file located at [terraform/cloud-nuke.yaml](/terraform/cloud-nuke.yaml).

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

Infracost, the chosen cost estimation tool for our test pipeline, requires an API key for operation. This key is necessary both for the [DevContainer](#credentials-configuration) and within the [test pipeline](/jenkins/README.md#infracost-credentials).

### Acquiring an Infracost API Key

To obtain your Infracost API key, follow these steps:

1. **Via CLI**: Typically, you can use the command `infracost auth login` to get an API key. However, if this method is unsuccessful, proceed to the next step.
2. **Sign Up Online**: Register at [Infracost Dashboard](https://dashboard.infracost.io).
3. **Retrieve API Key**: Once signed up, navigate to Org Settings on the dashboard to find your API key.

For more detailed information on Infracost and its setup, refer to the [Infracost Quick-Start Guide](https://www.infracost.io/docs/#quick-start).
