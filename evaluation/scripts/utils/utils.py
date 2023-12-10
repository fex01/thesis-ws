import pandas as pd
import os
import subprocess

# Constants for script for cost calculation and cost breakdown file paths
CALCULATE_COSTS_SCRIPT_PATH = '../../terraform/scripts/calculate_costs.py'
COST_BREAKDOWN_FILE_PATH = '../../measurements/infracost_build_1.json'


def read_csv_to_dataframe(data_path):
    """
    Reads a CSV file into a pandas DataFrame with specified data types for each column.

    :param data_path: The path to the CSV file to be read.
    :return: A pandas DataFrame containing the parsed data.
    """
    # Define column data types
    column_types = {
        'build': int,
        'defect_category': float, # parse NA as NaN
        'test_case':  float, # parse NA as NaN
        'test_approach': int,
        'test_tool': str,
        'runtime(seconds)': float,
        'costs(USD)': float,
        'revision': str,
        'build_start': int,
        'build_duration(hh:mm:ss)': str
    }

    try:
        # Read the CSV file with specified data types
        df = pd.read_csv(data_path, dtype=column_types)

        # Convert 'defect_category' and 'test_case' to int, replacing NaNs with a placeholder (e.g., -1)
        df['defect_category'] = df['defect_category'].fillna(-1).astype(int)
        df['test_case'] = df['test_case'].fillna(-1).astype(int)

        return df
    except Exception as e:
        print(f"Error while reading the file: {e}")
        return None
    


def without_incomplete_data_sets(original_data, test_case_value=14):
    """
    Filters out data sets from the DataFrame that do not contain a specified test_case value.
    By default, it filters out data sets that do not contain test_case=14.

    :param original_data: The original pandas DataFrame with time series data.
    :param test_case_value: The test_case value to filter data sets by (default is 14).
    :return: A pandas DataFrame containing only the data sets with the specified test_case value.
    """
    # Convert 'test_case' column to numeric for proper filtering
    original_data['test_case'] = pd.to_numeric(original_data['test_case'], errors='coerce')

    # Identify unique 'build' values where 'test_case' matches the specified value
    builds_with_test_case = original_data[original_data['test_case'] == test_case_value]['build'].unique()

    # Filter the DataFrame to include only rows where 'build' is in the identified list
    filtered_data = original_data[original_data['build'].isin(builds_with_test_case)]

    # Reset index to maintain continuity
    filtered_data.reset_index(drop=True, inplace=True)

    return filtered_data



def flatten_multi_tc_apply_destroy_cycles(original_data, delete_originals=True):
    """
    Flattens test cases between 'terraform apply' and 'terraform destroy' stages by summarizing runtimes and costs.
    This function iterates through the DataFrame, summarizing runtimes and costs between the 'terraform apply'
    and 'terraform destroy' entries. It aggregates test cases and handles varying defect categories within 
    a build, marking 'NA' if categories differ. The resulting DataFrame represents each apply-destroy cycle as a single entry.
    
    :param original_data: The original pandas DataFrame with time series data.
    :param delete_originals: Boolean indicating whether to delete the original entries after aggregation.
    :return: A pandas DataFrame with aggregated apply-destroy cycle data.
    """
    # Create a copy of the input DataFrame
    data = original_data.copy()

    # Initialize variables
    in_sequence = False
    runtime_sum = 0
    cost_sum = 0
    start_build = None
    test_cases_list = []
    defect_category = None
    revision = None
    build_start = None
    build_duration = None
    start_index = None

    for index, row in data.iterrows():
        if row['test_tool'] == 'terraform apply':
            # Start a new sequence
            in_sequence = True
            start_build = row['build']
            start_index = index
            runtime_sum = row['runtime(seconds)']
            revision = row['revision']
            build_start = row['build_start']
            build_duration = row['build_duration(hh:mm:ss)']
            continue

        if in_sequence and row['build'] == start_build:
            # Accumulate data for the sequence
            runtime_sum += row['runtime(seconds)']

            if row['test_tool'] != 'terraform destroy':
                # Process non-destroy test tools
                test_cases_list.append(int(row['test_case']) if row['test_case'] != -1 else -1)
                if defect_category is None:
                    defect_category = row['defect_category']
                elif defect_category != row['defect_category']:
                    defect_category = -1  # Mark as -1 if defect categories differ

            if row['test_tool'] == 'terraform destroy':
                # End of sequence, call external script for cost calculation
                subprocess_result = subprocess.run(
                    [
                        'python3', CALCULATE_COSTS_SCRIPT_PATH, 
                        '--infracost-json', COST_BREAKDOWN_FILE_PATH, 
                        '--runtime', str(int(runtime_sum)),
                        '--split-by', '1'
                    ],
                    capture_output=True, text=True
                )
                cost_sum = round(float(subprocess_result.stdout.strip()), 5)
                test_cases_list.sort()
                sorted_test_cases = int(''.join(map(str, test_cases_list)))
                new_entry = {
                    'build': start_build,
                    'defect_category': defect_category,
                    'test_case': sorted_test_cases,
                    'test_approach': 5,
                    'test_tool': 'terraform test',
                    'runtime(seconds)': runtime_sum,
                    'costs(USD)': cost_sum,
                    'revision': revision,
                    'build_start': build_start,
                    'build_duration(hh:mm:ss)': build_duration
                }

                if delete_originals:
                    # Replace the 'terraform apply' entry with the new entry
                    data.loc[start_index] = pd.Series(new_entry)
                    # Delete subsequent entries in the sequence
                    data.drop(data.loc[start_index + 1:index].index, inplace=True)
                else:
                    # Create a new DataFrame for the new entry
                    new_entry_df = pd.DataFrame([new_entry])
                    # Concatenate the new DataFrame to the main DataFrame
                    data = pd.concat([data.iloc[:index + 1], new_entry_df, data.iloc[index + 1:]]).reset_index(drop=True)

                # Reset variables for next sequence
                in_sequence = False
                runtime_sum = 0
                cost_sum = 0
                test_cases_list = []
                defect_category = None
                revision = None
                build_start = None
                build_duration = None
                start_index = None

    # Reset index to maintain continuity
    data.reset_index(drop=True, inplace=True)

    return data


def filter_data_sets_by_build(original_data, min_build_value=None, max_build_value=None):
    """
    Filters data sets in the DataFrame to include only those within a specified range of 'build' values.
    Either min_build_value or max_build_value must be provided.

    :param original_data: The original pandas DataFrame with time series data.
    :param min_build_value: Optional; the minimum 'build' value to include in the filter.
    :param max_build_value: Optional; the maximum 'build' value to include in the filter.
    :return: A pandas DataFrame containing only the data sets within the specified 'build' range.
    """

    # Create a copy of the DataFrame to avoid SettingWithCopyWarning
    data_copy = original_data.copy()

    # Convert 'build' column to numeric for proper filtering
    data_copy['build'] = pd.to_numeric(data_copy['build'], errors='coerce')

    # Applying filter based on the provided values
    if min_build_value is not None and max_build_value is not None:
        filtered_data = data_copy[(data_copy['build'] > min_build_value) & 
                                  (data_copy['build'] <= max_build_value)]
    elif min_build_value is not None:
        filtered_data = data_copy[data_copy['build'] > min_build_value]
    elif max_build_value is not None:
        filtered_data = data_copy[data_copy['build'] <= max_build_value]
    else:
        raise ValueError("At least one of min_build_value or max_build_value must be provided")

    return filtered_data



def format_test_case_label(test_case, test_approach):
    """
    Formats and returns a string label for a test case and test approach.

    This function takes numerical values for a test case and test approach, and returns a formatted string label.
    The test case number is formatted such that if it has more than two digits, commas are inserted between each digit.
    The test approach is prepended with 'TA' and the test case number is prepended with 'TC'.

    :param test_case: An integer or a float representing the test case number. 
                      If a float is provided, it is converted to an integer.
    :param test_approach: An integer or a float representing the test approach number. 
                          If a float is provided, it is converted to an integer.
    :return: A formatted string label representing the test case and test approach.
             For example, for test_case=123 and test_approach=4, it returns "TC1,2,3 (TA4)".
    """
    test_case_str = str(int(test_case))
    if len(test_case_str) > 2:
        test_case_str = ','.join(test_case_str)
    return f"TC{test_case_str} (TA{int(test_approach)})"

def short_test_case_label(test_case):
    """
    Returns a string label for a test case.

    This function takes a numerical value for a test case and returns a formatted string label.
    If the test case number has more than two digits, commas are inserted between each digit.
    The test case number is prepended with 'TC'.

    :param test_case: An integer or a float representing the test case number. 
                      If a float is provided, it is converted to an integer.
    :return: A formatted string label representing the test case.
             For example, for test_case=123, it returns "TC1,2,3".
             For test_case=12, it returns "TC12".
    """
    test_case_str = str(int(test_case))
    if len(test_case_str) > 2:
        test_case_str = ','.join(test_case_str)
    return f"TC{test_case_str}"

def format_deploy_phase_label(test_tool):
    """
    Formats and returns a string label for a deploy phase.

    This function takes a string with the Terraform command and returns the matching phase name.

    :param test_tool: A string representing the deploy phase.
    :return: A formatted string label representing the deploy phase.
             For example, for test_tool='terraform apply', it returns "deploy".
    """
    return 'deploy' if test_tool == 'terraform apply' else 'destroy' if test_tool == 'terraform destroy' else None



def write_latex(caption, label, data=None, header_key_pairs=None, summary_table=False,
                output_file='../output.tex', digits=2):
    """
    Function to create LaTeX tables and figure boilerplate.
    
    :param caption: The title for the table or figure.
    :param label: The LaTeX label for referencing. For figures also used as the file name.
    :param header_key_pairs: List of tuples for header and key mapping in the table.
    :param data: DataFrame for the table. If None, a figure is generated.
    :param summary_table: Boolean indicating whether to generate a summary table with statistics.
    :param output_file: The file path for the output LaTeX file.
    :param digits: Optional; Number of digits to round floating-point numbers to (default is 2).
    """
    if data is not None:
        if summary_table:
            latex = generate_summary_table(data, header_key_pairs, caption, label, digits)
        else:
            latex = generate_table(data, header_key_pairs, caption, label, digits)

    if data is None:
        latex = generate_figure(label, caption)
    
    append_to_file(
        output_file=output_file,
        content=latex,
        label=label
    )



def generate_table(data, header_key_pairs, caption, label, digits=2):
    """
    Generates LaTeX code for a standard table.

    :param data: Pandas DataFrame containing the data to be summarized.
    :param header_key_pairs: List of tuples (human-readable label, DataFrame column key).
    :param caption: Title of the table to use as the caption.
    :param label: LaTeX label for referencing the table.
    :param digits: Number of digits to round floating-point numbers to (default is 2).
    """
    # Process header_key_pairs to remove ', log scale' from headers
    processed_header_key_pairs = []
    for header, key in header_key_pairs:
        cleaned_header = header.replace(', log scale', '', 1)
        cleaned_header = cleaned_header.replace(', Log Scale', '', 1)
        processed_header_key_pairs.append((cleaned_header, key))
    columns = [pair[1] for pair in processed_header_key_pairs]
    selected_data = data[columns]

    table_latex = r"\begin{table}[h!]" + "\n"
    table_latex += r"  \begin{tabular}{|" + " | ".join(["l"] * len(processed_header_key_pairs)) + "|}" + "\n"
    table_latex += r"    \hline" + "\n"
    table_latex += "    " + " & ".join([f"\\textbf{{{label}}}" for label, _ in processed_header_key_pairs]) + r" \\" + "\n"
    table_latex += r"    \hline" + "\n"
    for _, row in selected_data.iterrows():
        # Format each cell value using format_table_numbers
        row_values = [format_table_numbers(row[col], digits) for col in columns]
        table_latex += "    " + " & ".join(row_values) + r" \\" + "\n"
        table_latex += r"    \hline" + "\n"
    table_latex += r"  \end{tabular}" + "\n"
    table_latex += fr"  \caption{{{caption}}}" + "\n"
    table_latex += fr"  \label{{tab:{label}}}" + "\n"
    table_latex += r"\end{table}" + "\n"

    return table_latex


def generate_summary_table(data, header_key_pairs, caption, label, digits=2):
    """
    Generates LaTeX code for a summary table with statistics.

    :param data: Pandas DataFrame containing the data to be summarized.
    :param header_key_pairs: List of tuples (human-readable label, DataFrame column key).
    :param caption: Title of the table to use as the caption.
    :param label: LaTeX label for referencing the table.
    :param digits: Number of digits to round floating-point numbers to (default is 2).
    """
    if len(header_key_pairs) != 2:
        raise ValueError("header_key_pairs must contain exactly two pairs.")

    # Unpacking the pairs
    legend_label, legend_key = header_key_pairs[0]
    ylabel, ykey = header_key_pairs[1]
    row_headers = data[legend_key].unique()
    statistics = ['Mean', 'Median', 'Q1', 'Q3', 'IQR', 'Min', 'Max', 'Std Dev']


    # Checking if resizebox is needed
    resizebox = digits >= 5

    table_latex = r"\begin{table}[h!]" + "\n"
    if resizebox: table_latex += r"  \resizebox{\textwidth}{!}{" + "\n"
    table_latex += r"  \begin{tabular}{|l|" + "r|" * len(statistics) + "}" + "\n"
    table_latex += r"    \hline" + "\n"
    table_latex += "    & \\multicolumn{" + str(len(statistics)) + "}{c|}{\\textbf{" + ylabel + "}} \\\\" + "\n"
    table_latex += r"    \hline" + "\n"
    table_latex += "    \\textbf{" + legend_label + "} & " + " & ".join(stat for stat in statistics) + r" \\" + "\n"
    table_latex += r"    \hline" + "\n"
    for s in row_headers:
        subset = data[data[legend_key] == s]
        row_values = [get_statistic(subset, ykey, stat) for stat in statistics]
        formatted_values = [format_table_numbers(val, digits) for val in row_values]
        table_latex += "    " + s + " & " + " & ".join(formatted_values) + r" \\" + "\n"
        table_latex += r"    \hline" + "\n"
    table_latex += r"  \end{tabular}" + "\n"
    if resizebox: table_latex += r"  }" + "\n"
    table_latex += fr"  \caption{{{caption}}}" + "\n"
    table_latex += fr"  \label{{tab:{label}}}" + "\n"
    table_latex += r"\end{table}" + "\n"

    return table_latex



def get_statistic(df, col, stat_type):
    """
    Helper function to calculate a statistic for a given DataFrame column.

    :param df: Pandas DataFrame.
    :param col: Column name for which to calculate the statistic.
    :param stat_type: Type of statistic to calculate ('Mean', 'Median', 'Min', 'Max', 'Std Dev').
    :return: Calculated statistic value.
    """
    if stat_type == 'Mean':
        return df[col].mean()
    elif stat_type == 'Median':
        return df[col].median()
    elif stat_type == 'Q1':
        return df[col].quantile(0.25)
    elif stat_type == 'Q3':
        return df[col].quantile(0.75)
    elif stat_type == 'IQR':
        return df[col].quantile(0.75) - df[col].quantile(0.25)
    elif stat_type == 'Min':
        return df[col].min()
    elif stat_type == 'Max':
        return df[col].max()
    elif stat_type == 'Std Dev':
        return df[col].std()
    else:
        return None

def format_table_numbers(num, digits=2):
    """
    Formats a number by rounding it to a specified number of digits, appending trailing zeros if necessary.
    If the input cannot be cast to a float, returns 'NaN'.

    :param num: The number to be formatted. Can be a float, int, or string.
    :param digits: Number of digits to round the number to (default is 2).
    :return: Formatted string representation of the number or 'NaN' if casting fails.
    """
    try:
        float_num = float(num)
        format_str = f"{{:.{digits}f}}"
        return format_str.format(float_num)
    except ValueError:
        return num



def generate_figure(label, caption):
    """
    Generates LaTeX code for a figure.
    """
    figure_latex = r"\begin{figure}[h!]" + "\n"
    figure_latex += r"  \centering" + "\n"
    figure_latex += fr"  \includegraphics[width=\textwidth]{{img/{label}.png}}" + "\n"
    figure_latex += fr"  \caption{{{caption}}}" + "\n"
    figure_latex += fr"  \label{{fig:{label}}}" + "\n"
    figure_latex += r"\end{figure}" + "\n"

    return figure_latex


def append_to_file(output_file, label, content):
    """
    Appends or replaces content in a LaTeX file based on a specific label substring.

    :param output_file: Path to the LaTeX file.
    :param label: The unique substring of the label of the table or figure to append or replace.
    :param content: The LaTeX code to append or replace in the file.
    """
    try:
        with open(output_file, 'r+') as file:
            existing_content = file.read()

            # Determine whether it's a table or figure
            if r'\begin{table}' in content:
                start_tag = r'\begin{table}'
                end_tag = r'\end{table}'
            elif r'\begin{figure}' in content:
                start_tag = r'\begin{figure}'
                end_tag = r'\end{figure}'
            else:
                file.write(content)
                return

            # Search for the label within the section
            section_start = existing_content.find(start_tag)
            while section_start != -1:
                section_end = existing_content.find(end_tag, section_start) + len(end_tag)
                section_content = existing_content[section_start:section_end]

                if label in section_content:
                    # Replace existing content
                    new_content = existing_content[:section_start] + content + existing_content[section_end:]
                    break

                section_start = existing_content.find(start_tag, section_end)

            else:
                # Append new content if no match was found
                new_content = existing_content + '\n' + content

            # Write updated content
            file.seek(0)
            file.write(new_content)
            file.truncate()

    except FileNotFoundError:
        # Create file if it doesn't exist
        with open(output_file, 'w') as file:
            file.write(content)
