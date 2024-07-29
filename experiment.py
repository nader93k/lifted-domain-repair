# Import necessary modules and classes
import os, logging
from model.plan import *
from astar_partial_grounding import all_action_groundings, read_action_names, AStar, Node
from pathlib import Path
import pprint as pp



class x:
    def __init__(self, domain_class):
        self.domain_class = domain_class
        self.planning_problem_file = planning_problem
        self.
        self.error_rate = error_rate

'''
world_name
    domain_1_1.pddl
    domain_1_2.pddl
    domain_n_m.pddl
    1_1.pddl
    1_2.pddl
    n_m.pddl
world_name_plans
    i_j.pddl
'''
'''
world_names = {}
world_name['block_world'] = []
world_name.append()
'''

parent_exp_folder = r'/Users/naderkarimi/Downloads/domain-repair-accessible-main/benchmarks-G1'


def list_folders(directory: Path):
    return [f.name for f in directory.iterdir() if f.is_dir()]


def list_files(directory: Path):
    return [f.name for f in directory.iterdir() if f.is_file()]


if __name__ == "__main__":
    folders = list_folders(Path(parent_exp_folder))
    folders.sort()
    world_folders = folders[::2]

    experiments = {}

    for folder in folders[::2]:
        experiments["planning_world"] = {folder}
        planning_folder = parent_exp_folder / folder
        all_files = list_files(planning_folder)
        problem_files = [file for file in all_files if not file.name.startswith("domain")]
        print(f"Planning folder: {planning_folder}")
