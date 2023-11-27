import pandas as pd
import matplotlib.pyplot as plt
import sys

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
test_approaches_to_include = [1, 2, 3, 4]

filtered_data = filtered_data[filtered_data['test_approach'].isin(test_approaches_to_include)]

# Convert runtime to numeric
filtered_data['runtime(seconds)'] = pd.to_numeric(filtered_data['runtime(seconds)'], errors='coerce')

# Group by 'test_tool' and 'build' to sum the runtimes
summed_runtimes = filtered_data.groupby(['test_tool', 'build'])['runtime(seconds)'].sum().reset_index()

# Plot
plt.figure(figsize=(12, 6))
for tool in summed_runtimes['test_tool'].unique():
    tool_data = summed_runtimes[summed_runtimes['test_tool'] == tool]
    plt.plot(tool_data['build'], tool_data['runtime(seconds)'], label=tool)

plt.ylabel('Runtime (seconds)')
plt.xlabel('Build')
plt.title('Runtimes by Test Tool (static)')
plt.legend()
plt.tight_layout()
plt.show()

# Save the plot
plt.savefig('runtime_distribution_by_tt_static.png', dpi=300, bbox_inches='tight')
