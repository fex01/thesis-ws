# Import Statements
from doctest import debug
from matplotlib import legend, pyplot as plt
import pandas as pd
import sys
import os

# Custom utility functions
from utils.utils import *

def static_filtering(data):
    test_approaches_to_include = [1, 2, 3, 4]
    # Filter out rows with 'NA' in 'runtime(seconds)'
    filtered_data = data[(data['runtime(seconds)'].notna())]
    # exclude tests prior to refactoring (prior build 140)
    filtered_data = filter_data_sets_by_build(filtered_data, min_build_value=140)
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    return filtered_data

def dynamic_filtering(data):
    test_approaches_to_include = [5, 6]
    filtered_data = without_incomplete_data_sets(data, 14)
    filtered_data = flatten_multi_tc_apply_destroy_cycles(filtered_data)
    # Filter out rows with 'NA' in 'runtime(seconds)'
    filtered_data = filtered_data[(filtered_data['runtime(seconds)'].notna())]
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    return filtered_data

def data_processing(data):
    # Get overall stage runtimes: group by 'build', 'test_tool', and 'test_approach' and sum the runtimes
    summed_runtimes = data.groupby(['build', 'test_tool', 'test_approach'])['runtime(seconds)'].sum().reset_index()
    # Create a combined label for test tool and test approach
    summed_runtimes['tool_approach'] = summed_runtimes['test_tool'] + " (TA" + summed_runtimes['test_approach'].astype(str) + ")"
    return summed_runtimes

def generate_plot(summed_runtimes, plot_title, output_figure_path):
    plt.figure(figsize=(12, 6))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(plot_title)

    # Sort the legend labels based on the test_approach part of the label
    label_handles = {}  # Dictionary to hold label-handle pairs
    for label in summed_runtimes['tool_approach'].unique():
        label_data = summed_runtimes[summed_runtimes['tool_approach'] == label]
        line, = plt.plot(label_data['build'], label_data['runtime(seconds)'], label=label)
        label_handles[label] = line  # Store the handle against the label

    # Sorting labels and handles
    sorted_labels_handles = sorted(label_handles.items(), key=lambda lh: lh[0].split(' (TA')[1])
    sorted_labels = [label for label, handle in sorted_labels_handles]
    plt.legend(handles=[label_handles[label] for label in sorted_labels])

    plt.tight_layout()
    plt.savefig(output_figure_path, dpi=300, bbox_inches='tight')
    plt.show()

    return sorted_labels

# Argument Parsing
# Check if an argument is provided and use it if available
data_path = '../../measurements/merged_measurements_3.csv'
if len(sys.argv) == 2:
    data_path = sys.argv[1]

# Variable Definition
xkey = 'build'
ykey = 'runtime(seconds)'
legend_key = 'tool_approach'
xlabel = 'Build'
ylabel = 'Runtime (Seconds)'
legend_label = 'Test Tool (TA)'
plot_title = 'Test Stage Runtime Distribution'

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
static_data = static_filtering(data)
dynamic_data = dynamic_filtering(data)

static_data = data_processing(static_data)
dynamic_data = data_processing(dynamic_data)

# Output Preparation
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path_static = os.path.join(diagrams_dir, name + '_static.png')
output_figure_path_dynamic = os.path.join(diagrams_dir, name + '_dynamic.png')
plot_title_static = plot_title + ' (Static)'
plot_title_dynamic = plot_title + ' (Dynamic)'

sorted_labels_static = generate_plot(static_data, plot_title_static, output_figure_path_static)
sorted_labels_dynamic = generate_plot(dynamic_data, plot_title_dynamic, output_figure_path_dynamic)


# Combine static and dynamic data
combined_data = pd.concat([static_data, dynamic_data])
combined_labels = sorted_labels_static + sorted_labels_dynamic

# Write the LaTeX summary table for the combined data
write_latex_summary_table(df=combined_data, 
                          filename=output_table_path, 
                          plot_title=plot_title,
                          ylabel=ylabel,
                          legend_label=legend_label,
                          ykey=ykey,
                          legend_key=legend_key,
                          series=combined_labels,
                          suffixes=[
                                 ('_static', ' (Static)'), 
                                 ('_dynamic', ' (Dynamic)')])

