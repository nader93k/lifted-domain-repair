# Import necessary modules and classes
import os
from model.plan import *
from repairer import *
from astar_partial_grounding import all_action_groundings


input_directory = r"./input/block_world/AAAI25-example1"
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
    domain = Domain(domain_file)
    task = Task(task_file)
    white_grounded_plan_list = [PositivePlan(white_plan_grounded_file)]

    with open(white_plan_grounded_file, 'r') as f:
        test_string = f.read()

    test_string = ''
    test_plan = [PositivePlan.from_string(test_string)]

    repairer = Repairer(
        domain
        , [(task, white_grounded_plan_list)]
    )

    repairer.write(out_file)

    s = repairer.get_repairs_string()

    x = 1
