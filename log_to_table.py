import pandas as pd
import sys

def analyze_csv(input_file, output_file):
    # Read the CSV file - first let's preserve NA values
    df = pd.read_csv(input_file, na_values=['', 'NA', 'null', 'NULL'])
    
    # Filter based on error_group criteria - modified to properly handle NA
    df = df[df['error group'].isna() | 
            df['error group'].isin(['time', 'memory'])]
    
    # Calculate metrics
    def calculate_metrics(group):
        # Calculate C metric (completion rate)
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
            
        return pd.Series({
            'C': round(completion_rate, 2) if completion_rate else None,
            'Q': round(q_metric, 2) if q_metric else None,
            'max_h': round(max_h, 2) if max_h else None
        })
    
    # Group and calculate metrics
    grouped = df.groupby(['lift_prob', 'domain class', 'grounding method', 'search algorithm']).apply(calculate_metrics)
    grouped = grouped.reset_index()
    
    instance_counts = df.groupby(['lift_prob', 'domain class'])['instance id'].nunique().reset_index(name='instance_count')
    
    # Create pivot tables for all metrics
    pivot_c = pd.pivot_table(
        grouped,
        values='C',
        index=['lift_prob', 'domain class', 'grounding method'],
        columns=['search algorithm'],
        fill_value=None
    )
    
    pivot_q = pd.pivot_table(
        grouped,
        values='Q',
        index=['lift_prob', 'domain class', 'grounding method'],
        columns=['search algorithm'],
        fill_value=None
    )
    
    pivot_h = pd.pivot_table(
        grouped,
        values='max_h',
        index=['lift_prob', 'domain class', 'grounding method'],
        columns=['search algorithm'],
        fill_value=None
    )

    algorithms = pivot_c.columns
    result_df = pd.DataFrame(index=pivot_c.index)
    
    for algo in algorithms:
        result_df[f'{algo}_C'] = pivot_c[algo]
        result_df[f'{algo}_Q'] = pivot_q[algo]
        result_df[f'{algo}_max_h'] = pivot_h[algo] if algo in pivot_h.columns else None
    
    # Reset index to make lift_prob, domain_class, and grounding_method regular columns
    result_df = result_df.reset_index()
    
    # Merge with instance counts
    result_df = result_df.merge(instance_counts, on=['lift_prob', 'domain class'])
    
    # Reorder columns to put instance_count after domain class and grounding method before search algorithm metrics
    cols = result_df.columns.tolist()
    metric_cols = [col for col in cols if col not in ['lift_prob', 'domain class', 'grounding method', 'instance_count']]
    new_cols = ['lift_prob', 'domain class', 'instance_count', 'grounding method'] + metric_cols
    result_df = result_df[new_cols]
    
    # Sort by lift_prob, domain_class, and grounding_method
    result_df = result_df.sort_values(['lift_prob', 'domain class', 'grounding method'])
    
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
        sys.exit(1)