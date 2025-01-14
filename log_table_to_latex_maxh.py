import pandas as pd
import argparse

def safe_float_convert(value):
    if pd.isna(value) or value == '-':
        return '-'  # Keep missing values as '-'
    try:
        float_val = float(value)
        return float_val if float_val != 0 else '-'  # Convert actual 0s to '-' as well
    except (ValueError, TypeError):
        return '-'

def create_latex_table(csv_path, output_path):
    # Read the CSV file with appropriate parsing settings
    df = pd.read_csv(csv_path, na_values=['-', 'NA', 'null', 'NULL'])
    
    # Define columns we care about - now only astar_max_h for heuristic
    numeric_columns = ['lift_prob', 'instance_count', 'astar_max_h']
    
    for col in numeric_columns:
        df[col] = df[col].apply(safe_float_convert)
    
    # Create the table header
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        "    \\begin{tabular}{ccccccccccc}",  # Reduced columns since h_max only for A*
        "    \\toprule",
        "    \\multirow{3}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
        "    \\multirow{3}{*}{\\rotatebox[origin=c]{90}{Domain}} & ",
        "    \\multirow{3}{*}{\\rotatebox[origin=c]{90}{Problems}} & ",
        "    \\multicolumn{2}{c}{G1} & \\multicolumn{2}{c}{G2} & \\multicolumn{2}{c}{G3} \\\\",
        "    \\cmidrule(lr){4-5} \\cmidrule(lr){6-7} \\cmidrule(lr){8-9}",
        "    & & & a* & h\\_max & a* & h\\_max & a* & h\\_max \\\\"
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
            for method in ['G1', 'G2', 'G3']:
                df_method = df_domain[df_domain['grounding method'] == method]
                if not df_method.empty:
                    # Add A* data and h_max
                    h_max = df_method['astar_max_h'].iloc[0]
                    row_data.extend([
                        "-",  # placeholder for A* metric
                        f"{h_max:.1f}" if h_max != '-' else '-'
                    ])
                else:
                    # Add dashes for missing data
                    row_data.extend(['-', '-'])
            
            # Add the row to latex content
            latex_content.append("    " + " & ".join(row_data) + " \\\\")
        
        # Add midrule between lift probability sections
        latex_content.append("    \\midrule")

    # Add table footer
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. G1: removing absent preconditions, G2: removing negative preconditions and delete-relaxation, G3: all groundings. h\\_max represents the maximum heuristic value encountered during A* search.}",
        "    \\label{tab:search_algorithms}",
        "\\end{table*}"
    ])

    # Write to output file
    with open(output_path, 'w') as f:
        f.write('\n'.join(latex_content))

def main():
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'

    csv_table = folder + 'main_table.csv'
    output = folder + 'max_h_table.tex'
    
    create_latex_table(csv_table, output)
    print(f"LaTeX table has been written to {output}")

if __name__ == "__main__":
    main()