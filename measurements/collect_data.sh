#!/bin/bash

show_help() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Merge CSV files from build directories."
  echo ""
  echo "Optional options:"
  echo "  --path             Base path to build directories. Default: /var/jenkins_home/jobs/thesis/builds/"
  echo "  --from-build       Starting build number."
  echo "  --to-build         Ending build number."
  echo "  --csv-file         Name of the CSV file to merge. Default: measurements.csv"
  echo "  --container-name   Name of the Docker container to use. Default: jenkins-blueocean"
  echo "  --run-locally      If set, script runs locally instead of connecting to dockerized Jenkins."
  echo "  --output-file      Name of the merged output CSV file. Default: merged_measurements.csv"
  echo "  --get-breakdown    If set, retrieves the breakdown file from the first build directory."
  echo "  --breakdown-file   Name of the breakdown file to retrieve. Setting this automatically turns on --get-breakdown. Default: infracost.json"
  echo ""
}

# Define defaults
BUILDS_PATH="/var/jenkins_home/jobs/thesis/builds"
FROM_BUILD=""
TO_BUILD=""
CSV_FILE="measurements.csv"
OUTPUT_FILE="merged_measurements.csv"
CONTAINER_NAME="jenkins-blueocean"
RUN_LOCALLY=false
BREAKDOWN_FILE="infracost.json"
GET_BREAKDOWN=false

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        --path)
            BUILDS_PATH="$2"
            shift 2
            ;;
        --from-build)
            FROM_BUILD="$2"
            shift 2
            ;;
        --to-build)
            TO_BUILD="$2"
            shift 2
            ;;
        --csv-file)
            CSV_FILE="$2"
            shift 2
            ;;
        --output-file) 
            OUTPUT_FILE="$2"; 
            shift 2
            ;;
        --container-name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --run-locally)
            RUN_LOCALLY=true
            shift
            ;;
        --get-breakdown)
            GET_BREAKDOWN=true
            shift
            ;;
        --breakdown-file)
            BREAKDOWN_FILE="$2"
            GET_BREAKDOWN=true
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get directories from the path excluding the base directory
if [[ "$RUN_LOCALLY" = true ]]; then
    dirs=($(find "$BUILDS_PATH" -maxdepth 1 -mindepth 1 -type d | sort -n))
else
    if [[ -z "$CONTAINER_NAME" ]]; then
        echo "Error: Container name must be provided if not running locally."
        exit 1
    fi
    dirs=($(docker exec "$CONTAINER_NAME" bash -c "find $BUILDS_PATH -maxdepth 1 -mindepth 1 -type d" | sort -n))
fi

dirs=($(printf '%s\n' "${dirs[@]##*/}" | sort -n))

# Ensure FROM_BUILD and TO_BUILD are numbers if they are not empty
if [[ -n "$FROM_BUILD" && ! "$FROM_BUILD" =~ ^[0-9]+$ ]]; then
    echo "Error: FROM_BUILD ($FROM_BUILD) is not a valid number."
    exit 1
fi

if [[ -n "$TO_BUILD" && ! "$TO_BUILD" =~ ^[0-9]+$ ]]; then
    echo "Error: TO_BUILD ($TO_BUILD) is not a valid number."
    exit 1
fi

# Ensure FROM_BUILD < TO_BUILD if both are set
if [[ -n "$FROM_BUILD" && -n "$TO_BUILD" && "$FROM_BUILD" -ge "$TO_BUILD" ]]; then
    echo "Error: FROM_BUILD ($FROM_BUILD) should be less than TO_BUILD ($TO_BUILD)."
    exit 1
fi

# Ensure FROM_BUILD and TO_BUILD are in the range of directories
if [[ -n "$FROM_BUILD" && ! " ${dirs[@]} " =~ " $FROM_BUILD " ]]; then
    echo "Error: Invalid FROM_BUILD value ($FROM_BUILD). Smallest build number in dirs: ${dirs[0]}"
    exit 1
fi

if [[ -n "$TO_BUILD" && ! " ${dirs[@]} " =~ " $TO_BUILD " ]]; then
    echo "Error: Invalid TO_BUILD value ($TO_BUILD). Highest build number in dirs: ${dirs[-1]}"
    exit 1
fi

# Calculate range
[[ -n "$FROM_BUILD" ]] && dirs=($(printf "%s\n" "${dirs[@]}" | awk -v fb="$FROM_BUILD" '$1 >= fb'))
[[ -n "$TO_BUILD" ]] && dirs=($(printf "%s\n" "${dirs[@]}" | awk -v tb="$TO_BUILD" '$1 <= tb'))

if [[ "${#dirs[@]}" -eq 0 ]]; then
    echo "No directories found to process."
    exit 1
fi

merge_csv_files() {
    local dir="$1"
    local csv_file="$2"
    local output_file="$3"
    local current_header=""
    local output_header=""
    local file_content=""
    local file_path="$dir/archive/$csv_file"

    # Check if running locally or within a Docker container
    if [[ "$RUN_LOCALLY" = true ]]; then
        if [[ ! -f "$file_path" ]]; then
            echo "File not found: $file_path"
            return
        fi
        current_header=$(head -n 1 "$file_path" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        file_content=$(tail -n +2 "$file_path")
    else
        if [[ -z "$CONTAINER_NAME" ]]; then
            echo "Error: Container name must be provided if not running locally."
            exit 1
        fi

        current_header=$(docker exec "$CONTAINER_NAME" bash -c \
          "if [[ -f $file_path ]]; then \
              head -n 1 $file_path; \
          else \
              echo 'File not found'; \
          fi" \
          | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ "$current_header" == "File not found" ]]; then
            echo "File not found: $file_path in Docker container"
            return
        fi
        file_content=$(docker exec "$CONTAINER_NAME" bash -c "tail -n +2 $file_path")
    fi

    # Checking output file and merging logic
    if [[ ! -f "$output_file" ]]; then
        echo "$current_header" > "$output_file"
    else
        output_header=$(head -n 1 "$output_file")
        if [[ "$current_header" != "$output_header" ]]; then
            echo "Error: Mismatch in CSV headers between $output_file and $file_path"
            exit 1
        fi
    fi

    # Extract the current build number
    current_build_number=$(basename "$dir")

    # Check if the output_file contains a line starting with the current build number
    if grep -q "^$current_build_number," "$output_file"; then
        echo "Build number $current_build_number has already been merged. Skipping..."
        return
    fi

    echo "$file_content" >> "$output_file"
}

# Get and rename the BREAKDOWN_FILE if --get-breakdown is set
if [[ "$GET_BREAKDOWN" = true ]]; then
    # Assuming breakdown file is in the first build directory
    first_build_dir="${dirs[0]}"
    original_path="$BUILDS_PATH/$first_build_dir/archive/$BREAKDOWN_FILE"
    file_ending="${BREAKDOWN_FILE##*.}" # Extracts file extension
    renamed_file="${BREAKDOWN_FILE%.*}_build_$first_build_dir.$file_ending"
    
    if [[ "$RUN_LOCALLY" = true ]]; then
        if [[ ! -f "$original_path" ]]; then
            echo "Breakdown file not found: $original_path"
        else
            cp "$original_path" "$renamed_file"
        fi
    else
        # Check if the file exists inside the container first.
        if docker exec "$CONTAINER_NAME" bash -c "[[ -f $original_path ]]"; then
            # Copy the file from the container to the host system.
            docker cp "$CONTAINER_NAME:$original_path" "$renamed_file"
        else
            echo 'Breakdown file not found in Docker container'
        fi
    fi
fi

# Merge CSVs
for dir in "${dirs[@]}"; do
    merge_csv_files "$BUILDS_PATH/$dir" "$CSV_FILE" "$OUTPUT_FILE"
done

echo "CSV files merged into $OUTPUT_FILE"
