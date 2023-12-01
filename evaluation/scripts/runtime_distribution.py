# Import Statements
from matplotlib import pyplot as plt
import pandas as pd
import sys
import os
import seaborn as sns

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
plot_title_tc = 'Test Case Runtime Distribution'
plot_title_stage = 'Test Stage Runtime Distribution'

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
    # Sorting the results first by 'test_approach' and then by 'test_case'
    data.sort_values(by=['test_approach', 'test_case', 'build'], inplace=True)
    data['label'] = data.apply(lambda row: format_test_case_label(row['test_case'], row['test_approach']), axis=1)
    return data

def deploy_phases_data_processing(data):
    processed_data = data.copy()
    processed_data.sort_values(by=['build'], inplace=True)
    processed_data['label'] = processed_data.apply(lambda row: format_deploy_phase_label(row['test_tool']), axis=1)
    return processed_data

def stage_data_processing(data):
    # Get overall stage runtimes: group by 'build', 'test_tool', and 'test_approach' and sum the runtimes
    data = data.groupby(['build','test_approach', 'test_tool'])['runtime(seconds)'].sum().reset_index()
    # Create a combined label for test tool and test approach
    data['label'] = data['test_tool'] + " (TA" + data['test_approach'].astype(str) + ")"
    return data

def generate_line_plot(data, plot_title, output_path):
    plt.figure(figsize=(12, 6))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(plot_title)
    for label in data['label'].unique():
        label_data = data[data['label'] == label]
        plt.plot(label_data['build'], label_data['runtime(seconds)'], label=label)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()

def generate_violin_plot(data, plot_title, xlabel, output_path):
    plt.figure(figsize=(12, 6))
    sns.violinplot(x=legend_key, y=ykey, data=data)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.title(plot_title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()

def create_latex_for_type(plots_info, type_key, plot_title, filename):
    combined_data = pd.DataFrame()

    # Iterate over plots_info to handle both table data combination and figure generation
    for plot_info in plots_info:
        if plot_info["type"] == type_key:
            # Combine data for tables
            combined_data = pd.concat([combined_data, plot_info["data"]])
            
            # Create figure for each plot_info
            figure_caption = plot_title + plot_info["caption_suffix"]
            figure_label = plot_info["label_prefix"] + filename
            write_latex(figure_caption,figure_label)
            write_latex(figure_caption,figure_label + '_violin')

    # Write the LaTeX summary table for the combined data
    write_latex(
        caption=plot_title,
        label=type_key + '_' + filename,
        data=combined_data,
        header_key_pairs=[
            ("", legend_key),
            (ylabel, ykey)
        ],
        summary_table=True
    )

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
static_tc_data = tc_data_processing(filtering_static_tc(data))
dynamic_combined_tc_data = tc_data_processing(filtering_dynamic_combined_tc(data))
dynamic_standalone_tc_data = tc_data_processing(filtering_dynamic_standalone_tc(data))
deploy_destroy_phases_data = deploy_phases_data_processing(filtering_deploy_destroy_phases(data))
dynamic_standalone_tc_and_phases_data = pd.concat([dynamic_standalone_tc_data, deploy_destroy_phases_data])
static_stages_data = stage_data_processing(filtering_static_stages(data))
dynamic_stages_data = stage_data_processing(filtering_dynamic_stages(data))

plots_info = [
    {
        "data": static_tc_data,
        "label_prefix": 'static_tc_',
        "caption_suffix": ' (Static)',
        "violin_xlabel": "Test Case and Approach",
        "type": "tc"
    },
    {
        "data": dynamic_combined_tc_data,
        "label_prefix": 'dynamic_combined_tc_',
        "caption_suffix": ' (Dynamic, Net TC Runtime)',
        "violin_xlabel": "Test Case and Approach",
        "type": "tc"
    },
    {
        "data": dynamic_standalone_tc_and_phases_data,
        "label_prefix": 'dynamic_standalone_tc_',
        "caption_suffix": ' (Dynamic, Including Deploy/Destroy Phases)',
        "violin_xlabel": "Test Case and Approach",
        "type": "tc"
    },
    {
        "data": static_stages_data,
        "label_prefix": 'static_stage_',
        "caption_suffix": ' (Static)',
        "violin_xlabel": "Test Tool and Approach",
        "type": "stage"
    },
    {
        "data": dynamic_stages_data,
        "label_prefix": 'dynamic_stage_',
        "caption_suffix": ' (Dynamic)',
        "violin_xlabel": "Test Tool and Approach",
        "type": "stage"
    }
]

filename = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]

# Iterate over the data structure and generate plots
for plot_info in plots_info:
    plot_title = plot_title_tc if plot_info["type"] == "tc" else plot_title_stage
    generate_line_plot(
        plot_info["data"],
        plot_title + plot_info["caption_suffix"],
        os.path.join(diagrams_dir, plot_info["label_prefix"] + filename + '.png')
    )
    generate_violin_plot(
        plot_info["data"],
        plot_title + plot_info["caption_suffix"],
        plot_info["violin_xlabel"],
        os.path.join(diagrams_dir, plot_info["label_prefix"] + filename + '_violin.png')
    )

# Create LaTeX tables for each type
create_latex_for_type(plots_info, "tc", plot_title_tc, filename)
create_latex_for_type(plots_info, "stage", plot_title_stage, filename)