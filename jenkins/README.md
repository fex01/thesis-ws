# Jenkins Test Pipeline

This document serves as an instructional guide for setting up and configuring a Jenkins test pipeline, tailored specifically for the execution of this project's tests.
Should you already possess an active Jenkins installation, the [Configuration](#configuration) section will be the sole area requiring your attention.

## Setup: Dockerized Jenkins

The following section is only applicable if you have not yet installed Jenkins and wish to use a dockerized instance.
For a more comprehensive installation guide, consult the [Jenkins Handbook](https://www.jenkins.io/doc/book/installing/docker/).

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
docker build . -f jenkins/DOCKERFILE -t myjenkins-blueocean:2.427-1
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

If you do not possess AWS credentials, please refer to the [AWS README](/.aws/README.md) for guidance on obtaining the necessary access keys.
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

### Create Pipeline

To create a new pipeline, navigate to `Dashboard -> New Item`.
Enter a name (e.g., `thesis`), select `Pipeline`, and click `OK`.
Scroll to the `Pipeline` section:

- Choose `Pipeline script from SCM` from the `Definition` dropdown.
- SCM: `Git`
- Repository URL: `https://github.com/fex01/thesis-tf.git`
- **Change** Branch Specifier to `*/main`, as new GitHub repositories use `main` instead of `master`.

Click `Save`.

This concludes the Jenkins setup and configuration guide for this project's test pipeline.
For further details on creating a pipeline, consult the [SCM Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/getting-started/#in-scm).
