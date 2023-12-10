# Import Statements
from matplotlib import pyplot as plt
import numpy as np
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
label_key = 'label'
runtime_key = 'runtime(seconds)'
costs_key = 'costs(USD)'

# Directory Management for Outputs
diagrams_dir = '../diagrams'
tables_dir = '../tables'
os.makedirs(diagrams_dir, exist_ok=True)
os.makedirs(tables_dir, exist_ok=True)

def filtering_static_tc(data):
    test_approaches_to_include = [1, 2, 3, 4]
    data = data[(data['test_case'] != -1)]
    # exclude tests prior to refactoring (prior build 140)
    data = filter_data_sets_by_build(data, min_build_value=140)
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    return data

def filtering_dynamic_combined_tc(data):
    test_approaches_to_include = [5, 6]
    data = data[(data['test_case'] != -1)]
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    # Filter out rows where runtime is greater than 60 seconds
    # to only show raw dynamic test cases without deploy/destroy overhead
    data = data[data['runtime(seconds)'] <= 60]
    return data

def filtering_dynamic_standalone_tc(data):
    test_approaches_to_include = [5, 6]
    # Filter for data sets including tc14
    data = without_incomplete_data_sets(data, 14)
    data = flatten_multi_tc_apply_destroy_cycles(data)
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    # Filter out rows where runtime is less than 60 seconds
    # to exclude raw dynamic test cases without deploy/destroy overhead
    data = data[data['runtime(seconds)'] > 60]
    return data

def filtering_deploy_destroy_phases(data):
    # Cover the same build range as filtering_dynamic_standalone_tc
    data = without_incomplete_data_sets(data, 14)
    data = data[data['test_tool'].isin(['terraform apply', 'terraform destroy'])]
    return data

def filtering_static_stages(data):
    test_approaches_to_include = [1, 2, 3, 4]
    # Filter out rows with 'NA' in 'runtime(seconds)'
    data = data[(data['runtime(seconds)'].notna())]
    # exclude tests prior to refactoring (prior build 140)
    data = filter_data_sets_by_build(data, min_build_value=140)
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    return data

def filtering_dynamic_stages(data):
    test_approaches_to_include = [5, 6]
    data = without_incomplete_data_sets(data, 14)
    data = flatten_multi_tc_apply_destroy_cycles(data)
    # Filter out rows with 'NA' in 'runtime(seconds)'
    data = data[(data['runtime(seconds)'].notna())]
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    return data

def tc_data_processing(data):
    # Calculating Average Runtimes
    data = data.groupby(['test_case', 'test_approach'])['runtime(seconds)'].mean().reset_index()
    # Sorting the results first by 'test_approach' and then by 'test_case'
    data.sort_values(by=['test_approach', 'test_case'], inplace=True)
    data['label'] = data.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)
    return data

def tc_costs_data_processing(data):
    # Calculating Average Costs
    data = data.groupby(['test_case', 'test_approach']).agg({runtime_key: 'mean', costs_key: 'mean'}).reset_index()
    # Sorting the results first by 'test_approach' and then by 'test_case'
    data.sort_values(by=['test_approach', 'test_case'], inplace=True)
    data['label'] = data.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)
    return data

def deploy_phases_data_processing(data):
    # Calculating Average Runtimes
    data = data.groupby(['test_tool'])['runtime(seconds)'].mean().reset_index()
    data['label'] = data.apply(lambda row: format_deploy_phase_label(row['test_tool']), axis=1)
    return data

def stage_data_processing(data):
    # Get overall stage runtimes: group by 'build', 'test_tool', and 'test_approach' and sum the runtimes
    data = data.groupby(['build','test_approach', 'test_tool'])['runtime(seconds)'].sum().reset_index()
    # Get average stage runtimes: group by 'test_tool' and 'test_approach' and calculate the average of these sums
    data = data.groupby(['test_approach', 'test_tool'])['runtime(seconds)'].mean().reset_index()
    # Create a combined label for test tool and test approach
    data['label'] = data['test_tool'] + " (TA" + data['test_approach'].astype(str) + ")"
    return data

def generate_bar_plot(data, plot_title, xkey, xlabel, ykey, ylabel, output_path):
    # Plotting and Saving Results
    plt.figure(figsize=(12, 6))
    plt.bar(data[xkey], data[ykey], color='blue', width=0.8)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.xticks(rotation=45, ha='right')
    plt.title(plot_title)
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()

def generate_double_bar_plot(data, plot_title, xkey, xlabel, ykey, ylabel, y2key, y2label, output_path):
    # Define the width of the bars
    bar_width = 0.35  # Adjust this as necessary to fit your plot
    # Calculate the positions for the bars
    positions = np.arange(len(data))
    # Plotting and Saving Results
    fig, ax1 = plt.subplots(figsize=(12, 6))
    # Bar plot for average runtime
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel, color='blue')
    # Offset the x positions by subtracting half the width of the bar
    ax1.bar(positions - bar_width / 2, data[ykey], width=bar_width, color='blue', label=ylabel)
    ax1.tick_params(axis='y', labelcolor='blue')
    # Set the x-ticks to the middle of the two sets of bars
    ax1.set_xticks(positions)
    ax1.set_xticklabels(data[xkey], rotation=45, ha='right')
    # Create a twin axis for the average costs
    ax2 = ax1.twinx()
    ax2.set_ylabel(y2label, color='green')
    # Offset the x positions by adding half the width of the bar
    ax2.bar(positions + bar_width / 2, data[y2key], width=bar_width, color='green', label=y2label)
    ax2.tick_params(axis='y', labelcolor='green')
    # Title and layout
    plt.title(plot_title)
    fig.tight_layout()
    # Saving the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()


# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)

dynamic_combined_tc_data = filtering_dynamic_combined_tc(data)
dynamic_standalone_tc_data = filtering_dynamic_standalone_tc(data)
tc_runtime_data = tc_data_processing(pd.concat([
    filtering_static_tc(data), 
    dynamic_combined_tc_data, 
    dynamic_standalone_tc_data
]))

tc_runtime_data_extended = pd.concat([
    tc_runtime_data, 
    deploy_phases_data_processing(filtering_deploy_destroy_phases(data))
])

tc_cost_data = tc_costs_data_processing(pd.concat([ 
    dynamic_combined_tc_data, 
    dynamic_standalone_tc_data
]))

stage_runtime_data = stage_data_processing(pd.concat([
    filtering_static_stages(data), 
    filtering_dynamic_stages(data)
]))

plots_info = [
    {
        "data": stage_runtime_data,
        "label_prefix": 'stage_',
        "caption": 'Average Test Stage Runtime',
        "xlabel": 'Test Tool and Approach',
        "ylabel": 'Average Runtime (Seconds, Log Scale)',
        "type": "bar",
        "digits": 2
    },
    {
        "data": tc_cost_data,
        "label_prefix": 'tc_cost_',
        "caption": 'Average Runtime and Costs per Dynamic Test Case',
        "xlabel": 'Test Case and Approach',
        "ylabel": 'Average Runtime (Seconds)',
        "y2label": 'Average Costs (USD)',
        "type": "double_bar",
        "digits": 2
    },
    {
        "data": tc_runtime_data_extended,
        "label_prefix": 'tc_',
        "caption": 'Average Test Case Runtime',
        "xlabel": 'Test Case and Approach',
        "ylabel": 'Average Runtime (Seconds, Log Scale)',
        "type": "bar",
        "digits": 2
    }
]

filename = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Iterate over the data structure and generate plots
for plot_info in plots_info:
    output_path = os.path.join(diagrams_dir, plot_info["label_prefix"] + filename + '.png')
    if plot_info["type"] == "bar":
        generate_bar_plot(
            plot_info["data"],
            plot_info["caption"],
            xkey=label_key,
            xlabel=plot_info["xlabel"],
            ykey=runtime_key,
            ylabel=plot_info["ylabel"],
            output_path=output_path
        )
        header_key_pairs=[
            (plot_info["xlabel"], label_key),
            (plot_info["ylabel"], runtime_key)
        ]
    elif plot_info["type"] == "double_bar":
        generate_double_bar_plot(
            plot_info["data"],
            plot_info["caption"],
            xkey=label_key,
            xlabel=plot_info["xlabel"],
            ykey=runtime_key,
            ylabel=plot_info["ylabel"],
            y2key=costs_key,
            y2label=plot_info["y2label"],
            output_path=output_path
        )
        header_key_pairs=[
            (plot_info["xlabel"], label_key),
            (plot_info["ylabel"], runtime_key),
            (plot_info["y2label"], costs_key)
        ]
    # Create LaTeX table and figure boilerplate
    latex_label = plot_info["label_prefix"] + filename
    write_latex(plot_info["caption"], latex_label)
    write_latex(
        caption=plot_info["caption"],
        label=latex_label,
        data=plot_info["data"],
        header_key_pairs=header_key_pairs,
        digits=plot_info["digits"]
    )





