import pandas as pd
import numpy as np

def process_csv_to_latex(main_df, summary_df, alg_order_list, output_file, caption="Search Algorithm Performance Comparison", include_liftprob=False):
    # Get unique values from dataframes
    grounding_methods = sorted(main_df['grounding method'].unique())
    search_algorithms = alg_order_list
    
    # Calculate number of columns needed
    num_metric_cols = 2  # C and Q
    num_alg_cols = len(search_algorithms)
    num_g_cols = len(grounding_methods)
    total_data_cols = num_metric_cols * num_alg_cols * num_g_cols
    
    # Create column specification based on whether lift_prob is included
    col_spec = "c" * (2 if not include_liftprob else 3) + "c" * total_data_cols
    
    latex_content = [
        "\\begin{table*}",
        "    \\centering",
        f"    \\begin{{tabular}}{{{col_spec}}}",
        "    \\toprule"
    ]
    
    # Add initial column headers conditionally
    if include_liftprob:
        latex_content.extend([
            "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{L. Prob.}} & ",
            "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & "
        ])
    else:
        latex_content.append(
            "    \\multirow{4}{*}{\\rotatebox[origin=c]{90}{Domain}} & "
        )
    
    # Add grounding method headers
    g_method_header = []
    for g in grounding_methods:
        cols = num_metric_cols * num_alg_cols
        g_method_header.append(f"\\multicolumn{{{cols}}}{{c}}{{{g}}}")
    latex_content.append("    " + " & ".join(g_method_header) + " \\\\")
    
    # Add cmidrule separators for grounding methods
    cmidrules = []
    start_col = 2 if not include_liftprob else 3  # Adjust starting column based on include_liftprob
    for _ in grounding_methods:
        end_col = start_col + (num_metric_cols * num_alg_cols) - 1
        cmidrules.append(f"\\cmidrule(lr){{{start_col}-{end_col}}}")
        start_col = end_col + 1
    latex_content.append("    " + " ".join(cmidrules))
    
    # Add algorithm headers
    alg_header = []
    for g in grounding_methods:
        for alg in search_algorithms:
            display_name = alg.split('_')[0]
            alg_header.append(f"\\multicolumn{{2}}{{c}}{{{display_name}}}")
    latex_content.append("    " + ("& " if not include_liftprob else "& & ") + " & ".join(alg_header) + " \\\\")
    
    # Add cmidrules for algorithms
    cmidrules = []
    col = 2 if not include_liftprob else 3
    for _ in range(len(grounding_methods) * len(search_algorithms)):
        cmidrules.append(f"\\cmidrule(lr){{{col}-{col+1}}}")
        col += 2
    latex_content.append("    " + " ".join(cmidrules))
    
    # Add C/Q headers
    metrics_header = ["C & Q"] * (len(grounding_methods) * len(search_algorithms))
    latex_content.append("    " + ("& " if not include_liftprob else "& & ") + " & ".join(metrics_header) + " \\\\")
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
            
            # Format row start based on include_liftprob
            if include_liftprob:
                formatted_prob = str(int(prob)) if prob.is_integer() else f"{prob:.1f}".lstrip('0')
                row_str = f"    {formatted_prob} & {domain_with_count}" if j == 0 else f"    \\multicolumn{{1}}{{c}}{{}} & {domain_with_count}"
            else:
                row_str = f"    {domain_with_count}"
            
            # Rest of the row processing remains the same
            c_values = []
            q_values = []
            row_data = []
            
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
            
            max_c = max(c_values) if c_values else None
            max_q = max(q_values) if q_values else None
            
            for data, g, alg_base in row_data:
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    q_val = data['Q'].iloc[0]
                    
                    if pd.notna(c_val):
                        c_str = str(int(c_val))
                        if max_c is not None and c_val == max_c:
                            c_str = f"\\textbf{{{c_str}}}"
                    else:
                        c_str = "-"
                    
                    if pd.notna(q_val):
                        if q_val.is_integer():
                            q_str = str(int(q_val))
                        else:
                            q_str = f"{q_val:.1f}".lstrip('0')
                        if max_q is not None and abs(q_val - max_q) < 1e-10:
                            q_str = q_str
                    else:
                        q_str = "-"
                else:
                    c_str = "-"
                    q_str = "-"
                
                row_str += f" & {c_str} & {q_str}"
            
            row_str += " \\\\"
            latex_content.append(row_str)
        
        # Add midrule before summary rows
        latex_content.append(f"    \\cmidrule(l){{2-{total_data_cols + (2 if include_liftprob else 1)}}}")
        
        # Process summary rows
        summary_row = summary_df[summary_df['lift_prob'] == prob]
        summary_data = []
        
        for g in grounding_methods:
            g_summary_data = []
            c_values = []
            q_values = []
            
            for alg_base in search_algorithms:
                data = summary_row[
                    (summary_row['grounding method'] == g) & 
                    (summary_row['search algorithm'] == alg_base)
                ]
                
                if len(data) > 0:
                    c_val = data['C_abs'].iloc[0]
                    q_val = data['Q'].iloc[0]
                    if pd.notna(c_val):
                        c_values.append(c_val)
                    if pd.notna(q_val):
                        q_values.append(q_val)
                    g_summary_data.append((c_val, q_val))
                else:
                    g_summary_data.append((None, None))
            
            g_max_c = max(c_values) if c_values else None
            g_max_q = max(q_values) if q_values else None
            
            formatted_data = []
            for c_val, q_val in g_summary_data:
                if c_val is not None:
                    c_str = str(int(c_val))
                    if g_max_c is not None and c_val == g_max_c:
                        c_str = f"\\textbf{{{c_str}}}"
                else:
                    c_str = "-"
                
                if q_val is not None:
                    if q_val.is_integer():
                        q_str = str(int(q_val))
                    else:
                        q_str = f"{q_val:.1f}".lstrip('0')
                    if g_max_q is not None and abs(q_val - g_max_q) < 1e-10:
                        q_str = f"\\textbf{{{q_str}}}"
                else:
                    q_str = "-"
                
                formatted_data.append((c_str, q_str))
            
            summary_data.extend(formatted_data)
        
        # Add summary rows with conditional formatting for lift_prob column
        multicolumn_start = "    \\multicolumn{1}{c}{} & " if include_liftprob else "    "
        
        # SUM(C) row
        row_str = f"{multicolumn_start}SUM(C)"
        for c_str, _ in summary_data:
            row_str += f" & {c_str} & "
        row_str = row_str.rstrip()
        row_str += " \\\\"
        latex_content.append(row_str)
        
        # AVG(Q) row
        row_str = f"{multicolumn_start}AVG(Q)"
        for _, q_str in summary_data:
            row_str += f" &  & {q_str}"
        latex_content.append(row_str + " \\\\")
        
        if i < len(lift_probs) - 1:
            latex_content.append("    \\midrule")
    
    # Add table footer
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
    folder = 'exp_logs_csv/'
    main_table = folder + 'main_table.csv'
    main_df = pd.read_csv(main_table)
    summary_table = folder + 'summary_table.csv'
    summary_df = pd.read_csv(summary_table)

    output = folder + 'main_table.tex'
    alg_order_list = ['UCS', 'A*(FF)', 'A*(UNR)', 'WA*(FF)', 'WA*(UNR)', 'GBFS(FF)', 'GBFS(UNR)', 'DFS']

    main_df = main_df[main_df['grounding method'] != 'SG4']
    
    # Set include_liftprob to False to exclude the lift probability column
    process_csv_to_latex(main_df, summary_df, alg_order_list, output, include_liftprob=False)