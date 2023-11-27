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

# Filter out rows with 'NA' in the test_case column
filtered_data = data[data['test_case'] != 'NA']

# Convert runtime to numeric, coercing errors to NaN (to handle any non-numeric values)
filtered_data['runtime(seconds)'] = pd.to_numeric(filtered_data['runtime(seconds)'], errors='coerce')

# Calculate the average runtime for each test case
average_runtimes = filtered_data.groupby('test_case')['runtime(seconds)'].mean()

# Convert test case numbers to integers for plotting
average_runtimes.index = average_runtimes.index.astype(int)

# Plot
plt.figure(figsize=(12, 6))

# Plot average runtimes
plt.bar(average_runtimes.index.astype(str), average_runtimes, color='blue')

# Set the y-axis label for runtimes
plt.ylabel('Average Runtime (seconds, log scale)')
plt.xlabel('Test Case')

# Ensure the x-ticks are treated as categorical data and placed accordingly
plt.xticks(ticks=range(len(average_runtimes)), labels=average_runtimes.index.astype(str))

# Set plot title
plt.title('Average Runtime per Test Case')

plt.yscale('log')  # Using logarithmic scale
plt.tight_layout()
plt.show()

# Save the plot
plt.savefig('avg_runtime_by_tc.png', dpi=300, bbox_inches='tight')
