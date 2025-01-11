import pandas as pd
import numpy as np

def safe_float_convert(value):
    if pd.isna(value) or value == '-':
        return '-'
    try:
        float_val = float(value)
        return float_val if float_val != 0 else '-'
    except (ValueError, TypeError):
        return '-'

def find_highest_c_values(row):
    """Find the highest C value among algorithms for a single row."""
    c_values = {
        'ucs': safe_float_convert(row['bfs_C']),
        'dfs': safe_float_convert(row['dfs_C']),
        'astar': safe_float_convert(row['astar_C'])
    }
    
    # Filter out '-' values
    valid_values = {k: v for k, v in c_values.items() if v != '-'}
    
    if not valid_values:
        return {}
        
    max_value = max(valid_values.values())
    return {k: (v == max_value) for k, v in valid_values.items()}

def format_value_with_bold(value, is_bold):
    """Format a value with boldface if needed."""
    if value == '-':
        return '-'
    try:
        float_val = float(value)
        formatted = f"{float_val:.1f}"
        return f"\\textbf{{{formatted}}}" if is_bold else formatted
    except (ValueError, TypeError):
        return '-'

def create_latex_table(csv_path, output_path):
    # Read the CSV file
    df = pd.read_csv(csv_path, na_values=['-', 'NA', 'null', 'NULL'])
    
    # Create the table header
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        "    \\begin{tabular}{ccccccccccccccccccccccccccc}",
        "    \\toprule",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & ",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Problems}} & ",
        "    \\multicolumn{8}{c}{G1} & \\multicolumn{8}{c}{G2} & \\multicolumn{8}{c}{G3} \\\\",
        "    \\cmidrule(lr){4-11} \\cmidrule(lr){12-19} \\cmidrule(lr){20-27}",
        "    & & & \\multicolumn{2}{c}{ucs} & \\multicolumn{2}{c}{dfs} & \\multicolumn{2}{c}{a*} & \\multicolumn{2}{c}{grd} & ",
        "    \\multicolumn{2}{c}{ucs} & \\multicolumn{2}{c}{dfs} & \\multicolumn{2}{c}{a*} & \\multicolumn{2}{c}{grd} & ",
        "    \\multicolumn{2}{c}{ucs} & \\multicolumn{2}{c}{dfs} & \\multicolumn{2}{c}{a*} & \\multicolumn{2}{c}{grd} \\\\",
        "    \\cmidrule(lr){4-5} \\cmidrule(lr){6-7} \\cmidrule(lr){8-9} \\cmidrule(lr){10-11}",
        "    \\cmidrule(lr){12-13} \\cmidrule(lr){14-15} \\cmidrule(lr){16-17} \\cmidrule(lr){18-19}",
        "    \\cmidrule(lr){20-21} \\cmidrule(lr){22-23} \\cmidrule(lr){24-25} \\cmidrule(lr){26-27}",
        "    & & & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q \\\\"
    ]

    # Add midrule
    latex_content.append("    \\midrule")

    # Process data for each lift probability
    for lift_prob in sorted(df['lift_prob'].unique(), reverse=True):
        df_prob = df[df['lift_prob'] == lift_prob]
        
        # Process each domain for current lift probability
        for domain in sorted(df_prob['domain class'].unique()):
            df_domain = df_prob[df_prob['domain class'] == domain]
            instance_count = int(df_domain['instance_count'].iloc[0])
            
            # Create row content
            row_data = []
            
            # Add lift probability (only for first domain)
            row_data.append(f"{lift_prob:.2f}" if domain == sorted(df_prob['domain class'].unique())[0] else "")
            
            # Add domain and instance count
            row_data.extend([domain, str(instance_count)])
            
            # Process data for each grounding method
            for method in ['G1', 'G2']:
                df_method = df_domain[df_domain['grounding method'] == method]
                if not df_method.empty:
                    # Find highest C values for this row
                    highest_c = find_highest_c_values(df_method.iloc[0])
                    
                    # Add data for each algorithm
                    c_q_pairs = [
                        ('bfs_C', 'bfs_Q', 'ucs'),    # ucs
                        ('dfs_C', 'dfs_Q', 'dfs'),    # dfs
                        ('astar_C', 'astar_Q', 'astar'), # a*
                        ('-', '-', 'grd')              # grd
                    ]
                    
                    for c_metric, q_metric, alg_name in c_q_pairs:
                        if c_metric == '-':
                            row_data.extend(['-', '-'])
                        else:
                            c_val = df_method[c_metric].iloc[0]
                            q_val = df_method[q_metric].iloc[0]
                            
                            # Format C value with bold if it's the highest
                            is_bold = highest_c.get(alg_name, False)
                            c_formatted = format_value_with_bold(c_val, is_bold)
                            q_formatted = format_value_with_bold(q_val, False)
                            
                            row_data.extend([c_formatted, q_formatted])
                else:
                    # Add dashes for missing data
                    row_data.extend(['-'] * 8)
            
            # Add dashes for G3
            row_data.extend(['-'] * 8)
            
            # Add the row to latex content
            latex_content.append("    " + " & ".join(row_data) + " \\\\")
        
        # Add midrule between lift probability sections
        latex_content.append("    \\midrule")

    # Add table footer
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. G1: removing absent preconditions, G2: removing negative preconditions and delete-relaxation, G3: all groundings. C and Q mean coverage and quality, respectively. Bold values indicate highest coverage within each grounding method.}",
        "    \\label{tab:search_algorithms}",
        "\\end{table*}"
    ])

    # Write to output file
    with open(output_path, 'w') as f:
        f.write('\n'.join(latex_content))

def main():
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'
    csv_table = folder + 'main_table.csv'
    output = folder + 'main_table.tex'
    create_latex_table(csv_table, output)
    print(f"LaTeX table has been written to {output}")

if __name__ == "__main__":
    main()