# Import necessary modules and classes
from repairer import *
from model.plan import *
import os
import argparse


# parser = argparse.ArgumentParser()
# parser.add_argument("--input_directory", type=str)
# parser.add_argument("--domain_file", type=str, default="domain.pddl")
# parser.add_argument("--task_file", type=str, default="task.pddl")
# parser.add_argument("--white_plan_file", type=str, default="white_plan.pddl")
#
# parser.add_argument("--output_directory", type=str,
#                     help="the output file containing found repairs")
#
# args = parser.parse_args()


input_directory = r"/Users/naderkarimi/Code/GitHub/nader-classical-domain-repairer/input/block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan_lifted.pddl"

output_directory = r"/Users/naderkarimi/Code/GitHub/nader-classical-domain-repairer/output"


domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")


def read_action_names(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(';'):
                result.append(line)
    return result

# if __name__ == '__main__':
#     PASS

if __name__ == '__main__':
    domain = Domain(domain_file)
    task = Task(task_file)
    # white_plan_list = [PositivePlan(white_plan_file)]
    white_action_names = read_action_names(white_plan_file)

    for name in white_action_names:
        print(domain.get_action(name))




    # repairer = Repairer(
    #     domain
    #     , [(task, white_plan_list)]
    # )
    #
    # repairer.write(out_file)
