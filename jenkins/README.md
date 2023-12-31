# Jenkins Test Pipeline

This document serves as an instructional guide for setting up and configuring a Jenkins test pipeline, tailored specifically for the execution of this project's tests.
Should you already possess an active Jenkins installation, the [Configuration](#configuration) section will be the sole area requiring your attention.

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
docker build jenkins/ -f jenkins/DOCKERFILE -t myjenkins-blueocean:2.427-1
```

### Run Jenkins Container

Run the Jenkins container using your custom image:

```bash
docker run --name jenkins-blueocean --restart=on-failure --detach --network jenkins --env DOCKER_HOST=tcp://docker:2376 --env DOCKER_CERT_PATH=/certs/client --env DOCKER_TLS_VERIFY=1 --publish 8080:8080 --publish 50000:50000 --volume jenkins-data:/var/jenkins_home --volume jenkins-docker-certs:/certs/client:ro myjenkins-blueocean:2.427-1
```

### Initialization Steps

To initialize your Jenkins instance, execute the following commands:

```bash
docker exec jenkins-blueocean cat /var/jenkins_home/secrets/initialAdminPassword
```

Visit <http://localhost:8080> and input the initial password.
Install the suggested plugins.
Finally, log in using `admin` and the password you've retrieved.

### Add GitHub to Known Hosts

To avoid SSH errors when connecting to GitHub, execute the following steps:

```bash
docker exec -it jenkins-blueocean bash
ssh -T git@github.com
yes
exit
```

## Configuration

The subsequent steps outline the necessary configurations required to execute the Jenkinsfile associated with this Proof of Concept (PoC).
These configurations are essential for the successful orchestration of the test pipeline and include adding AWS and RDS credentials to Jenkins.

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
Enter a name (e.g., `thesis`), select `Pipeline`, and click `OK`.
Scroll to the `Pipeline` section:

- Choose `Pipeline script from SCM` from the `Definition` dropdown.
- SCM: `Git`
- Repository URL: `https://github.com/fex01/thesis-tf.git`
- Ignore field Credentials as the repo is public and does not require authentication.
- **Change** Branch Specifier to `*/main`, as new GitHub repositories use `main` instead of `master`.

Click `Save`.

This concludes the Jenkins setup and configuration guide for this project's test pipeline.
For further details on creating a pipeline, consult the [SCM Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/getting-started/#in-scm).

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
