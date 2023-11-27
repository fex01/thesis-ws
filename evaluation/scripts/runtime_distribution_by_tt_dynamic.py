import pandas as pd
import matplotlib.pyplot as plt
import sys
from utils.utils import process_apply_destroy_sequences

# Set the default file path
file_path = '../measurements/merged_measurements_3.csv'

# Check if an argument is provided and use it if available
if len(sys.argv) == 2:
    file_path = sys.argv[1]

# Read the CSV data
data = pd.read_csv(file_path)

# Filter out rows with 'NA' in the 'test_case' and 'runtime(seconds)' columns
filtered_data = data[(data['test_case'] != 'NA') & (data['runtime(seconds)'] != 'NA')]

# Define the range of test_approaches to include
test_approaches_to_include = [5, 6]

filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]

# Convert runtime to numeric
filtered_data['runtime(seconds)'] = pd.to_numeric(filtered_data['runtime(seconds)'], errors='coerce')

# Process and exclude 'terraform apply' and 'terraform destroy' entries
apply_destroy_data = process_apply_destroy_sequences(filtered_data)
exclude_tools = ['terraform apply', 'terraform destroy', 'exclude']
filtered_data = filtered_data[~filtered_data['test_tool'].isin(exclude_tools)]
filtered_data = pd.concat([filtered_data, apply_destroy_data])

# Group by 'test_tool' and 'build' to sum the runtimes
summed_runtimes = filtered_data.groupby(['test_tool', 'build'])['runtime(seconds)'].sum().reset_index()

# Plot
plt.figure(figsize=(12, 6))
for tool in summed_runtimes['test_tool'].unique():
    tool_data = summed_runtimes[summed_runtimes['test_tool'] == tool]
    plt.plot(tool_data['build'], tool_data['runtime(seconds)'], label=tool)

plt.ylabel('Runtime (seconds)')
plt.xlabel('Build')
plt.title('Runtimes by Test Tool (dynamic)')
plt.legend()
plt.tight_layout()
plt.show()

# Save the plot
plt.savefig('runtime_distribution_by_tt_dynamic.png', dpi=300, bbox_inches='tight')
