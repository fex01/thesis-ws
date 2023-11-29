# Import Statements
from doctest import debug
from matplotlib import legend, pyplot as plt
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
xkey = 'build'
ykey = 'runtime(seconds)'
legend_key = 'label'
xlabel = 'Build'
ylabel = 'Runtime (Seconds)'
legend_label = 'TC (TA)'
plot_title = 'Test Case Runtime Distribution'

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

def static_filtering(data):
    test_approaches_to_include = [1, 2, 3, 4]
    filtered_data = data[(data['test_case'] != -1)]
    # exclude tests prior to refactoring (prior build 140)
    filtered_data = filter_data_sets_by_build(filtered_data, min_build_value=140)
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    return filtered_data

def dynamic_filtering_fast(data):
    test_approaches_to_include = [5, 6]
    filtered_data = data[(data['test_case'] != -1)]
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    # Filter out rows where runtime is greater than 60 seconds
    # to only show raw dynamic test cases without deploy/destroy overhead
    filtered_data = filtered_data[filtered_data['runtime(seconds)'] <= 60]
    return filtered_data

def dynamic_filtering_slow(data):
    test_approaches_to_include = [5, 6]
    filtered_data = flatten_multi_tc_apply_destroy_cycles(data)
    filtered_data = filtered_data[(filtered_data['test_case'] != -1)]
    # Filter for data sets including tc14
    filtered_data = without_incomplete_data_sets(filtered_data, 14)
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    # Filter out rows where runtime is less than 60 seconds
    # to exclude raw dynamic test cases without deploy/destroy overhead
    filtered_data = filtered_data[filtered_data['runtime(seconds)'] > 60]
    return filtered_data

def data_processing(data):
    # Sorting the results first by 'test_approach' and then by 'test_case'
    data.sort_values(by=['test_approach', 'test_case'], inplace=True)
    data['label'] = data.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)
    return data

def generate_plot(data, plot_title, output_figure_path):
    plt.figure(figsize=(12, 6))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(plot_title)

    # Sort the legend labels based on the test_approach part of the label
    label_handles = {}  # Dictionary to hold label-handle pairs
    for label in data['label'].unique():
        label_data = data[data['label'] == label]
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

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
static_data = static_filtering(data)
dynamic_data_fast = dynamic_filtering_fast(data)
dynamic_data_slow = dynamic_filtering_slow(data)

static_data = data_processing(static_data)
dynamic_data_fast = data_processing(dynamic_data_fast)
dynamic_data_slow = data_processing(dynamic_data_slow)

# Output Preparation
name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
output_table_path = os.path.join(tables_dir, name + '.tex')
output_figure_path_static = os.path.join(diagrams_dir, name + '_static.png')
output_figure_path_dynamic_fast = os.path.join(diagrams_dir, name + '_dynamic_fast.png')
output_figure_path_dynamic_slow = os.path.join(diagrams_dir, name + '_dynamic_slow.png')
plot_title_static = plot_title + ' (Static)'
plot_title_dynamic_fast = plot_title + ' (Dynamic, <= 1 minute)'
plot_title_dynamic_slow = plot_title + ' (Dynamic, > 1 minute)'

sorted_labels_static = generate_plot(static_data, plot_title_static, output_figure_path_static)
sorted_labels_dynamic_fast = generate_plot(dynamic_data_fast, plot_title_dynamic_fast, output_figure_path_dynamic_fast)
sorted_labels_dynamic_slow = generate_plot(dynamic_data_slow, plot_title_dynamic_slow, output_figure_path_dynamic_slow)


# Combine static and dynamic data
combined_data = pd.concat([static_data, dynamic_data_fast, dynamic_data_slow])
combined_labels = sorted_labels_static + sorted_labels_dynamic_fast + sorted_labels_dynamic_slow

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
                                 ('_dynamic_fast', ' (Dynamic, <= 1 minute)'), 
                                 ('_dynamic_slow', ' (Dynamic, > 1 minute)')])

