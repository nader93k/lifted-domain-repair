import pandas as pd

def analyze_csv(input_file, output_file):
    # Read the CSV file - first let's preserve NA values
    df = pd.read_csv(input_file, na_values=['', 'NA', 'null', 'NULL'])
    
    # Filter based on error_group criteria - modified to properly handle NA
    df = df[df['error group'].isna() | 
            df['error group'].isin(['time', 'memory'])]
    
    # Calculate metrics
    def calculate_metrics(group):
        # Calculate C metric (completion rate)
        # total_rows = len(group[group['vanilla repair length'] >= 0])
        total_rows = len(group)
        successful_rows = len(group[group['goal reached'].astype(str).str.upper().str.strip() == 'TRUE'])
        completion_rate = (successful_rows / total_rows * 100) if total_rows > 0 else None
        
        # Calculate Q metric - modified to properly handle NA
        valid_rows = group[group['search g cost'] >= 0]
        
        if len(valid_rows) > 0:
            equal_and_positive = len(valid_rows[
                (valid_rows['search g cost'] == valid_rows['vanilla repair length']) & 
                (valid_rows['search g cost'] >= 0)
            ])
            q_metric = (equal_and_positive / len(valid_rows) * 100)
        else:
            q_metric = None
            
        # Calculate max_h metric
        max_h = group[pd.to_numeric(group['h_max'], errors='coerce') > float('-inf')]['h_max'].max()

        result = pd.Series({
            'C': round(completion_rate, 2) if completion_rate is not None else None,
            'Q': round(q_metric, 2) if q_metric is not None else None,
            'max_h': round(max_h, 2) if max_h is not None else None
        })
            
        return result
    
    grouping_cols = ['grounding method', 'lift_prob', 'search algorithm', 'domain class']
    
    result_df = df.groupby(grouping_cols).apply(calculate_metrics)
    result_df = result_df.reset_index()
    
    # Add instance counts
    instance_counts = df.groupby(grouping_cols)['instance id'].nunique().reset_index(name='instance_count')
    result_df = result_df.merge(instance_counts, on=grouping_cols)
    
    # Reorder columns
    cols = [*grouping_cols, 'instance_count', 'C', 'Q', 'max_h']
    result_df = result_df[cols]
    
    # Sort the dataframe
    result_df = result_df.sort_values(grouping_cols)
    
    # Save to CSV
    result_df.to_csv(output_file, index=False)
    return result_df

if __name__ == "__main__":
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'
    input_file = folder + 'merged.csv'
    output_file = folder + 'main_table.csv'
    
    try:
        result_df = analyze_csv(input_file, output_file)
        print(f"Analysis complete. Results saved to {output_file}")
        print("\nFirst few rows of the result:")
        print(result_df.head())
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
