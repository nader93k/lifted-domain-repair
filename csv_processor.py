import pandas as pd
import numpy as np
import re

def process_csv(input_file, output_file, columns_to_include):
    # Read the CSV file, treating all columns as strings initially
    df = pd.read_csv(input_file, dtype=str, quotechar='"', escapechar='\\', on_bad_lines='warn')

    # Replace underscores with spaces in column names
    df.columns = df.columns.str.replace('_', ' ')

    # Update columns_to_include list to replace underscores with spaces
    columns_to_include = [col.replace('_', ' ') for col in columns_to_include]

    # Print column names
    print("Columns in the CSV file:")
    print(df.columns.tolist())

    # Handle 'results exists' column
    if 'results exists' in df.columns:
        df['results exists'] = df['results exists'].map({'True': True, 'False': False})

    # Handle 'result g cost' column
    if 'result g cost' in df.columns:
        df['result g cost'] = pd.to_numeric(df['result g cost'], errors='coerce')
        df = df.sort_values(by='result g cost', ascending=False)
    else:
        print("Warning: 'result g cost' column not found. Skipping sorting step.")

    # Function to count matching entries
    def count_matching_entries(str1, str2):
        if pd.isna(str1) or pd.isna(str2):
            return 0
        set1 = set(str(str1).split('\n'))
        set2 = set(str(str2).split('\n'))
        return len(set1.intersection(set2))

    # Add new column counting matching entries if required columns exist
    if 'str ground repair' in df.columns and 'result repair set' in df.columns:
        df['matching entries count'] = df.apply(lambda row: count_matching_entries(row['str ground repair'], row['result repair set']), axis=1)
    else:
        print("Warning: 'str ground repair' or 'result repair set' column not found. Skipping matching entries count.")

    # Ensure 'str ground repair' is properly handled
    if 'str ground repair' in df.columns:
        df['str ground repair'] = df['str ground repair'].apply(lambda x: str(x) if pd.notna(x) else '')

    # Extract run time in seconds with improved handling
    if 'run time' in df.columns:
        def extract_seconds(time_val):
            if pd.isna(time_val):
                return np.nan
            
            # If it's already a numeric value, try to convert directly
            try:
                return float(time_val)
            except (ValueError, TypeError):
                # If it's a string, try to extract seconds using regex
                if isinstance(time_val, str):
                    match = re.search(r'=\s*([\d.]+)\s*seconds', time_val)
                    return float(match.group(1)) if match else np.nan
                return np.nan
        
        df['run secs'] = df['run time'].apply(extract_seconds)
    else:
        print("Warning: 'run time' column not found. Skipping run time extraction.")

    # Remove any columns that might have been added due to inconsistent data
    df = df[df.columns[~df.columns.str.contains('Unnamed')]]
    
    # Filter the DataFrame to include only the specified columns (if they exist)
    existing_columns = [col for col in columns_to_include if col in df.columns]
    if 'run secs' in df.columns and 'run secs' not in existing_columns:
        existing_columns.append('run secs')
    
    df_output = df[existing_columns]

    # Save the result to a new CSV file
    df_output.to_csv(output_file, index=False, quoting=1)  # quoting=1 ensures all fields are quoted

    print(f"Processed data saved to {output_file}")

# Usage
input_file = 'results.csv'
output_file = 'filtered.csv'
columns_to_include = [
    'file name',
    'problem name',
    'plan length',
    'num ground repair',
    'run secs',
    'iteration max',
    'branching factor avg',
    'results exists',
    'result g cost',
    'result h cost',
    'result f cost',
    'fringe size max',
    'num neighbours sum'
]
process_csv(input_file, output_file, columns_to_include)