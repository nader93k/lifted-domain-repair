import os
import numpy as np
import re
from collections import Counter
import matplotlib.pyplot as plt


def folder6():
    """
    Find the distribution of heuristic values on ASTAR mega-run
    """
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

def folder7():
    """
    Analyse the resultws for Songtuan's vanilla algorithm...
    """
    def get_txt_files(folder_path):
        return [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    def extract_lengths(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            repair_match = re.search(r'>>>  Vanilla ground repair length:\s*(\d+)', content)
            plan_match = re.search(r'> Plan length=\s*(\d+)', content)
            
            repair_length = int(repair_match.group(1)) if repair_match else None
            plan_length = int(plan_match.group(1)) if plan_match else None
            
        return repair_length, plan_length

    def analyze_lengths(folder_path):
        txt_files = get_txt_files(folder_path)
        repair_lengths = []
        plan_lengths = []

        for file in txt_files:
            repair_length, plan_length = extract_lengths(os.path.join(folder_path, file))
            if repair_length is not None and plan_length is not None:
                repair_lengths.append(repair_length)
                plan_lengths.append(plan_length)

        return repair_lengths, plan_lengths
    
    def print_long_repair_files(folder_path):
        txt_files = get_txt_files(folder_path)
        long_repairs = []

        for file in txt_files:
            file_path = os.path.join(folder_path, file)
            repair_length, plan_length = extract_lengths(file_path)
            if repair_length is not None and repair_length > 4:
                long_repairs.append((file, repair_length, plan_length))

        # Sort the list by repair length in descending order
        long_repairs.sort(key=lambda x: x[1], reverse=True)

        print("\nFiles with repair length greater than 4 (sorted by repair length, descending):")
        print("Filename: Repair Length, Plan Length")
        for file, repair_length, plan_length in long_repairs:
            print(f"{file}: {repair_length}, {plan_length}")
    
    def plot_distribution(repair_lengths):
        counter = Counter(repair_lengths)
        total_instances = len(repair_lengths)

        lengths = list(counter.keys())
        frequencies = list(counter.values())
        percentages = [freq / total_instances * 100 for freq in frequencies]

        fig, ax1 = plt.subplots(figsize=(12, 6))

        bars = ax1.bar(lengths, frequencies, color='skyblue', alpha=0.7)
        ax1.set_xlabel("Songtuan's Repair Length")
        ax1.set_ylabel('Frequency', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Add frequency labels and percentages on top of each bar
        for bar, percentage in zip(bars, percentages):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)} ({percentage:.1f}%)',
                    ha='center', va='bottom', fontsize=8)

        ax2 = ax1.twinx()
        ax2.set_ylabel('Percentage (%)')
        ax2.tick_params(axis='y')

        plt.title("Distribution of Songtuan's Repair Length")
        plt.text(0.95, 0.95, f'Total Instances: {total_instances}', 
                horizontalalignment='right', verticalalignment='top', 
                transform=ax1.transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.5))

        plt.tight_layout()
        
        plt.savefig('repair_length_distribution.png')
        print("Visualization saved as 'repair_length_distribution.png' in the current folder.")
    
    def plot_scatter(repair_lengths, plan_lengths):
        plt.figure(figsize=(12, 8))
        plt.scatter(plan_lengths, repair_lengths, alpha=0.6)
        plt.xlabel('Plan Length')
        plt.ylabel('Repair Length')
        plt.title('Scatter Plot: Plan Length vs Repair Length')
        
        # Add a line of best fit
        z = np.polyfit(plan_lengths, repair_lengths, 1)
        p = np.poly1d(z)
        plt.plot(plan_lengths, p(plan_lengths), "r--", alpha=0.8)
        
        # Add correlation coefficient
        correlation = np.corrcoef(plan_lengths, repair_lengths)[0, 1]
        plt.text(0.95, 0.95, f'Correlation: {correlation:.2f}', 
                horizontalalignment='right', verticalalignment='top', 
                transform=plt.gca().transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('plan_vs_repair_length_scatter.png')
        print("Scatter plot saved as 'plan_vs_repair_length_scatter.png' in the current folder.")


        # Usage
    folder_path = './exp_logs/7 Songtuan Vanilla'  # Replace with your folder path
    repair_lengths, plan_lengths = analyze_lengths(folder_path)
    plot_distribution(repair_lengths)
    print_long_repair_files(folder_path)
    plot_scatter(repair_lengths, plan_lengths)


folder7()
