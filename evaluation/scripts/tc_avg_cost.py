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
ykey = 'costs(USD)'
xlabel = 'Test Case and Approach'
ylabel = 'Average Cost (USD)'
plot_title = 'Average Test Case Cost'
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
processed_data = flatten_multi_tc_apply_destroy_cycles(data, delete_originals=False)

# Filter out entries with NaN costs
filtered_data = processed_data[(processed_data['test_case'] != -1) & (processed_data['costs(USD)'].notna())]

# Calculating Average Costs
average_costs = filtered_data.groupby(['test_case', 'test_approach'])['costs(USD)'].mean().reset_index()

# Sorting the results first by 'test_approach' and then by 'test_case'
average_costs.sort_values(by=['test_approach', 'test_case'], inplace=True)

average_costs['label'] = average_costs.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)

# Output Preparation
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path = os.path.join(diagrams_dir, name + '.png')
write_latex_table(
    average_costs, 
    output_table_path, 
    plot_title, 
    label_column_pairs=[
        (xlabel, xkey),
        (ylabel, ykey)
    ])

# Plotting and Saving Results
plt.figure(figsize=(12, 6))
plt.bar(average_costs[xkey], average_costs[ykey], color='green', width=0.8)
plt.ylabel(ylabel)
plt.xlabel(xlabel)
plt.xticks(rotation=45, ha='right')
plt.title(plot_title)
plt.tight_layout()
plt.savefig(output_figure_path, dpi=300, bbox_inches='tight')
plt.show()
