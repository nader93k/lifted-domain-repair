"""
Takes the CSV logs (outputs of log_merger.py) and merges them into a single table (main_table.csv by default).
"""

import pandas as pd


domain_shortcuts = {
    'domain-trimmed': 'shorten',
    'zenotravel': 'Zeno',
    'visitall': 'Visit',
    'transport': 'Trans',
    'tpp': 'TPP',
    'tetris': 'Tetris',
    'scanalyzer': 'Scan',
    'satellite': 'Satellite',
    'rovers': 'Rovers',
    'pegsol': 'Pegs',
    'nomystery': 'NoMyst',
    'mystery': 'Myst',
    'mprime': 'MPrime',
    'miconic': 'Miconic',
    'logistics98': 'Logistics',
    'hiking': 'Hike',
    'gripper': 'Gripper',
    'grid': 'Grid',
    'freecell': 'Freecell',
    'elevators': 'Elevs',
    'driverlog': 'Driverlog',
    'depot': 'Depot',
    'blocks': 'BlocksW'
}


def main_table(input_file, order_list):
    
    # Read the CSV file - first let's preserve NA values
    df = pd.read_csv(input_file, na_values=['', 'NA', 'null', 'NULL'])
    
    # Apply both renamings at the start
    df['domain class'] = df['domain class'].map(domain_shortcuts)
    
    # Filter based on error_group criteria - modified to properly handle NA
    df = df[df['error group'].isna() | 
            df['error group'].isin(['time', 'memory'])]
    
    # Calculate metrics
    def calculate_metrics(group):
        # Calculate C metric (completion rate)
        total_rows = len(group)
        successful_rows = len(group[group['goal reached'].astype(str).str.upper().str.strip() == 'TRUE'])
        completion_rate = (successful_rows / total_rows) if total_rows > 0 else None
        completion_abs = successful_rows if total_rows > 0 else None
        
        # Calculate Q metric - modified to properly handle NA
        valid_rows = group[group['search g cost'] >= 0]
        
        if len(valid_rows) > 0:
            equal_and_positive = len(valid_rows[
                (valid_rows['search g cost'] <= valid_rows['vanilla repair length']) & 
                (valid_rows['search g cost'] >= 0)
            ])
            q_metric = (equal_and_positive / len(valid_rows))
        else:
            q_metric = None
            
        # Calculate max_h metric
        max_h = group[pd.to_numeric(group['h_max'], errors='coerce') > float('-inf')]['h_max'].max()

        result = pd.Series({
            'C_rate': round(completion_rate, 2) if completion_rate is not None else None,
            'C_abs': completion_abs,
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
    cols = [*grouping_cols, 'instance_count', 'C_rate', 'C_abs', 'Q', 'max_h']
    result_df = result_df[cols]
    
    result_df['search algorithm'] = pd.Categorical(
        result_df['search algorithm'],
        categories=order_list,
        ordered=True
    )

    result_df = result_df.sort_values(grouping_cols)
    return result_df


def summary_table(main_table):
    grouping_cols = ['grounding method', 'lift_prob', 'search algorithm']
    agg_dict = {
        'instance_count': 'sum',
        'C_rate': 'mean',
        'C_abs': 'sum',
        'Q': 'mean',
        'max_h': 'max'
    }
    summary_df = main_table.groupby(grouping_cols).agg(agg_dict).reset_index()
    float_cols = ['C_rate', 'Q', 'max_h']
    summary_df[float_cols] = summary_df[float_cols].round(2)
    summary_df = summary_df.sort_values(grouping_cols) 
    return summary_df


if __name__ == "__main__":
    folder = '../exp_logs_csv/'
    input_file = folder + 'merged.csv'
    output_main = folder + 'main_table.csv'
    output_summary = folder + 'summary_table.csv'

    order_list = ['UCS', 'A*(FF)', 'A*(UNR)', 'WA*(FF)', 'WA*(UNR)', 'GBFS(FF)', 'GBFS(UNR)', 'DFS']
    
    main_df = main_table(input_file, order_list)
    main_df.to_csv(output_main, index=False)
    print("\nFirst few rows of the main_df:")
    print(main_df.head())

    summary_df = summary_table(main_df)
    summary_df.to_csv(output_summary, index=False)
    print("\nFirst few rows of the summary_df:")
    print(summary_df.head())
