import os
import pandas as pd
import glob
from log_reader import process_yaml_files


folders = [
    ('bfs relax-prec lp033', 0.33, 'G1'),
    ('bfs relax-prec lp066', 0.66, 'G1'),
    ('bfs relax-prec lp1', 1.0, 'G1'),
    
    ('bfs relax-prec-delete lp033', 0.33, 'G2'),
    ('bfs relax-prec-delete lp066', 0.66, 'G2'),
    ('bfs relax-prec-delete lp1', 1.0, 'G2'),

    ('dfs relax-prec lp033', 0.33, 'G1'),
    ('dfs relax-prec lp066', 0.66, 'G1'),
    ('dfs relax-prec lp1', 1.0, 'G1'),
    
    ('dfs relax-prec-delete lp033', 0.33, 'G2'),
    ('dfs relax-prec-delete lp066', 0.66, 'G2'),
    ('dfs relax-prec-delete lp1', 1.0, 'G2'),

    ('astar-unary relax-prec lp033', 0.33, 'G1'),
    ('astar-unary relax-prec lp066', 0.66, 'G1'),
    ('astar-unary relax-prec lp1', 1.0, 'G1'),

    ('astar-unary relax-prec-delete lp033', 0.33, 'G2'),
    ('astar-unary relax-prec-delete lp066', 0.66, 'G2'),
    ('astar-unary relax-prec-delete lp1', 1.0, 'G2'),

    ('astar-unary-ff relax-prec lp1', 1.0, 'ff'),
    ('astar-unary-ff relax-prec lp066', 0.66, 'ff'),
]

excluded_domains = [
    'pipesworld-notankage',
    'woodworking-opt08-strips',
    'woodworking-sat08-strips',
    'woodworking-sat11-strips',
    'woodworking-opt11-strips',
    'tidybot-opt11-strips',
    'data-network-opt18-strips',
    'snake-opt18-strips',
    'logistics00',
    'ged-opt14-strips'
]


exp_parent = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/'
csv_folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'

df_list = []
for f, p, g in folders:
    exp_folder = exp_parent + f
    output_csv = csv_folder + f + '.csv'
    if not os.path.exists(output_csv):
        process_yaml_files(exp_folder, output_csv, lift_prob=p, domain_class_list=excluded_domains, grounding_method=g)
    df = pd.read_csv(output_csv)
    df_list.append(df)

merged_df = pd.concat(df_list)
merged_df = merged_df[merged_df['instance id'].notna() & (merged_df['instance id'].str.strip() != '')]
merged_df = merged_df[~merged_df['domain class'].isin(excluded_domains)]
merged_df.to_csv(csv_folder + "merged.csv", index=False)

duplicate_check = merged_df.duplicated().sum()
if duplicate_check > 0:
    print(f"Found {duplicate_check} duplicate rows")
