import pandas as pd
import os


def flatten_multi_tc_apply_destroy_cycles(original_data):
    """
    Flattens test cases between 'terraform apply' and 'terraform destroy' stages by summarizing runtimes and costs.

    This function iterates through the DataFrame, summarizing runtimes and costs between the 'terraform apply'
    and 'terraform destroy' entries. It aggregates test cases and handles varying defect categories within 
    a build, marking 'NA' if categories differ. The resulting DataFrame represents each apply-destroy cycle as a single entry.
    
    :param original_data: The original pandas DataFrame with time series data.
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
    indices_to_delete = []

    for index, row in data.iterrows():
        if row['test_tool'] == 'terraform apply':
            # Start a new sequence
            in_sequence = True
            start_index = index
            start_build = row['build']
            runtime_sum = row['runtime(seconds)']
            revision = row['revision']
            build_start = row['build_start']
            build_duration = row['build_duration(hh:mm:ss)']
            continue

        if in_sequence and row['build'] == start_build:
            # Accumulate data for the sequence
            indices_to_delete.append(index)
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
                data.loc[start_index] = pd.Series(new_entry)
                # Reset variables for next sequence
                in_sequence = False
                runtime_sum = 0
                cost_sum = 0
                test_cases_list = []
                defect_category = None
                revision = None
                build_start = None
                build_duration = None

    # Delete rows that are part of sequences and have been aggregated
    data.drop(indices_to_delete, inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data



def write_latex_table_from_plot(df, filename, plot_title, xlabel, ylabel, columns):
    """
    Writes selected DataFrame data to a LaTeX table, rounding float values to five decimal places.

    :param df: Pandas DataFrame containing the data to be written.
    :param filename: Full path to the output file (without extension) and the base for the LaTeX label.
    :param plot_title: Title of the plot to use as the table caption.
    :param xlabel: Label for the x-axis to use as the first column header.
    :param ylabel: Label for the y-axis to use as the second column header.
    :param columns: List of column keys from the DataFrame to include in the table.
    """
    # Strip ', log scale' from ylabel if it exists
    ylabel = ylabel.replace(', log scale', '')

    # Generate LaTeX label by extracting basename and removing file extension
    label_name = os.path.splitext(os.path.basename(filename))[0]

    selected_data = df[columns]

    with open(filename, 'w') as file:
        file.write(r"\begin{table}[h!]" + "\n")
        file.write(r"\begin{tabular}{|" + " | ".join(["l"] * len(columns)) + "|}" + "\n")
        file.write(r"\hline" + "\n")
        file.write(" & ".join([f"\\textbf{{{col}}}" for col in [xlabel, ylabel]]) + r" \\" + "\n")
        file.write(r"\hline" + "\n")
        for _, row in selected_data.iterrows():
            row_values = [f"{row[col]:.5f}".rstrip('0').rstrip('.') if isinstance(row[col], float) else row[col] for col in columns]
            file.write(" & ".join(str(val) for val in row_values) + r" \\" + "\n")
            file.write(r"\hline" + "\n")
        file.write(r"\end{tabular}" + "\n")
        file.write(fr"\caption{{{plot_title}}}" + "\n")
        file.write(fr"\label{{tab:{label_name}}}" + "\n")
        file.write(r"\end{table}" + "\n")



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
