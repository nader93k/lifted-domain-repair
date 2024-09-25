import sys
import os
# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add the project root to the Python path
sys.path.insert(0, project_root)

import subprocess
from heuristic_tools import Heurisitc
import heuristic_tools
from pathlib import Path
import copy
from model.plan import *
from repairer import *


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


    ############
    # Example: Computing heuristic
    ############

    action_sequence = plan[0]._steps
    h = Heurisitc(h_name="G_HMAX", relaxation="none")
    print("Initial Heuristic value was:", h.evaluate(domain, task, action_sequence))


    ############
    # Example: Grounding
    ############

    print("== Performing task transformation")

    domain2 = copy.deepcopy(domain) # verbose
    task2 = copy.deepcopy(task) # verbose
    heuristic.integrate_action_sequence(domain2, task2, action_sequence)

    domain_pddl = aux_folder + "pass_to_grounder_domain.pddl"
    problem_pddl = aux_folder + "pass_to_grounder_problem.pddl"
    heuristic.revert_to_fd_structure(domain2, task2)
    heuristic.print_domain(domain2, domain_pddl)
    heuristic.print_problem(task2, problem_pddl)


    print("== Grounding")

    current_dir = os.path.dirname(__file__)
    current_dir = Path(__file__).parent
    grounder = os.path.join(current_dir, 'fd2', 'src', 'translate', 'translate.py')
    print("Using grounder", grounder)

    sas_file = aux_folder + "out.sas"
    subprocess.check_call([grounder, domain_pddl, problem_pddl, "--sas-file", sas_file])
    print("Grounded file written to", sas_file)


    ############
    # Example: Repairing
    ############

    repairer = Repairer()
    if repairer.repair(domain, [(task, plan)]): # type: ignore
        repairer.write(out_file)
        print("Repair done")
        s = repairer.get_repairs_string()
        # print(s)
    else:
        print("Problem is unsolvable")
