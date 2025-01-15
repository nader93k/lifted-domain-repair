import pandas as pd
import numpy as np


def process_csv_to_latex(main_df, summary_df, output_file):
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        "    \\begin{tabular}{cccccccccccccccccccccccccc}",
        "    \\toprule",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & ",
        "    \\multicolumn{8}{c}{G1} & \\multicolumn{8}{c}{G2} & \\multicolumn{8}{c}{G3} \\\\",
        "    \\cmidrule(lr){3-10} \\cmidrule(lr){11-18} \\cmidrule(lr){19-26}",
        "    & & \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} & ",
        "    \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} & ",
        "    \\multicolumn{2}{c}{UCS} & \\multicolumn{2}{c}{DFS} & \\multicolumn{2}{c}{A*} & \\multicolumn{2}{c}{GBFS} \\\\",
        "    \\cmidrule(lr){3-4} \\cmidrule(lr){5-6} \\cmidrule(lr){7-8} \\cmidrule(lr){9-10}",
        "    \\cmidrule(lr){11-12} \\cmidrule(lr){13-14} \\cmidrule(lr){15-16} \\cmidrule(lr){17-18}",
        "    \\cmidrule(lr){19-20} \\cmidrule(lr){21-22} \\cmidrule(lr){23-24} \\cmidrule(lr){25-26}",
        "    & & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q & C & Q \\\\",
        "    \\midrule"
    ]

    lift_probs = sorted(main_df['lift_prob'].unique(), reverse=True)
    
    for i, prob in enumerate(lift_probs):
        prob_df = main_df[main_df['lift_prob'] == prob]
        domains = sorted(main_df['domain class'].unique())
        
        # Process domains as before
        for j, domain in enumerate(domains):
            domain_df = prob_df[prob_df['domain class'] == domain]
            instance_count = domain_df['instance_count'].iloc[0]
            domain_with_count = f"{domain} ({int(instance_count)})"
            
            row_str = f"    {prob:.2f} & {domain_with_count}" if j == 0 else f"    \\multicolumn{{1}}{{c}}{{}} & {domain_with_count}"
            
            for g in ['G1', 'G2', 'G3']:
                for alg_base in ['UCS', 'DFS', 'A*_HADD_UNARY_FF', 'GBFS_HADD_UNARY_FF']:
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
        
        # Add summary row after all domains for this lift probability
        summary_row = summary_df[summary_df['lift_prob'] == prob]
        row_str = "    \\multicolumn{1}{c}{} & \\textbf{Total}"
        
        for g in ['G1', 'G2', 'G3']:
            for alg_base in ['UCS', 'DFS', 'A*_HADD_UNARY_FF', 'GBFS_HADD_UNARY_FF']:
                data = summary_row[
                    (summary_row['grounding method'] == g) & 
                    (summary_row['search algorithm'] == alg_base)
                ]
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    q_val = data['Q'].iloc[0]
                    c_str = f"\\textbf{{{int(c_val)}}}" if pd.notna(c_val) else "-"
                    q_str = f"\\textbf{{{q_val:.1f}}}" if pd.notna(q_val) else "-"
                else:
                    c_str = "-"
                    q_str = "-"
                
                row_str += f" & {c_str} & {q_str}"
        
        row_str += " \\\\"
        latex_content.append(row_str)
        
        if i < len(lift_probs) - 1:
            latex_content.append("    \\midrule")

    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. G1: removing absent preconditions, G2: removing negative preconditions and delete-relaxation, G3: all groundings. C and Q mean coverage and quality, respectively.}",
        "    \\label{tab:search_algorithms}",
        "\\end{table*}"
    ])

    with open(output_file, 'w') as f:
        f.write('\n'.join(latex_content))

# Example usage
if __name__ == "__main__":
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'
    main_table = folder + 'main_table.csv'
    main_df = pd.read_csv(main_table)
    summary_table = folder + 'summary_table.csv'
    summary_df = pd.read_csv(summary_table)

    output = folder + 'main_table.tex'
    process_csv_to_latex(main_df, summary_df, output)
