import os
import re
from collections import Counter

# Directory containing the .txt files
directory = 'exp_logs/6 ASTAR mega-run full-log-heauristic0'

# Regular expression pattern to match h_cost=<integer>
pattern = r'h_cost=(\d+)'

# Counter to store the distribution of h_cost values
h_cost_distribution = Counter()

# Iterate through all .txt files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.txt'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as file:
            content = file.read()
            # Find all matches of the pattern in the file
            matches = re.findall(pattern, content)
            # Convert matches to integers and update the counter
            h_cost_distribution.update(map(int, matches))

# Print the distribution as value and frequency pairs
print("h_cost value and frequency pairs:")
for value, count in sorted(h_cost_distribution.items()):
    print(f"{value} {count}")