import pandas as pd
import numpy as np

def process_csv_to_latex(main_df, summary_df, alg_order_list, output_file, caption="Search Algorithm Performance Comparison"):
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
            
            if prob.is_integer(): formatted_prob = str(int(prob))
            else: formatted_prob = f"{prob:.2f}".lstrip('0')

            row_str = f"    {formatted_prob} & {domain_with_count}" if j == 0 else f"    \\multicolumn{{1}}{{c}}{{}} & {domain_with_count}"
            
            # Collect all valid C and Q values for this row
            c_values = []
            q_values = []
            row_data = []
            
            # First pass: collect all values
            for g in grounding_methods:
                for alg_base in search_algorithms:
                    data = domain_df[
                        (domain_df['grounding method'] == g) & 
                        (domain_df['search algorithm'] == alg_base)
                    ]
                    
                    if len(data) > 0:
                        c_val = data['C_abs'].iloc[0]
                        q_val = data['Q'].iloc[0]
                        if pd.notna(c_val):
                            c_values.append(c_val)
                        if pd.notna(q_val):
                            q_values.append(q_val)
                    row_data.append((data, g, alg_base))
            
            # Find maximum values
            max_c = max(c_values) if c_values else None
            max_q = max(q_values) if q_values else None
            
            # Second pass: format values
            for data, g, alg_base in row_data:
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    q_val = data['Q'].iloc[0]
                    
                    # Format C value
                    if pd.notna(c_val):
                        c_str = str(int(c_val))
                        if max_c is not None and c_val == max_c:
                            c_str = f"\\textbf{{{c_str}}}"
                    else:
                        c_str = "-"
                    
                    # Format Q value
                    if pd.notna(q_val):
                        if q_val.is_integer():
                            q_str = str(int(q_val))
                        else:
                            q_str = f"{q_val:.2f}".lstrip('0')
                        if max_q is not None and abs(q_val - max_q) < 1e-10:  # Using small epsilon for float comparison
                            q_str = f"\\textbf{{{q_str}}}"
                    else:
                        q_str = "-"
                else:
                    c_str = "-"
                    q_str = "-"
                
                row_str += f" & {c_str} & {q_str}"
            
            row_str += " \\\\"
            latex_content.append(row_str)
        
        # Add midrule before summary rows
        latex_content.append(f"    \\cmidrule(l){{2-{total_data_cols+2}}}")
        
        # Add two summary rows - one for SUM(C) and one for AVG(Q)
        summary_row = summary_df[summary_df['lift_prob'] == prob]
        
        # First row: SUM(C)
        row_str = "    \\multicolumn{1}{c}{} & \\textbf{SUM(C)}"
        for g in grounding_methods:
            for alg_base in search_algorithms:
                data = summary_row[
                    (summary_row['grounding method'] == g) & 
                    (summary_row['search algorithm'] == alg_base)
                ]
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    c_str = f"\\textbf{{{int(c_val)}}}" if pd.notna(c_val) else "-"
                else:
                    c_str = "-"
                
                # Only add C value and a blank space for Q
                row_str += f" & {c_str} & "
        
        row_str += " \\\\"
        latex_content.append(row_str)
        
        # Second row: AVG(Q)
        row_str = "    \\multicolumn{1}{c}{} & \\textbf{AVG(Q)}"
        for g in grounding_methods:
            for alg_base in search_algorithms:
                data = summary_row[
                    (summary_row['grounding method'] == g) & 
                    (summary_row['search algorithm'] == alg_base)
                ]
                if len(data) > 0:
                    q_val = data['Q'].iloc[0]
                    if pd.notna(q_val):
                        if q_val.is_integer():
                            formatted_num = str(int(q_val))
                        else:
                            formatted_num = f"{q_val:.2f}".lstrip('0')
                        q_str = f"\\textbf{{{formatted_num}}}"
                    else:
                        q_str = "\\textbf{-}"
                else:
                    q_str = "-"
                
                # Add blank space for C and then Q value
                row_str += f" &  & {q_str}"
        
        row_str += " \\\\"
        latex_content.append(row_str)
        
        if i < len(lift_probs) - 1:
            latex_content.append("    \\midrule")
    
    # Add table footer with caption parameter
    latex_content.extend([
        "    \\bottomrule",
        "    \\end{tabular}",
        f"    \\caption{{{caption}. C and Q mean coverage and quality, respectively.}}",
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
    alg_order_list = ['UCS', 'A*_FF', 'GBFS_FF', 'DFS']
    process_csv_to_latex(main_df, summary_df, alg_order_list, output)