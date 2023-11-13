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
  echo "  --valid-entries    Optional: When set, only CSV files with the expected number of entries will be collected."
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
VALIDE_NUMBER_OF_ENTRIES=""

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
        --valid-entries)
            VALID_NUMBER_OF_ENTRIES="$2"
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
if [[ -n "$FROM_BUILD" && -n "$TO_BUILD" && "$FROM_BUILD" -gt "$TO_BUILD" ]]; then
    echo "Error: FROM_BUILD ($FROM_BUILD) should be less or euqal to TO_BUILD ($TO_BUILD)."
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

# Function to convert timestamp to date-time-group
convert_timestamp_to_datetimegroup() {
    local ts=$1
    local os_name=$(uname)

    # Check OS and apply appropriate date command
    if [[ "$os_name" == "Linux" ]]; then
        # GNU date (Linux)
        date -d @"$((ts / 1000))" +"%Y%m%d%H%M%S"
    elif [[ "$os_name" == "Darwin" ]]; then
        # BSD date (macOS)
        date -r $((ts / 1000)) +"%Y%m%d%H%M%S"
    else
        echo "Timestamp conversion failed, returning original timestamp. Reason:"
        echo "   Unsupported OS: $os_name. Supported OSs are Linux and Darwin (macOS)."
        return $ts
    fi
}

# This function converts a time duration from milliseconds to a formatted string in hours, minutes, and seconds.
# Usage: convert_milliseconds_to_hours_minutes_seconds <milliseconds>
convert_milliseconds_to_hours_minutes_seconds() {
    local milliseconds="$1"
    # Convert milliseconds to seconds by dividing by 1000
    # Add 500 before division to round to the nearest second
    local total_seconds=$(((milliseconds + 500) / 1000))
    # Calculate the number of hours by dividing the total seconds by 3600 (seconds in an hour)
    local hours=$((total_seconds / 3600))
    # Calculate the number of minutes by first finding the remaining seconds after removing hours,
    # then dividing by 60 (seconds in a minute)
    local minutes=$(((total_seconds % 3600) / 60))
    # Calculate the remaining seconds by finding the remainder of total seconds after removing hours and minutes
    local seconds=$((total_seconds % 60))

    # Print the formatted time in hh:mm:ss format, padding each unit with zeros if necessary
    printf "%02d:%02d:%02d\n" "$hours" "$minutes" "$seconds"
}

# Function: validate_data
# Description: Processes a multiline string, line by line.
#              - Skips lines not starting with the specified build number.
#              - Corrects test case numeration for older data.
#              - Skips lines with zero runtime unless the test tool is 'terraform fmt'.
# Parameters: 
#   1. input_data - Multiline string to process.
#   2. current_build_number - The build number to filter the data by.
# Returns: 
#   A multiline string with the processed data.
validate_data() {
    local input_data="$1"
    local current_build_number="$2"
    local processed_data=""

    # Read each line from the input data
    while IFS= read -r line; do
        # Remove carriage returns and newlines
        line=$(echo "$line" | tr -d '\r\n')

        # Skip lines not starting with the current build number
        if ! [[ "$line" =~ ^$current_build_number, ]]; then
            continue  # Skip to next iteration
        fi

        # Correcting test case numeration for older data
        line=$(echo "$line" | sed 's/,1,1,5,/,1,3,5,/g')
        line=$(echo "$line" | sed 's/,1,2,5,/,1,4,5,/g')
        line=$(echo "$line" | sed 's/,2,1,4,terra/,2,5,4,terra/g')
        line=$(echo "$line" | sed 's/,2,2,4,pytest/,2,6,4,pytest/g')
        line=$(echo "$line" | sed 's/,2,1,5,/,2,7,5,/g')
        line=$(echo "$line" | sed 's/,3,1,4,pytest/,3,8,4,pytest/g')
        line=$(echo "$line" | sed 's/,3,1,5,/,3,9,5,/g')
        line=$(echo "$line" | sed 's/,4,1,4,pytest/,4,10,4,pytest/g')
        line=$(echo "$line" | sed 's/,5,1,5,/,5,11,5,/g')
        line=$(echo "$line" | sed 's/,6,1,4,pytest/,6,13,4,pytest/g')

        # If runtime (field 6) is zero, it's likely a corrupted measurement and will be reported. 
        # Exception: test tool 'terraform fmt', which can have a legitimate zero runtime (rounded down).
        local field_5=$(echo "$line" | cut -d',' -f5)
        local field_6=$(echo "$line" | cut -d',' -f6)
        if [[ ! "$field_5" =~ fmt$ ]] && [[ "$field_6" == "0" ]]; then
            continue  # Skip corrupted measurement
        fi

        # Append the processed line to the result
        processed_data+="$line"$'\n'
    done <<< "$input_data"

    # Return the processed data
    echo "$processed_data"
}

merge_csv_files() {
    local dir="$1"
    local csv_file="$2"
    local output_file_base="${3%.*}"
    local output_file_ext="${3##*.}"
    local output_file="${output_file_base}.${output_file_ext}"
    local current_header=""
    local file_content=""
    local file_path="$dir/archive/$csv_file"
    local current_build_number=$(basename "$dir")
    local revision=""
    local build_start=""
    local build_duration=""
    local build_success=""

    # Check if the output_file contains a line starting with the current build number
    file_matched=false
    files=($output_file_base*.$output_file_ext)
    # Check if the pattern matches any files
    if [ ${#files[@]} -gt 0 ] && [ -f "${files[0]}" ]; then
        # Loop through each file that matches the pattern
        for file in "${files[@]}"; do
            # Use grep to check if the build number is in the file
            if grep -q "^$current_build_number," "$file"; then
                file_matched=true
                break  # Stop the loop if we found the build number
            fi
        done
    fi
    # If the build number was found in any of the files, skip processing this build
    if $file_matched; then
        echo "Build number $current_build_number has already been merged. Skipping..."
        return
    fi

    # Get file content and header
    if [[ "$RUN_LOCALLY" = true ]]; then
        build_success=$(grep -m 1 -o "<result>[A-Z]*</result>" "$dir/build.xml" \
            | awk -F'[<>]' '/<result>/ {print $3}')
        # Validate the build result
        if [[ "$build_success" != "SUCCESS" ]]; then
            echo "Build number $current_build_number has result $build_success. Skipping..."
            return
        fi
        if [[ ! -f "$file_path" ]]; then
            echo "\"$csv_file\" not found for build $current_build_number."
            csv_files=$(ls "$dir/archive/"*.csv 2>/dev/null)
            if [ -z "$csv_files" ]; then
                echo "No csv files found for build $current_build_number."
            else
                echo -n "Available CSV files for build $current_build_number: "
                # Print file names in the same line
                echo "$csv_files" | xargs -n 1 basename | tr '\n' ' '
                echo  # Add a newline for formatting
            fi
            return
        fi
        current_header=$(head -n 1 "$file_path" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        file_content=$(tail -n +2 "$file_path")
        revision=$(grep -m 1 -o "<sha1>[a-z0-9]*</sha1>" "$dir/build.xml" \
            | awk -F'[<>]' '/<sha1>/ {print substr($3, 1, 7)}')
        build_start=$(convert_timestamp_to_datetimegroup \
            $(grep -m 1 -o "<startTime>[0-9]*</startTime>" "$dir/build.xml" \
            | awk -F'[<>]' '/<startTime>/ {print $3}'))
        build_duration=$(convert_milliseconds_to_hours_minutes_seconds \
            $(grep -m 1 -o "<duration>[0-9]*</duration>" "$dir/build.xml" \
            | awk -F'[<>]' '/<duration>/ {print $3}'))
    else
        build_success=$(docker exec "$CONTAINER_NAME" bash -c \
            "grep -m 1 -o '<result>[A-Z]*</result>' \"$dir/build.xml\"" \
            | awk -F'[<>]' '/<result>/ {print $3}')
        # Validate the build result
        if [[ "$build_success" != "SUCCESS" ]]; then
            echo "Build number $current_build_number has result $build_success. Skipping..."
            return
        fi
        current_header=$(docker exec "$CONTAINER_NAME" bash -c \
          "if [[ -f $file_path ]]; then \
              head -n 1 $file_path; \
          else \
              echo 'File not found'; \
          fi" \
          | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ "$current_header" == "File not found" ]]; then
            echo "\"$csv_file\" not found for build $current_build_number."
            csv_files=$(docker exec "$CONTAINER_NAME" bash -c "ls \"$dir/archive/\"*.csv" 2>/dev/null)
            if [ -z "$csv_files" ]; then
                echo "No csv files found for build $current_build_number."
            else
                echo -n "Available CSV files for build $current_build_number: "
                # Print file names in the same line
                echo "$csv_files" | xargs -n 1 basename | tr '\n' ' '
                echo  # Add a newline for formatting
            fi
            return
        fi
        file_content=$(docker exec "$CONTAINER_NAME" bash -c "tail -n +2 $file_path")
        revision=$(docker exec "$CONTAINER_NAME" bash -c \
            "grep -m 1 -o '<sha1>[a-z0-9]*</sha1>' \"$dir/build.xml\"" \
            | awk -F'[<>]' '/<sha1>/ {print substr($3, 1, 7)}')
        build_start=$(convert_timestamp_to_datetimegroup \
            $(docker exec "$CONTAINER_NAME" bash -c \
                "grep -m 1 -o '<startTime>[0-9]*</startTime>' \"$dir/build.xml\"" \
            | awk -F'[<>]' '/<startTime>/ {print $3}'))
        build_duration=$(convert_milliseconds_to_hours_minutes_seconds \
            $(docker exec "$CONTAINER_NAME" bash -c \
                "grep -m 1 -o '<duration>[0-9]*</duration>' \"$dir/build.xml\"" \
            | awk -F'[<>]' '/<duration>/ {print $3}'))
    fi

    # Validate the number of entries, if VALID_NUMBER_OF_ENTRIES is set
    if [[ -n "$VALID_NUMBER_OF_ENTRIES" ]]; then
        entry_count=$(grep -c '^' <<<"$file_content")
        if [[ "$entry_count" -ne $VALID_NUMBER_OF_ENTRIES ]]; then
            echo "Build number $current_build_number has $entry_count entries, expected $VALID_NUMBER_OF_ENTRIES. Skipping..."
            return
        fi
    fi

    # Older measurement files contain the '$' character, which can cause issues when processing
    # the data due to its special character status in many contexts. To avoid these problems,
    # we replace '$' with 'USD'.
    current_header=$(echo "$current_header" | sed 's/\$/USD/g')

    # Add revision, build_start and build_duration to the file header
    current_header="$current_header,revision,build_start,build_duration(hh:mm:ss)"

    # Handle changing CSV headers
    matched_file=""
    for f in "$output_file_base"_*."$output_file_ext" "$output_file"; do
        if [[ -f "$f" && $f =~ _([0-9]{1,3})\.$output_file_ext$ ]]; then
            local file_header=$(head -n 1 "$f")
            if [[ "$current_header" == "$file_header" ]]; then
                matched_file="$f"
                break
            fi
        fi
    done

    if [[ -n "$matched_file" ]]; then
        # merge file content into output file with matching header
        output_file="$matched_file"
    elif [[ -f "$output_file" || -f  "$output_file_base"_1."$output_file_ext" ]]; then
        local output_header=$(head -n 1 "$output_file")
        if [[ "$current_header" != "$output_header" ]]; then
            # Find the highest existing number
            local max_num=0
            for f in "$output_file_base"_*."$output_file_ext"; do
                if [[ $f =~ _([0-9]+)\.${output_file_ext}$ ]]; then
                    [[ "${BASH_REMATCH[1]}" -gt "$max_num" ]] && \
                        max_num="${BASH_REMATCH[1]}"
                fi
            done

            # Increment the number for the new file
            local new_num=$((max_num + 1))

            # Rename existing output_file if it's the first duplicate
            if [[ $max_num -eq 0 ]]; then
                mv "$output_file" "${output_file_base}_1.${output_file_ext}"
                new_num=2  # Set new_num to 2 as we now have a _1 file
            fi

            # Create a new file with incremented number
            output_file="${output_file_base}_${new_num}.${output_file_ext}"
            echo "Header changed. Creating new file: $output_file"
            echo "$current_header" > "$output_file"
        fi
    else
        # First file to be created
        echo "$current_header" > "$output_file"
    fi

    echo "Merge build $current_build_number into $output_file"

    file_content=$(validate_data "$file_content" "$current_build_number")

    # Append file content with additional build information
    while IFS= read -r line; do
        line=$(echo "$line" | tr -d '\r\n')  # Remove carriage returns and newlines
        echo "$line,$revision,$build_start,$build_duration" >> "$output_file"
    done <<< "$file_content"
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
