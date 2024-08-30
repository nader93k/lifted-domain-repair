import os
from model.plan import *
from repairer import *
from pathlib import Path
from astar_partial_grounding.action_grounding_tools import smart_grounder, _sas_parser



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

    plan = [PositivePlan(ground_action_sequence)]

    d = smart_grounder(domain, task, plan[0]._steps)
    
    print(d)
    x = 1