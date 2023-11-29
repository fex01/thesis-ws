# Import Statements
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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
runtime_key = 'runtime(seconds)'
costs_key = 'costs(USD)'
xlabel = 'Test Case and Approach'
ylabel_runtime = 'Average Runtime (seconds)'
ylabel_costs = 'Average Costs (USD)'
plot_title = 'Average Runtime and Costs per Dynamic Test Case'
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
processed_data = flatten_multi_tc_apply_destroy_cycles(data, delete_originals=False)

# Filter out entries with NaN values for runtime or costs
filtered_data = processed_data[(processed_data['test_case'] != -1) & 
                               (processed_data['runtime(seconds)'].notna()) & 
                               (processed_data['costs(USD)'].notna())]

# Calculating Averages
average_runtime_costs = filtered_data.groupby(['test_case', 'test_approach']).agg({runtime_key: 'mean', costs_key: 'mean'}).reset_index()

# Sorting the results first by 'test_approach' and then by 'test_case'
average_runtime_costs.sort_values(by=['test_approach', 'test_case'], inplace=True)

# Adding labels for the x-axis
average_runtime_costs['label'] = average_runtime_costs.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)

# Output Preparation
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path = os.path.join(diagrams_dir, name + '.png')
write_latex_table(
    average_runtime_costs, 
    output_table_path, 
    plot_title, 
    label_column_pairs=[
        (xlabel, xkey),
        (ylabel_runtime, runtime_key),
        (ylabel_costs, costs_key)
    ])

# Define the width of the bars
bar_width = 0.35  # Adjust this as necessary to fit your plot

# Calculate the positions for the bars
positions = np.arange(len(average_runtime_costs))

# Plotting and Saving Results
fig, ax1 = plt.subplots(figsize=(12, 6))

# Bar plot for average runtime - modify this part
ax1.set_xlabel(xlabel)
ax1.set_ylabel(ylabel_runtime, color='blue')
# Offset the x positions by subtracting half the width of the bar
ax1.bar(positions - bar_width / 2, average_runtime_costs[runtime_key], width=bar_width, color='blue', label='Average Runtime (seconds)')
ax1.tick_params(axis='y', labelcolor='blue')

# Set the x-ticks to the middle of the two sets of bars
ax1.set_xticks(positions)
ax1.set_xticklabels(average_runtime_costs[xkey], rotation=45, ha='right')

# Create a twin axis for the average costs - modify this part
ax2 = ax1.twinx()
ax2.set_ylabel(ylabel_costs, color='green')
# Offset the x positions by adding half the width of the bar
ax2.bar(positions + bar_width / 2, average_runtime_costs[costs_key], width=bar_width, color='green', label='Average Costs (USD)')
ax2.tick_params(axis='y', labelcolor='green')

# Title and layout
plt.title(plot_title)
fig.tight_layout()

# Saving the figure
plt.savefig(output_figure_path, dpi=300, bbox_inches='tight')

# Showing the figure
plt.show()
