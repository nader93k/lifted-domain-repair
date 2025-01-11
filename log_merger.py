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
    ('astar-unary relax-prec-delete lp1', 1.0, 'G2')
]

excluded_domains = [
    'pipesworld-notankage',
    'woodworking-opt08-strips',
    'woodworking-sat08-strips',
    'woodworking-sat11-strips',
    'woodworking-opt11-strips',
    'tidybot-opt11-strips',
    'data-network-opt18-strips',
    'snake-opt18-strips'
    'logistics00'
]


exp_parent = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/'
csv_folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_csv/'

for f, p, g in folders:
    exp_folder = exp_parent + f
    output_csv = csv_folder + f + '.csv'
    if not os.path.exists(output_csv):
        process_yaml_files(exp_folder, output_csv, lift_prob=p, domain_class_list=excluded_domains, grounding_method=g)

merged_df = pd.concat(map(pd.read_csv, glob.glob(csv_folder + "/*.csv")))
merged_df.to_csv(csv_folder + "merged.csv", index=False)

