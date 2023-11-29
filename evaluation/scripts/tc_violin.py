# Import Statements
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# Custom utility functions
from utils.utils import *

# Argument Parsing
data_path = '../../measurements/merged_measurements_3.csv'
if len(sys.argv) == 2:
    data_path = sys.argv[1]

# Variable Definition
ykey = 'runtime(seconds)'
legend_key = 'label'
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
    # exclude tests prior to tc14 implementation (prior build 142)
    filtered_data = filter_data_sets_by_build(filtered_data, min_build_value=140)
    # Filter for test approaches to include
    filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]
    # Filter out rows where runtime is less than 60 seconds
    # to exclude raw dynamic test cases without deploy/destroy overhead
    filtered_data = filtered_data[filtered_data['runtime(seconds)'] > 60]
    return filtered_data

def data_processing_for_violin(data):
    # Processing data for violin plot
    data['label'] = data.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)
    return data

def generate_violin_plot(data, plot_title, output_figure_path):
    plt.figure(figsize=(12, 6))
    sns.violinplot(x='label', y=ykey, data=data)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.title(plot_title)
    plt.tight_layout()
    plt.savefig(output_figure_path, dpi=300, bbox_inches='tight')
    plt.show()

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
static_data = static_filtering(data)
dynamic_data_fast = dynamic_filtering_fast(data)
dynamic_data_slow = dynamic_filtering_slow(data)

static_data = data_processing_for_violin(static_data)
dynamic_data_fast = data_processing_for_violin(dynamic_data_fast)
dynamic_data_slow = data_processing_for_violin(dynamic_data_slow)

# Generate Plots
output_figure_path_static = os.path.join(diagrams_dir, 'violin_static.png')
output_figure_path_dynamic_fast = os.path.join(diagrams_dir, 'violin_dynamic_fast.png')
output_figure_path_dynamic_slow = os.path.join(diagrams_dir, 'violin_dynamic_slow.png')

generate_violin_plot(static_data, plot_title + ' (Static)', output_figure_path_static)
generate_violin_plot(dynamic_data_fast, plot_title + ' (Dynamic, <= 1 minute)', output_figure_path_dynamic_fast)
generate_violin_plot(dynamic_data_slow, plot_title + ' (Dynamic, > 1 minute)', output_figure_path_dynamic_slow)
