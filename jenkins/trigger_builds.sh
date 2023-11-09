#!/bin/bash

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Trigger builds on a Jenkins job with parameters dynamic_testing=true & nuke=true."
    echo "USE ONLY IN TEST ENV - NUKE DELETES ALL RESOURCES!"
    echo ""
    echo "Optional options:"
    echo "  --jenkins-url      Jenkins server URL. Default: http://localhost:8080/"
    echo "  --job-name         Name of the Jenkins job to build. Default: thesis"
    echo "  --num-builds       Number of builds to trigger. Default: 10"
    echo "  --username         Jenkins username for authentication."
    echo "  --token            Jenkins API token or user password for authentication."
    echo ""
}

# Initialize default values
JENKINS_URL="http://localhost:8080/"
JOB_NAME="thesis"
NUM_BUILDS=10
USERNAME=""
TOKEN=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help; exit 0 ;;
        --jenkins-url) JENKINS_URL="$2"; shift; shift ;;
        --job-name) JOB_NAME="$2"; shift; shift ;;
        --num-builds) NUM_BUILDS="$2"; shift; shift ;;
        --username) USERNAME="$2"; shift; shift ;;
        --token) TOKEN="$2"; shift; shift ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# Check if Jenkins CLI jar exists or download it
if [[ ! -f "jenkins-cli.jar" ]]; then
    echo "jenkins-cli.jar not found. Attempting to download from Jenkins server..."
    curl -fSL "${JENKINS_URL}jnlpJars/jenkins-cli.jar" -o "jenkins-cli.jar"
    if [[ $? -ne 0 ]]; then
        echo "Error downloading jenkins-cli.jar from Jenkins server."
        echo "   See ${JENKINS_URL}manage/cli/ for manual download"
        exit 1
    fi
fi

# Validate Jenkins URL is reachable
if ! curl --output /dev/null --silent --head --fail "$JENKINS_URL"; then
    echo "Error: Jenkins server ($JENKINS_URL) not reachable."
    exit 1
fi

# Validate that both or neither username and token are provided
if [[ -n "$USERNAME" && -z "$TOKEN" ]]; then
    echo "Error: A token is required when a username is provided." \
         "Please provide both credentials or none if your Jenkins" \
         "server allows anonymous access."
    exit 1
elif [[ -z "$USERNAME" && -n "$TOKEN" ]]; then
    echo "Error: A username is required when a token is provided." \
         "Please provide both credentials or none if your Jenkins" \
         "server allows anonymous access."
    exit 1
fi

# Authentication command part
AUTH_CMD_PART=""
if [[ -n "$USERNAME" ]] && [[ -n "$TOKEN" ]]; then
    AUTH_CMD_PART="--username $USERNAME --password $TOKEN"
fi

# Validate the job exists on Jenkins server
if ! java -jar jenkins-cli.jar -s "$JENKINS_URL" $AUTH_CMD_PART list-jobs | grep -q "^$JOB_NAME$"; then
    echo "Error: Job name ($JOB_NAME) does not exist on Jenkins server ($JENKINS_URL)."
    exit 1
fi

# Validate NUM_BUILDS is a positive integer
if ! [[ "$NUM_BUILDS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Number of builds must be a positive integer."
    exit 1
fi

for ((i=1; i<=NUM_BUILDS; i++))
do
    echo "Starting build $i/$NUM_BUILDS of $JOB_NAME with parameters dynamic_testing=true, nuke=true"
    
    # Trigger the build with parameters and wait for its completion
    java -jar jenkins-cli.jar -s "$JENKINS_URL" $AUTH_CMD_PART build "$JOB_NAME" -s -w -p dynamic_testing=true -p nuke=true
    
    if [[ $? -ne 0 ]]; then
        echo "Error occurred during the triggering of build $i."
        exit 1
    fi

    echo "Build $i completed."
done

echo "All builds completed successfully."
