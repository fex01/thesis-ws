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

# Filter out rows where costs are 'NA' or not available
data = data.dropna(subset=['costs(USD)'])
data = data[data['costs(USD)'] != 'NA']

# Convert runtime and costs to numeric
data['runtime(seconds)'] = pd.to_numeric(data['runtime(seconds)'])
data['costs(USD)'] = pd.to_numeric(data['costs(USD)'])

# Group by test case and calculate the average runtime and costs
grouped_data = data.groupby('test_case')[['runtime(seconds)', 'costs(USD)']].mean()

# Plotting
fig, ax1 = plt.subplots(figsize=(12, 6))

# Locations for the bars on the x-axis
ind = range(len(grouped_data))

# Width of the bars
width = 0.35

# Plot runtime
ax1.bar(ind, grouped_data['runtime(seconds)'], width, color='blue', label='Average Runtime (seconds)')

# Set the y-axis label for runtime
ax1.set_ylabel('Average Runtime (seconds)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Create another y-axis for the costs
ax2 = ax1.twinx()

# Plot costs
ax2.bar([i + width for i in ind], grouped_data['costs(USD)'], width, color='orange', label='Average Costs (USD)')

# Set the y-axis label for costs
ax2.set_ylabel('Average Costs (USD)', color='orange')
ax2.tick_params(axis='y', labelcolor='orange')

# Set x-axis labels
ax1.set_xlabel('Test Case')
ax1.set_xticks([i + width / 2 for i in ind])
ax1.set_xticklabels(grouped_data.index)

# Set plot title and show legend
plt.title('Average Runtime and Costs per Test Case')
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

fig.tight_layout()
plt.show()

# Save the plot
plt.savefig('test_case_analysis.png', dpi=300, bbox_inches='tight')
