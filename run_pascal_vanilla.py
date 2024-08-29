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

    # test_string = ''
    plan = [PositivePlan(ground_action_sequence)]

    repairer = Repairer()


    # Example for computing heuristic
    action_sequence = plan[0]._steps
    h = Heurisitc(h_name="G_HMAX", relaxation="none")
    print("Initial Heuristic value was:", h.evaluate(domain, task, action_sequence))


    # Example for grounding
    print("== Performing task transformation")
    domain = copy.deepcopy(domain) # verbose
    task = copy.deepcopy(task) # verbose

    heuristic.integrate_action_sequence(domain, task, action_sequence)

    domain_pddl = "pass_to_grounder_domain.pddl"
    problem_pddl = "pass_to_grounder_problem.pddl"
    heuristic.revert_to_fd_structure(domain, task)
    heuristic.print_domain(domain, domain_pddl)
    heuristic.print_problem(task, problem_pddl)

    print("== Grounding")
    current_dir = os.path.dirname(__file__)

    current_dir = Path(__file__).parent
    grounder = os.path.join(current_dir, 'fd2', 'src', 'translate', 'translate.py')
    print("Using grounder", grounder)

    sas_file = "out.sas"
    subprocess.check_call([grounder, domain_pddl, problem_pddl, "--sas-file", sas_file])

    print("Grounded file written to", sas_file)

    if repairer.repair(domain, [(task, plan)]):
        repairer.write(out_file)
        s = repairer.get_repairs_string()
        print(s)
    else:
        print("Problem is unsolvable")
