import pandas as pd
import argparse

def safe_float_convert(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def create_latex_table(csv_path, output_path):
    # Read the CSV file and convert numeric columns to float
    df = pd.read_csv(csv_path)
    numeric_columns = ['lift_prob', 'instance_count', 
                      'astar_C', 'astar_Q', 'bfs_C', 'bfs_Q', 'dfs_C', 'dfs_Q']
    
    for col in numeric_columns:
        df[col] = df[col].apply(safe_float_convert)
    
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
                    # Add data for each algorithm in order: ucs, dfs, a*, grd
                    row_data.extend([
                        f"{safe_float_convert(df_method['bfs_C'].iloc[0]):.1f}",
                        f"{safe_float_convert(df_method['bfs_Q'].iloc[0]):.1f}",
                        f"{safe_float_convert(df_method['dfs_C'].iloc[0]):.1f}",
                        f"{safe_float_convert(df_method['dfs_Q'].iloc[0]):.1f}",
                        f"{safe_float_convert(df_method['astar_C'].iloc[0]):.1f}",
                        f"{safe_float_convert(df_method['astar_Q'].iloc[0]):.1f}",
                        "0.0", "0.0"  # Placeholder for grd values
                    ])
                else:
                    # Add empty values if no data for this method
                    row_data.extend(["0.0"] * 8)
            
            # Add empty values for G3 (all 0s as placeholder)
            row_data.extend(["0.0"] * 8)
            
            # Add the row to latex content
            latex_content.append("    " + " & ".join(row_data) + " \\\\")
        
        # Add midrule between lift probability sections
        latex_content.append("    \\midrule")

    # Add table footer
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. G1: removing absent preconditions, G2: removing negative preconditions and delete-relaxation, G3: all groundings. C and Q mean coverage and quality, respectively.}",
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