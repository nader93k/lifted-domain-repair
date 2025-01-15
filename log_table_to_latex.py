import pandas as pd
import numpy as np

def process_csv_to_latex(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Start the LaTeX table
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        "    \\begin{tabular}{cccccccccccccccccccccccccc}",  # Removed one c for the eliminated column
        "    \\toprule",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & ",
        "    \\multicolumn{8}{c}{G1} & \\multicolumn{8}{c}{G2} & \\multicolumn{8}{c}{G3} \\\\",
        "    \\cmidrule(lr){3-10} \\cmidrule(lr){11-18} \\cmidrule(lr){19-26}",  # Adjusted column ranges
        "    & & \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} & ",
        "    \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} & ",
        "    \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} \\\\",
        "    \\cmidrule(lr){3-4} \\cmidrule(lr){5-6} \\cmidrule(lr){7-8} \\cmidrule(lr){9-10}",  # Adjusted column ranges
        "    \\cmidrule(lr){11-12} \\cmidrule(lr){13-14} \\cmidrule(lr){15-16} \\cmidrule(lr){17-18}",
        "    \\cmidrule(lr){19-20} \\cmidrule(lr){21-22} \\cmidrule(lr){23-24} \\cmidrule(lr){25-26}",
        "    & & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q \\\\",
        "    \\midrule"
    ]

    # Get unique lift probabilities and domains (sorted in descending order)
    lift_probs = sorted(df['lift_prob'].unique(), reverse=True)
    
    # Process each lift probability
    for i, prob in enumerate(lift_probs):
        prob_df = df[df['lift_prob'] == prob]
        domains = sorted(prob_df['domain class'].unique())
        
        # Process each domain
        for j, domain in enumerate(domains):
            domain_df = prob_df[prob_df['domain class'] == domain]
            instance_count = domain_df['instance_count'].iloc[0]  # Get instance count for this domain
            
            # Format domain name with problem count
            domain_with_count = f"{domain} ({int(instance_count)})"
            
            # Start each row
            if j == 0:
                # First row of a group - include lift probability
                row_str = f"    {prob:.2f} & {domain_with_count}"
            else:
                # Subsequent rows - use multicolumn to skip lift probability
                row_str = f"    \\multicolumn{{1}}{{c}}{{}} & {domain_with_count}"
            
            # Process each grounding method
            for g in ['G1', 'G2', 'G3']:
                # Process each algorithm type in order: UCS, DFS, A*, GBFS
                for alg_base in ['UCS', 'DFS', 'A*_HADD_UNARY_FF', 'GBFS_HADD_UNARY_FF']:
                    # Get the data for this combination
                    data = domain_df[
                        (domain_df['grounding method'] == g) & 
                        (domain_df['search algorithm'] == alg_base)
                    ]
                    
                    if len(data) > 0:
                        c_val = data['C_abs'].iloc[0]
                        q_val = data['Q'].iloc[0]
                        
                        c_str = f"{int(c_val)}" if pd.notna(c_val) else "-"
                        q_str = f"{q_val:.1f}" if pd.notna(q_val) else "-"
                    else:
                        c_str = "-"
                        q_str = "-"
                    
                    row_str += f" & {c_str} & {q_str}"
            
            row_str += " \\\\"
            latex_content.append(row_str)
            
        # Add midrule between lift probability groups (except after the last group)
        if i < len(lift_probs) - 1:
            latex_content.append("    \\midrule")

    # Add final lines
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. G1: removing absent preconditions, G2: removing negative preconditions and delete-relaxation, G3: all groundings. C and Q mean coverage and quality, respectively.}",
        "    \\label{tab:search_algorithms}",
        "\\end{table*}"
    ])

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex_content))

# Example usage
if __name__ == "__main__":
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'
    csv_table = folder + 'main_table.csv'
    output = folder + 'main_table.tex'
    process_csv_to_latex(csv_table, output)