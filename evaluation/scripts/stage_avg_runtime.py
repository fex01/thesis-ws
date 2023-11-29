# Import Statements
from doctest import debug
from matplotlib import pyplot as plt
import pandas as pd
import sys
import os

# Custom utility functions
from utils.utils import *

# Argument Parsing
# Check if an argument is provided and use it if available
data_path = '../../measurements/merged_measurements_3.csv'
if len(sys.argv) == 2:
    data_path = sys.argv[1]

# Variable Definition
xkey = 'tool_approach'
ykey = 'runtime(seconds)'
xlabel = 'Test Tool and Approach'
ylabel = 'Average Runtime (seconds, log scale)'
plot_title = 'Average Test Stage Runtime'
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
processed_data = flatten_multi_tc_apply_destroy_cycles(data)
# Get overall stage runtimes: group by 'build', 'test_tool', and 'test_approach' and sum the runtimes
summed_runtimes = processed_data.groupby(['build', 'test_tool', 'test_approach'])['runtime(seconds)'].sum().reset_index()
# Get average stage runtimes: group by 'test_tool' and 'test_approach' and calculate the average of these sums
average_runtimes = summed_runtimes.groupby(['test_tool', 'test_approach'])['runtime(seconds)'].mean().reset_index()
# Sort by 'test_approach' and then by 'test_tool'
average_runtimes.sort_values(by=['test_approach', 'test_tool'], inplace=True)
# Create a combined label for test tool and test approach
average_runtimes['tool_approach'] = average_runtimes['test_tool'] + " (TA" + average_runtimes['test_approach'].astype(str) + ")"

# Output Preparation
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path = os.path.join(diagrams_dir, name + '.png')
write_latex_table(
    average_runtimes, 
    output_table_path, 
    plot_title, 
    label_column_pairs=[
        (xlabel, xkey),
        (ylabel, ykey)
    ])

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
