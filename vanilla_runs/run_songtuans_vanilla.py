import os
from model.plan import *
from repairer import *
import copy


def ground_repair(domain, task, plan_path):
    domain = copy.deepcopy(domain)
    task = copy.deepcopy(task)

    with open(plan_path, 'r') as f:
        ground_action_sequence = f.read()
    ground_action_sequence = ground_action_sequence.split('\n')
    plan = [PositivePlan(ground_action_sequence)]

    repairer = Repairer()

    if repairer.repair(domain, [(task, plan)]):
        r = repairer.get_repairs_string()
    else:
        raise Exception("Problem is unsolvable")
    return(r)


input_directory = r"./input/dummy_block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_grounded_file = "white_plan_grounded.pddl"
white_plan_lifted_file = "white_plan_lifted.pddl"

output_directory = r"./output"

domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_grounded_file = os.path.join(input_directory, white_plan_grounded_file)
white_plan_lifted_file = os.path.join(input_directory, white_plan_lifted_file)
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

    if repairer.repair(domain, [(task, plan)]):
        repairer.write(out_file)
        s = repairer.get_repairs_string()
        print(s)
    else:
        print("Problem is unsolvable")
