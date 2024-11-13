import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import copy
from heuristic_tools import heuristic
import subprocess

from pathlib import Path
import re
from typing import List


from model.plan import *
from repairer import *



def grounder(domain_in, task_in, lifted_action) -> List[str]:
    aux_folder = r'heuristic_tools/'
    domain_path = aux_folder + "pass_to_grounder_domain.pddl"
    task_path = aux_folder + "pass_to_grounder_task.pddl"
    sas_path = aux_folder + 'out.sas'

    domain = copy.deepcopy(domain_in) # verbose
    task = copy.deepcopy(task_in) # verbose

    heuristic.integrate_action_sequence(domain, task, [lifted_action])
    heuristic.revert_to_fd_structure(domain, task)

    heuristic.print_domain(domain, domain_path)
    heuristic.print_problem(task, task_path)

    project_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(project_path)
    project_path = '/home/nader/projects/lifted-white-plan-domain-repair'
    grounder = os.path.join(project_path, 'fd2', 'src', 'translate', 'translate.py')
    # TODO: change file transactions to memory transactions for efficiency later. 
    with open('/dev/null', 'w') as devnull:
        subprocess.run(
            [grounder, domain_path, task_path, "--sas-file", sas_path],
            check=True,
            stdout=devnull,
            stderr=devnull
        )
    
    return _sas_parser(Path(sas_path), lifted_action[0])


def _sas_parser(file_path: Path, action_name_in: str) -> List[str]:
    def has_nx_pattern(l):
        # To see if there are any parameters of type n1..n10..nx which is only ariticially added by the grounder
        pattern = r'^n\d+$'
        return any(re.match(pattern, str(item)) for item in l)


    with file_path.open('r') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]
    filtered_lines = [lines[i+1] for i in range(len(lines)-1) if lines[i] == "begin_operator"]


    groundings = []    
    for l in filtered_lines:
        parts = l.split()
        action_name, step = parts[0].split('-step-')
        step = int(step)
        parameters = parts[1:]

        assert action_name == action_name_in, f"Grounder is passing unspected actionname={action_name}, while we are waiting for action_name_in={action_name_in}"

        ground_action = '(' + action_name + ' ' + ' '.join(map(str, parameters)) + ')'

        if has_nx_pattern(parameters):
            continue
        
        groundings.append(ground_action)

    return groundings


input_directory = os.path.join(project_root, "input/dummy_block_world/AAAI25-example1")
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan.pddl"
output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__)))
aux_folder = os.path.join(project_root, "heuristic_tools")

domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_grounded_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")


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
# action_sequence = plan[0]._steps

x = grounder(domain, task, ["pick-up", "b"])

print(x)
