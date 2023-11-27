# Import Statements
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Custom utility functions
from utils.utils import *

# Argument Parsing
data_path = '../../measurements/merged_measurements_3.csv'
if len(sys.argv) == 2:
    data_path = sys.argv[1]

# Variable Definition
xkey = 'label'
ykey = 'runtime(seconds)'
xlabel = 'Test Case and Approach'
ylabel = 'Average Runtime (seconds, log scale)'
plot_title = 'Average Test Case Runtime'
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
processed_data = flatten_multi_tc_apply_destroy_cycles(data)
filtered_data = processed_data[(processed_data['test_case'] != -1)]

# Calculating Average Runtimes
average_runtimes = filtered_data.groupby(['test_case', 'test_approach'])['runtime(seconds)'].mean().reset_index()

# Sorting the results first by 'test_approach' and then by 'test_case'
average_runtimes.sort_values(by=['test_approach', 'test_case'], inplace=True)

# Formatting Test Case Labels
def format_test_case_label(test_case, test_approach):
    test_case_str = str(int(test_case))
    if len(test_case_str) > 2:
        test_case_str = ','.join(test_case_str)
    return f"TC{test_case_str} (TA{int(test_approach)})"

average_runtimes['label'] = average_runtimes.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)

# Output Preparation
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path = os.path.join(diagrams_dir, name + '.png')
write_latex_table_from_plot(average_runtimes, output_table_path, plot_title, xlabel, ylabel, columns=[xkey, ykey])

# Plotting and Saving Results
plt.figure(figsize=(12, 6))
plt.bar(average_runtimes[xkey], average_runtimes[ykey], color='blue', width=0.8)
plt.ylabel(ylabel)
plt.xlabel(xlabel)
plt.xticks(rotation=45, ha='right')
plt.title(plot_title)
plt.yscale('log')
plt.tight_layout()
plt.savefig(output_figure_path, dpi=300, bbox_inches='tight')
plt.show()

