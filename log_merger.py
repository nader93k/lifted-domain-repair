import os
import pandas as pd
import glob
from itertools import product
from log_reader import process_yaml_files





# Define base components
algorithms = ['bfs', 'dfs', 'astar-unary-ff', 'gbfs-unary-ff']
relaxations = ['relax-prec', 'relax-prec-delete', 'relax-all']
lp_pairs = [('033', 0.33), ('066', 0.66), ('1', 1.0)]
groundings = dict([
    ('relax-prec', 'G1'),
    ('relax-prec-delete', 'G2'),
    ('relax-all', 'G3'),
])
rename = dict([
    ('bfs', 'UCS'),
    ('dfs', 'DFS'),
    ('astar-unary-ff', 'A*_FF'),
    ('gbfs-unary-ff', 'GBFS_FF'),
])

# folder, prob, grounding, rename
experiments = [
    (f"{alg} {relax} lp{lp_str}", prob, groundings[relax], rename[alg])
    for alg, relax, (lp_str, prob)
    in product(algorithms, relaxations, lp_pairs)
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
for folder, prob, grounding, rename in experiments:
    exp_folder = exp_parent + folder
    print(f'processing folder={exp_folder}')
    output_csv = csv_folder + folder + '.csv'
    if not os.path.exists(output_csv):
        process_yaml_files(exp_folder, output_csv, lift_prob=prob)
    df = pd.read_csv(output_csv)
    df['search algorithm'] = rename
    df['grounding method'] = grounding
    df_list.append(df)


merged_df = pd.concat(df_list)
merged_df = merged_df[merged_df['instance id'].notna() & (merged_df['instance id'].str.strip() != '')]
merged_df = merged_df[~merged_df['domain class'].isin(excluded_domains)]
merged_df.to_csv(csv_folder + "merged.csv", index=False)

print(f"len_df_list={len(df_list)}")
print(f"The output rows are={len(merged_df)}")
duplicate_check = merged_df.duplicated().sum()
if duplicate_check > 0:
    print(f"Found {duplicate_check} duplicate rows")


# folders = [
#     # (log-file, lift-prob, grounding, algorithm-rename)

#     # UCS
#     ('bfs relax-prec lp033', 0.33, 'G1'),
#     ('bfs relax-prec lp066', 0.66, 'G1'),
#     ('bfs relax-prec lp1', 1.0, 'G1'),
    
#     ('bfs relax-prec-delete lp033', 0.33, 'G2'),
#     ('bfs relax-prec-delete lp066', 0.66, 'G2'),
#     ('bfs relax-prec-delete lp1', 1.0, 'G2'),

#     ('bfs relax-all lp033', 0.33, 'G3'),
#     ('bfs relax-all lp066', 0.66, 'G3'),
#     ('bfs relax-all lp1', 1.0, 'G3'),

#     # DFS
#     ('dfs relax-prec lp033', 0.33, 'G1'),
#     ('dfs relax-prec lp066', 0.66, 'G1'),
#     ('dfs relax-prec lp1', 1.0, 'G1'),
    
#     ('dfs relax-prec-delete lp033', 0.33, 'G2'),
#     ('dfs relax-prec-delete lp066', 0.66, 'G2'),
#     ('dfs relax-prec-delete lp1', 1.0, 'G2'),

#     ('dfs relax-all lp033', 0.33, 'G2'),
#     ('dfs relax-all lp066', 0.66, 'G2'),
#     ('dfs relax-all lp1', 1.0, 'G2'),

#     # A*
#     ('astar-unary-ff relax-prec lp033', 0.33, 'G1'),
#     ('astar-unary-ff relax-prec lp066', 0.66, 'G1'),
#     ('astar-unary-ff relax-prec lp1', 1.0, 'G1'),

#     ('astar-unary-ff relax-prec-delete lp033', 0.33, 'G2'),
#     ('astar-unary-ff relax-prec-delete lp066', 0.66, 'G2'),
#     ('astar-unary-ff relax-prec-delete lp1', 1.0, 'G2'),

#     ('astar-unary-ff relax-all lp033', 0.33, 'G3'),
#     ('astar-unary-ff relax-all lp066', 0.66, 'G3'),
#     ('astar-unary-ff relax-all lp1', 1.0, 'G3'),
    
#     # GBFS

#     ('gbfs-unary-ff relax-prec lp033', 0.33, 'G1'),
#     ('gbfs-unary-ff relax-prec lp066', 0.66, 'G1'),
#     ('gbfs-unary-ff relax-prec lp1', 1.0, 'G1'),

#     ('gbfs-unary-ff relax-prec-delete lp033', 0.33, 'G2'),
#     ('gbfs-unary-ff relax-prec-delete lp066', 0.66, 'G2'),
#     ('gbfs-unary-ff relax-prec-delete lp1', 1.0, 'G2'),

#     ('gbfs-unary-ff relax-prec lp033', 0.33, 'G3'),
#     ('gbfs-unary-ff relax-prec lp066', 0.66, 'G3'),
#     ('gbfs-unary-ff relax-prec lp1', 1.0, 'G3'),
# ]
