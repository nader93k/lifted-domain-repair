import pandas as pd
import numpy as np

def process_csv_to_latex(main_df, summary_df, alg_order_list, output_file):
    # Get unique values from dataframes
    grounding_methods = sorted(main_df['grounding method'].unique())
    search_algorithms = alg_order_list
    
    # Calculate number of columns needed
    num_metric_cols = 2  # C and Q
    num_alg_cols = len(search_algorithms)
    num_g_cols = len(grounding_methods)
    total_data_cols = num_metric_cols * num_alg_cols * num_g_cols
    
    # Create column specification
    col_spec = "cc" + "c" * total_data_cols
    
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        f"    \\begin{{tabular}}{{{col_spec}}}",
        "    \\toprule",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
        "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & "
    ]
    
    # Add grounding method headers
    g_method_header = []
    for g in grounding_methods:
        cols = num_metric_cols * num_alg_cols
        g_method_header.append(f"\\multicolumn{{{cols}}}{{c}}{{{g}}}")
    latex_content.append("    " + " & ".join(g_method_header) + " \\\\")
    
    # Add cmidrule separators for grounding methods
    cmidrules = []
    start_col = 3  # First two columns are L. Prob and Domain
    for _ in grounding_methods:
        end_col = start_col + (num_metric_cols * num_alg_cols) - 1
        cmidrules.append(f"\\cmidrule(lr){{{start_col}-{end_col}}}")
        start_col = end_col + 1
    latex_content.append("    " + " ".join(cmidrules))
    
    # Add algorithm headers
    alg_header = []
    for g in grounding_methods:
        for alg in search_algorithms:
            # Strip any suffixes for display (e.g., "_HADD_UNARY_FF")
            display_name = alg.split('_')[0]
            alg_header.append(f"\\multicolumn{{2}}{{c}}{{{display_name}}}")
    latex_content.append("    & & " + " & ".join(alg_header) + " \\\\")
    
    # Add cmidrules for algorithms
    cmidrules = []
    col = 3
    for _ in range(len(grounding_methods) * len(search_algorithms)):
        cmidrules.append(f"\\cmidrule(lr){{{col}-{col+1}}}")
        col += 2
    latex_content.append("    " + " ".join(cmidrules))
    
    # Add C/Q headers
    metrics_header = ["C & Q"] * (len(grounding_methods) * len(search_algorithms))
    latex_content.append("    & & " + " & ".join(metrics_header) + " \\\\")
    latex_content.append("    \\midrule")
    
    # Process data rows
    lift_probs = sorted(main_df['lift_prob'].unique(), reverse=True)
    domains = sorted(main_df['domain class'].unique())
    
    for i, prob in enumerate(lift_probs):
        prob_df = main_df[main_df['lift_prob'] == prob]
        
        for j, domain in enumerate(domains):
            domain_df = prob_df[prob_df['domain class'] == domain]
            instance_count = domain_df['instance_count'].iloc[0] if len(domain_df) > 0 else 0
            domain_with_count = f"{domain} ({int(instance_count)})"
            
            row_str = f"    {prob:.2f} & {domain_with_count}" if j == 0 else f"    \\multicolumn{{1}}{{c}}{{}} & {domain_with_count}"
            
            for g in grounding_methods:
                for alg_base in search_algorithms:
                    data = domain_df[
                        (domain_df['grounding method'] == g) & 
                        (domain_df['search algorithm'] == alg_base)
                    ]
                    
                    if len(data) > 0:
                        c_val = data['C_abs'].iloc[0]
                        q_val = data['Q'].iloc[0]
                        c_str = f"{int(c_val)}" if pd.notna(c_val) else "-"
                        q_str = str(int(q_val)) if pd.notna(q_val) and q_val.is_integer() else f"{q_val:.2f}".lstrip('0') if pd.notna(q_val) else "-"
                    else:
                        c_str = "-"
                        q_str = "-"
                    
                    row_str += f" & {c_str} & {q_str}"
            
            row_str += " \\\\"
            latex_content.append(row_str)
        
        # Add midrule before summary row
        latex_content.append(f"    \\cmidrule(l){{2-{total_data_cols+2}}}")
        
        # Add summary row
        summary_row = summary_df[summary_df['lift_prob'] == prob]
        row_str = "    \\multicolumn{1}{c}{} & \\textbf{Total}"
        
        for g in grounding_methods:
            for alg_base in search_algorithms:
                data = summary_row[
                    (summary_row['grounding method'] == g) & 
                    (summary_row['search algorithm'] == alg_base)
                ]
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    q_val = data['Q'].iloc[0]
                    c_str = f"\\textbf{{{int(c_val)}}}" if pd.notna(c_val) else "-"
                    if pd.notna(q_val):
                        if q_val.is_integer():
                            formatted_num = str(int(q_val))
                        else:
                            formatted_num = f"{q_val:.2f}".lstrip('0')
                        
                        q_str = f"\\textbf{{{formatted_num}}}"
                    else:
                        q_str = "\\textbf{-}"
                else:
                    c_str = "-"
                    q_str = "-"
                
                row_str += f" & {c_str} & {q_str}"
        
        row_str += " \\\\"
        latex_content.append(row_str)
        
        if i < len(lift_probs) - 1:
            latex_content.append("    \\midrule")
    
    # Add table footer
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        "    \\caption{Search Algorithm Performance Comparison. " + 
        ", ".join([f"{g}: {g_desc}" for g, g_desc in get_grounding_descriptions(grounding_methods).items()]) +
        ". C and Q mean coverage and quality, respectively.}",
        "    \\label{tab:search_algorithms}",
        "\\end{table*}"
    ])
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex_content))

def get_grounding_descriptions(grounding_methods):
    """Returns descriptions for grounding methods"""
    descriptions = {
        'G1': 'removing absent preconditions',
        'G2': 'removing negative preconditions and delete-relaxation',
        'G3': 'all groundings'
    }
    return {g: descriptions.get(g, g) for g in grounding_methods}

# Example usage
if __name__ == "__main__":
    folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'
    main_table = folder + 'main_table.csv'
    main_df = pd.read_csv(main_table)
    summary_table = folder + 'summary_table.csv'
    summary_df = pd.read_csv(summary_table)

    output = folder + 'main_table.tex'
    alg_order_list = ['UCS', 'A*_FF', 'GBFS_FF', 'DFS']
    process_csv_to_latex(main_df, summary_df, alg_order_list, output)
