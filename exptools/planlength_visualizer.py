import re
from collections import Counter
import statistics
import matplotlib.pyplot as plt

def analyze_log_file(file_path):
    plan_lengths = []
    instance_ids = []
    
    # Regular expressions to match the required patterns
    instance_pattern = re.compile(r'Instance ID=(.*)')
    plan_pattern = re.compile(r'Plan length=(\d+)')
    
    with open(file_path, 'r') as file:
        for line in file:
            instance_match = instance_pattern.match(line)
            plan_match = plan_pattern.match(line)
            
            if instance_match:
                instance_ids.append(instance_match.group(1))
            elif plan_match:
                plan_lengths.append(int(plan_match.group(1)))
    
    # Calculate statistics
    length_distribution = Counter(plan_lengths)
    total_plans = len(plan_lengths)
    avg_length = statistics.mean(plan_lengths)
    median_length = statistics.median(plan_lengths)
    min_length = min(plan_lengths)
    max_length = max(plan_lengths)
    
    # Print results
    print(f"Total number of plans: {total_plans}")
    print(f"Average plan length: {avg_length:.2f}")
    print(f"Median plan length: {median_length}")
    print(f"Minimum plan length: {min_length}")
    print(f"Maximum plan length: {max_length}")
    print("\nPlan length distribution:")
    for length, count in sorted(length_distribution.items()):
        percentage = (count / total_plans) * 100
        print(f"Length {length}: {count} plans ({percentage:.2f}%)")
    
    # Analyze instance IDs
    unique_instances = len(set(instance_ids))
    print(f"\nNumber of unique instance IDs: {unique_instances}")
    
    # Analyze error rates
    error_rates = [float(id.split('-')[-1]) for id in instance_ids if id.split('-')[-1].replace('.', '').isdigit()]
    if error_rates:
        avg_error_rate = statistics.mean(error_rates)
        print(f"Average error rate: {avg_error_rate:.2f}")
    
    # Plot and save cumulative distribution
    plot_cumulative_distribution(length_distribution, total_plans)

def plot_cumulative_distribution(length_distribution, total_plans):
    lengths = sorted(length_distribution.keys())
    counts = [length_distribution[length] for length in lengths]
    
    # Calculate cumulative distribution
    cumulative_counts = [sum(counts[:i+1]) for i in range(len(counts))]
    cumulative_percentages = [count / total_plans * 100 for count in cumulative_counts]
    
    # Create the plot with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot cumulative count on left y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Plan Length (log scale)')
    ax1.set_ylabel('Cumulative Number of Plans', color=color)
    ax1.semilogx(lengths, cumulative_counts, color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Create a second y-axis for percentage
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Cumulative Percentage', color=color)
    ax2.semilogx(lengths, cumulative_percentages, color=color, marker='s')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 100)
    
    # Add grid and title
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    plt.title('Cumulative Distribution of Plan Lengths')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, ['Cumulative Count', 'Cumulative Percentage'], loc='lower right')
    
    plt.tight_layout()
    plt.savefig('plan_length_cumulative_distribution.png')
    plt.close()
    
    print("Cumulative distribution plot has been saved as 'plan_length_cumulative_distribution.png' in the current folder.")

# Usage
base = 'exptools/'
file_path = base+'plan_lengths.txt'
analyze_log_file(file_path)