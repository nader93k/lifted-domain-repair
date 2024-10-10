import pandas as pd

def process_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Filter rows where results_exists is True
    df = df[df['results_exists'] == True]

    # Sort by result_g_cost in descending order
    df = df.sort_values(by='result_g_cost', ascending=False)

    # Function to count matching entries
    def count_matching_entries(str1, str2):
        set1 = set(str1.split('\n')) if isinstance(str1, str) else set()
        set2 = set(str2.split('\n')) if isinstance(str2, str) else set()
        return len(set1.intersection(set2))

    # Add new column counting matching entries
    df['matching_entries_count'] = df.apply(lambda row: count_matching_entries(row['str_ground_repair'], row['result_repair_set']), axis=1)

    # Save the result to a new CSV file
    df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")

# Usage
input_file = 'results.csv'
output_file = 'filtered.csv'
process_csv(input_file, output_file)