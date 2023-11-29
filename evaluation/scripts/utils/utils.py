import pandas as pd
import os


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
            if not pd.isna(row['costs(USD)']):
                cost_sum += row['costs(USD)']

            if row['test_tool'] != 'terraform destroy':
                # Process non-destroy test tools
                test_cases_list.append(int(row['test_case']) if row['test_case'] != -1 else -1)
                if defect_category is None:
                    defect_category = row['defect_category']
                elif defect_category != row['defect_category']:
                    defect_category = -1  # Mark as -1 if defect categories differ

            if row['test_tool'] == 'terraform destroy':
                # End of sequence, create new entry
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



def write_latex_table(df, filename, plot_title, label_column_pairs):
    """
    Writes selected DataFrame data to a LaTeX table and creates a LaTeX boilerplate for a corresponding figure.

    :param df: Pandas DataFrame containing the data to be written.
    :param filename: Full path to the output file (without extension) and the base for the LaTeX label.
    :param plot_title: Title of the plot to use as the table caption and figure caption.
    :param label_column_pairs: List of tuples containing labels and corresponding DataFrame column keys.
    """
    # Generate LaTeX label by extracting basename and removing file extension
    label_name = os.path.splitext(os.path.basename(filename))[0]

    # Extract the column keys from the label-column pairs
    columns = [pair[1] for pair in label_column_pairs]

    # Modify labels to remove ', log scale' if present
    label_column_pairs = [(label.replace(', log scale', ''), col) for label, col in label_column_pairs]

    selected_data = df[columns]

    with open(filename + '.tex', 'w') as file:
        # Write the LaTeX code for the figure
        file.write(r"\begin{figure}[ht]" + "\n")
        file.write(r"  \centering" + "\n")
        file.write(fr"  \includegraphics[width=\textwidth]{{img/{label_name}.png}}" + "\n")
        file.write(fr"  \caption{{{plot_title}}}" + "\n")
        file.write(fr"  \label{{fig:{label_name}}}" + "\n")
        file.write(r"\end{figure}" + "\n")
        file.write("\n")

        # Write the LaTeX code for the table with additional indentation
        file.write(r"\begin{table}[h!]" + "\n")
        file.write(r"  \begin{tabular}{|" + " | ".join(["l"] * len(label_column_pairs)) + "|}" + "\n")
        file.write(r"    \hline" + "\n")
        file.write("    " + " & ".join([f"\\textbf{{{label}}}" for label, _ in label_column_pairs]) + r" \\" + "\n")
        file.write(r"    \hline" + "\n")
        for _, row in selected_data.iterrows():
            row_values = [f"{row[col]:.5f}".rstrip('0').rstrip('.') if isinstance(row[col], float) else row[col] for col in columns]
            file.write("    " + " & ".join(str(val) for val in row_values) + r" \\" + "\n")
            file.write(r"    \hline" + "\n")
        file.write(r"  \end{tabular}" + "\n")
        file.write(fr"  \caption{{{plot_title}}}" + "\n")
        file.write(fr"  \label{{tab:{label_name}}}" + "\n")
        file.write(r"\end{table}" + "\n")



    
def write_latex_summary_table(df, filename, plot_title, ylabel, legend_label, ykey, legend_key, series, suffixes=None):
    """
    Writes a LaTeX table for line diagram data, with a dynamic header and a joined cell 
    indicating the ylabel. Optionally supports multiple figures with specified suffixes.

    :param df: Pandas DataFrame containing the data to be summarized.
    :param filename: Full path to the output file (without extension) and the base for the LaTeX label.
    :param plot_title: Title of the plot to use as the table caption.
    :param ylabel: Label for the y-axis, typically including the unit.
    :param legend_label: Label for the legend, used as a header in the table.
    :param ykey: Column name in DataFrame that contains the values.
    :param legend_key: Column name in DataFrame that contains the legend.
    :param series: List of sorted series labels.
    :param suffixes: Optional list of tuples (suffix_label, suffix_title) for multiple figures.
    """
    label_name = os.path.splitext(os.path.basename(filename))[0]
    statistics = ['Mean', 'Median', 'Q1', 'Q3', 'IQR', 'Min', 'Max', 'Std Dev']

    with open(filename, 'w') as file:
        if suffixes:
            for suffix_label, suffix_title in suffixes:
                fig_label_name = f"{label_name}{suffix_label}"

                file.write(r"\begin{figure}[ht]" + "\n")
                file.write(r"  \centering" + "\n")
                file.write(fr"  \includegraphics[width=\textwidth]{{img/{fig_label_name}.png}}" + "\n")
                file.write(fr"  \caption{{{plot_title}{suffix_title}}}" + "\n")
                file.write(fr"  \label{{fig:{fig_label_name}}}" + "\n")
                file.write(r"\end{figure}" + "\n\n")
        else:
            # Original figure code for single figure
            file.write(r"\begin{figure}[ht]" + "\n")
            file.write(r"  \centering" + "\n")
            file.write(fr"  \includegraphics[width=\textwidth]{{img/{label_name}.png}}" + "\n")
            file.write(fr"  \caption{{{plot_title}}}" + "\n")
            file.write(fr"  \label{{fig:{label_name}}}" + "\n")
            file.write(r"\end{figure}" + "\n\n")

        # LaTeX code for the transposed summary table
        file.write(r"\begin{table}[h!]" + "\n")
        file.write(r"  \begin{tabular}{|l|" + "r|" * len(statistics) + "}" + "\n")
        file.write(r"    \hline" + "\n")
        file.write("    & \\multicolumn{" + str(len(statistics)) + "}{c|}{\\textbf{" + ylabel + "}} \\\\" + "\n")
        file.write(r"    \hline" + "\n")
        file.write("    \\textbf{" + legend_label + "} & " + " & ".join(stat for stat in statistics) + r" \\" + "\n")
        file.write(r"    \hline" + "\n")
        for s in series:
            row_values = [get_statistic(df[df[legend_key] == s], ykey, stat) for stat in statistics]
            file.write("    " + s + " & " + " & ".join(format_number(val) for val in row_values) + r" \\" + "\n")
            file.write(r"    \hline" + "\n")
        file.write(r"  \end{tabular}" + "\n")
        file.write(fr"  \caption{{{plot_title}}}" + "\n")
        file.write(fr"  \label{{tab:{label_name}}}" + "\n")
        file.write(r"\end{table}" + "\n")

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

def format_number(num):
    """
    Helper function to format a number by removing trailing decimal zeros.
    If no digits remain after the decimal point, the decimal point is also removed.

    :param num: The number to be formatted.
    :return: Formatted string representation of the number.
    """
    if isinstance(num, float):
        return f"{num:.2f}".rstrip('0').rstrip('.')
    return str(num)


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