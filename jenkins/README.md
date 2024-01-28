# Jenkins Test Pipeline

This document serves as an instructional guide for setting up and configuring a Jenkins test pipeline, tailored specifically for the execution of this project's tests.
Should you already possess an active Jenkins installation, the [Configuration](#configuration) section will be the sole area requiring your attention.

1. [Setup: Dockerized Jenkins](#setup-dockerized-jenkins)
   - 1.1 [Initialize Docker Network](#initialize-docker-network)
   - 1.2 [Run Jenkins Docker-in-Docker Container](#run-jenkins-docker-in-docker-container)
   - 1.3 [Build Custom Jenkins Image](#build-custom-jenkins-image)
   - 1.4 [Run Jenkins Container](#run-jenkins-container)
   - 1.5 [Initialization Steps](#initialization-steps)
   - 1.6 [Troubleshooting](#troubleshooting)
      - 1.6.1 [Plugin is Missing](#plugin-is-missing)
      - 1.6.2 [Add GitHub to Known Hosts](#add-github-to-known-hosts)
2. [Configuration](#configuration)
   - 2.1 [Add Credentials](#add-credentials)
      - 2.1.1 [AWS Credentials](#aws-credentials)
      - 2.1.2 [RDS Credentials](#rds-credentials)
      - 2.1.3 [Infracost Credentials](#infracost-credentials)
   - 2.2 [Create Pipeline](#create-pipeline)
3. [Manual Builds](#manual-builds)
4. [Automated Build Triggering](#automated-build-triggering)
   - 4.1 [Precautions and Usage](#precautions-and-usage)
   - 4.2 [Custom Docker Image Consideration](#custom-docker-image-consideration)


## Setup: Dockerized Jenkins

This section guides you through setting up a dockerized Jenkins instance, particularly useful if you haven't already installed Jenkins.

Our Jenkins pipeline employs Docker-in-Docker for agents, ensuring isolation and reproducibility. When using this setup alongside the DevContainer, run the Jenkins container parallel to the DevContainer to avoid nested Docker environments.

Additionally, ensure that the execution context for all operations is the project's root folder. For a detailed installation guide, refer to the [Jenkins Handbook](https://www.jenkins.io/doc/book/installing/docker/).

### Initialize Docker Network

Create a dedicated Docker network for Jenkins:

```bash
docker network create jenkins
```

### Run Jenkins Docker-in-Docker Container

Run a Jenkins Docker-in-Docker container with the following command:

```bash
docker run --name jenkins-docker --rm --detach --privileged --network jenkins --network-alias docker --env DOCKER_TLS_CERTDIR=/certs --volume jenkins-docker-certs:/certs/client --volume jenkins-data:/var/jenkins_home --publish 2376:2376 docker:dind --storage-driver overlay2
```

### Build Custom Jenkins Image

Build a custom Jenkins image tailored for this project:

```bash
docker build jenkins/ -f jenkins/DOCKERFILE -t myjenkins-blueocean:2.442
```

### Run Jenkins Container

Run the Jenkins container using your custom image:

```bash
docker run --name jenkins-blueocean --restart=on-failure --detach --network jenkins --env DOCKER_HOST=tcp://docker:2376 --env DOCKER_CERT_PATH=/certs/client --env DOCKER_TLS_VERIFY=1 --publish 8080:8080 --publish 50000:50000 --volume jenkins-data:/var/jenkins_home --volume jenkins-docker-certs:/certs/client:ro myjenkins-blueocean:2.442
```

### Initialization Steps

To initialize your Jenkins instance, execute the following commands:

```bash
docker exec jenkins-blueocean cat /var/jenkins_home/secrets/initialAdminPassword
```

Visit <http://localhost:8080> and input the initial password.
Install the suggested plugins.
Finally, log in using `admin` and the password you've retrieved.

### Troubleshooting

#### Plugin is Missing

During the initial setup of Jenkins, some users might encounter a `Dependency errors` message. This issue can occur under certain unclear conditions when accessing `Dashboard -> Manage Jenkins` for the first time.

In our experience, this message was specifically related to the plugin dependency `json-path-api (2.8.0-5.v07cb_a_1ca_738c)`. If you face this issue, it can be resolved by connecting to the Jenkins container and manually installing the required plugin. Follow these steps:

```bash
docker exec -it jenkins-blueocean bash
jenkins-plugin-cli --plugins json-path-api:2.8.0-5.v07cb_a_1ca_738c
exit
docker restart jenkins-blueocean
```

#### Add GitHub to Known Hosts

To avoid SSH errors when connecting to GitHub, execute the following steps:

```bash
docker exec -it jenkins-blueocean bash
ssh -T git@github.com
yes
exit
```

Ignore the `Permission denied (publickey)` reply, that is the expected result

## Configuration

Follow these steps to configure Jenkins for running the Jenkinsfile in this PoC. You'll need to add AWS and RDS credentials to Jenkins to ensure the Test Pipeline runs successfully.


### Add Credentials

Navigate to `Dashboard -> Manage Jenkins -> Security -> Credentials`.
Click on `Stores scoped to Jenkins -> System`.
Select `System -> Global credentials (unrestricted)`.

#### AWS Credentials

If you do not possess AWS credentials, please refer to the [Main Readme](/README.md#aws) for guidance on obtaining the necessary access keys.
Once you have acquired your credentials, proceed with the following steps to add them:

- Kind: `Username with password`
- Scope: `Global`
- Username: `<aws_access_key_id>`
- Password: `<aws_secret_access_key>`
- ID: `aws-terraform-credentials`
- Click `Create`

#### RDS Credentials

Add RDS credentials:

- Kind: `Username with password`
- Scope: `Global`
- Username: `rds_admin`
- Password: `super_secret_password` - or any password with at least 8 characters
- ID: `terraform-db-credentials`
- Click `Create`

#### Infracost Credentials

If you do not possess Infracost credentials, please refer to the [Main Readme](/README.md#infracost) for guidance on obtaining the necessary api key.
Once you have acquired your credentials, proceed with the following steps to add them:

- Kind: `Secret text`
- Scope: `Global`
- Secret: `<your infracost api key>`
- ID: `jenkins-infracost-api-key`
- Click `Create`

### Create Pipeline

To create a new pipeline, navigate to `Dashboard -> New Item`.
Enter a name for the new job (e.g., `thesis`), select `Pipeline`, and click `OK`.
Scroll to the `Pipeline` section:

- Choose `Pipeline script from SCM` from the `Definition` dropdown.
- SCM: `Git`
- Repository URL: `https://github.com/fex01/thesis-tf.git`
- Ignore field Credentials as the repo is public and does not require authentication.
- **Change** Branch Specifier to `*/main`, as new GitHub repositories use `main` instead of `master`.

Click `Save`.

This concludes the Jenkins setup and configuration guide for this project's test pipeline.
For further details on creating a pipeline, consult the [SCM Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/getting-started/#in-scm).

## Manual Builds

Manually triggering a build in Jenkins is straightforward:

1. **Initial Build**:
   - For the first build, navigate to `Dashboard -> <job name>` and click `Build Now`.
   - The first build is essential as it allows Jenkins to recognize the parameters specified in the Jenkinsfile.

2. **Triggering Builds with Parameters**:
   - Post the initial build, the `Build with Parameters` option will be available under `Dashboard -> <job name>`.
   - Here, you can set values for various parameters.

3. **Available Parameters**:
   - `dynamic_testing` (Boolean): Run dynamic tests. Default: `false`.
   - `nuke` (Boolean): Use only in test environments - highly destructive! Default: `false`.
   - `terraform_version` (String): Specifies the Terraform version. Default: `1.6.2`.
   - `infracost_version` (String): Sets the Infracost version. Default: `0.10.30`.
   - `tfsec_version` (String): Determines the tfsec version. Default: `1.28`.
   - `pytest_version` (String): Version of the databricksdocs/pytest image. Default: `0.3.4-rc.2`.
   - `terratest_version` (String): Terratest version to use. Default: `0.29.0`.
   - `cloud_nuke_version` (String): Version for cloud-nuke. Default: `0.32.0`.
   - `aws_cli_version` (String): AWS CLI version. Default: `2.13.32`.

4. **Monitor Build Progress**:
   - Go to `Dashboard -> <job name> -> Build History` to observe the build status.
   - Click on the build number for detailed information.

5. **Viewing the Console Log**:
   - For in-depth insights, access `Console Output` in the build's page.
   - This log provides detailed progression and diagnostic information.

6. **Build Overview**:
   - The `Dashboard -> <job name>` page displays an overview of all builds and their outcomes.

By setting parameters, you gain control over the build's behavior, ensuring it aligns with your specific requirements and scenarios.



## Automated Build Triggering

Builds can be manually initiated via the Jenkins Dashboard, which provides a user-friendly interface for pipeline management.
For automated and sequential build triggering, particularly in a test environment, this repository includes a custom script named [trigger_builds.sh](/jenkins/trigger_builds.sh).

Its primary function is to automate the triggering of multiple builds in sequence.
The script triggers `cloud-nuke`, a powerful tool that can **delete all resources across your AWS account**; hence, its use outside of a test environment is strongly discouraged.

### Precautions and Usage

Before running the script, ensure that it is safe to do so in your current environment. The script expects the Jenkins CLI `.jar` to be present in the same directory; if not found, it attempts to download it, ensuring that the necessary CLI tool is available for triggering the builds.

The `trigger_builds.sh` script supports the following options for customization:

- `--jenkins-url`: Specify the Jenkins server URL. Default is `http://localhost:8080/`.
- `--job-name`: Define the name of the Jenkins job to build. Default is `thesis`.
- `--num-builds`: Set the number of builds to trigger. Default is 10.
- `--username`: Provide the Jenkins username for authentication.
- `--token`: Supply the Jenkins API token or user password for authentication.

This automated process allows for the efficient execution of multiple test runs, each of which can be monitored and managed via the Jenkins Dashboard.

### Custom Docker Image Consideration

When using our custom Dockerfile for Jenkins, the `trigger_builds.sh` script comes pre-copied to the appropriate directory. This setup is part of our effort to streamline the testing process, providing a ready-to-use environment for executing the test pipeline.
