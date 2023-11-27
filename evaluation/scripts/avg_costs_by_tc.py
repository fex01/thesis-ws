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

# Convert costs to numeric
data['costs(USD)'] = pd.to_numeric(data['costs(USD)'])

# Group by test case and calculate the average costs
average_costs = data.groupby('test_case')['costs(USD)'].mean()

# Plotting
plt.figure(figsize=(12, 6))

# Plot average costs
plt.bar(average_costs.index.astype(str), average_costs, color='green')

# Set the y-axis label for costs
plt.ylabel('Average Costs (USD)')
plt.xlabel('Test Case')

# Ensure the x-ticks are treated as categorical data and placed accordingly
plt.xticks(ticks=range(len(average_costs)), labels=average_costs.index.astype(str))

# Set plot title
plt.title('Average Costs per Test Case')

plt.tight_layout()
plt.show()

# Save the plot
plt.savefig('avg_costs_by_tc.png', dpi=300, bbox_inches='tight')
