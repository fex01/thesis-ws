# Import Statements
from matplotlib import pyplot as plt
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
xkey = 'test_case'
ykey = 'costs(USD)'
label_key = 'label'
xlabel = 'Test Case'
ylabel = 'Cloud Provider Costs (USD)'
plot_title = 'Test Case Cloud Provider Costs Distribution'

# Directory Management for Outputs
diagrams_dir = '../diagrams'
os.makedirs(diagrams_dir, exist_ok=True)

def filtering_dynamic_tc(data):
    test_approaches_to_include = [5, 6]
    # Filter for data sets including tc14
    data = without_incomplete_data_sets(data, 14)
    data = flatten_multi_tc_apply_destroy_cycles(data, delete_originals=False)
    # Filter for test approaches to include
    data = data[data['test_approach'].isin(test_approaches_to_include)]
    # Filter out deploy/destroy entries
    data = data[(data['test_case'] != -1)]
    return data

def tc_data_processing(data):
    # Sorting the results first by 'test_approach' and then by 'test_case'
    data['label'] = data.apply(lambda row: short_test_case_label(row['test_case']), axis=1)
    data.sort_values(by=[xkey], inplace=True)
    return data

def generate_box_whisker_plot(data, plot_title, xkey, xlabel, ykey, ylabel, output_path):
    plt.figure(figsize=(12, 6))
    # Create a mapping from xkey values to their order in the unique array
    unique_keys = data[xkey].unique()
    order_mapping = {key: i for i, key in enumerate(unique_keys)}
    # Group the data by xkey without sorting
    grouped_data = data.groupby(xkey, sort=False)
    # Sort the plot data based on the order_mapping determined by the unique keys
    plot_data = [group[ykey].values for _, group in sorted(grouped_data, key=lambda x: order_mapping[x[0]])]
    plt.boxplot(plot_data)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    # Set the x-axis ticks to the unique xkey values in the original order
    plt.xticks(range(1, len(unique_keys) + 1), unique_keys)   
    plt.title(plot_title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()

def generate_dual_box_whisker_plot(data, data_subset_1, data_subset_2, plot_title, xkey, xlabel, ykey, ylabel, output_path):
    plt.figure(figsize=(15, 6))
    # First subplot
    plt.subplot(1, 2, 1)
    generate_single_box_whisker_plot(data_subset_1, xkey, xlabel, ykey, ylabel)
    plt.title(plot_title + " (Multiple TC in One Cycle)")
    # Second subplot
    plt.subplot(1, 2, 2)
    generate_single_box_whisker_plot(data_subset_2, xkey, xlabel, ykey, ylabel)
    plt.title(plot_title + " (Complete Cycle)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()

def generate_single_box_whisker_plot(data, xkey, xlabel, ykey, ylabel):
    unique_keys = data[xkey].unique()
    order_mapping = {key: i for i, key in enumerate(unique_keys)}
    grouped_data = data.groupby(xkey, sort=False)
    plot_data = [group[ykey].values for _, group in sorted(grouped_data, key=lambda x: order_mapping[x[0]])]
    plt.boxplot(plot_data)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.xticks(range(1, len(unique_keys) + 1), unique_keys)

# Data Loading, Filtering and Processing
data = read_csv_to_dataframe(data_path)
tc_data = tc_data_processing(filtering_dynamic_tc(data))
tc_data_net = tc_data[tc_data['test_case'].isin([4, 7, 9])]
tc_data_complete = tc_data[~tc_data['test_case'].isin([4, 7, 9])]
filename = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
output_path = os.path.join(diagrams_dir, filename + '.png')

# Generate plot, latex table and latex figure boilerplate
# generate_box_whisker_plot(
#     data=tc_data,
#     plot_title=plot_title,
#     xkey=label_key,
#     xlabel=xlabel,
#     ykey=ykey,
#     ylabel=ylabel,
#     output_path=output_path
# )
generate_dual_box_whisker_plot(
    data=tc_data,
    data_subset_1=tc_data_net,
    data_subset_2=tc_data_complete,
    plot_title=plot_title,
    xkey=label_key,
    xlabel=xlabel,
    ykey=ykey,
    ylabel=ylabel,
    output_path=output_path
)
write_latex(
    caption=plot_title,
    label=filename,
    data=tc_data,
    header_key_pairs=[
        ("", label_key),
        (ylabel, ykey)
    ],
    digits=5,
    summary_table=True
)
write_latex(caption=plot_title, label=filename)