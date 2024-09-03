import os
import subprocess
from heuristic import Heurisitc
import heuristic
from pathlib import Path
import copy
from model.plan import *
from repairer import *


input_directory = r"./input/dummy_block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan_grounded.pddl"
output_directory = r"./output"
aux_folder = r'heuristic_aux_files/'


domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_grounded_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")



if __name__ == '__main__':
    with open(domain_file, 'r') as f:
        file_content = f.read()
        domain = Domain(file_content)

    with open(task_file, 'r') as f:
        file_content = f.read()
        task = Task(file_content)

    with open(white_plan_grounded_file, 'r') as f:
        ground_action_sequence = f.read()
        ground_action_sequence = ground_action_sequence.split('\n')

    plan = PositivePlan(ground_action_sequence)

    print(plan._steps)


    state = apply_action_sequence(domain, task, plan)

    print(state)


    # repairer = Repairer()
    # if repairer.repair(domain, [(task, plan)]): # type: ignore
    #     repairer.write(out_file)
    #     print("Repair done")
    #     s = repairer.get_repairs_string()
    #     # print(s)
    # else:
    #     print("Problem is unsolvable")
