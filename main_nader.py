# Import necessary modules and classes
import os
import argparse
import pickle
from heuristic import Heurisitc

"""
I'm chaning this file so that it will work with a fixed file structure, instead of taking different dirs as input.
The structure will look like this:

.
└── input_directory
    ├── domain.pddl
    ├── task.pddl
    └── white_plan.pddl

"""

def save_variable_to_folder(folder_path, variable, file_name):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, 'wb') as file:
        pickle.dump(variable, file)

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--input_directory", type=str)
parser.add_argument("--domain_file", type=str, default="domain.pddl")
parser.add_argument("--task_file", type=str, default="task.pddl")
parser.add_argument("--white_plan_file", type=str, default="white_plan.pddl")

# Feel free to remove this again,
# I needed this for testing, but it is not necessarily needed anymore
parser.add_argument("--pickl-dump", type=str, default=None)
parser.add_argument("--pickl-load", type=str, default=None)

parser.add_argument("--output_directory", type=str,
                    help="the output file containing found repairs")

args = parser.parse_args()

if __name__ == '__main__':
    if args.pickl_load:
        with open(args.pickl_load, 'rb') as file:
            repairer = pickle.load(file)

        print('loaded', repairer)

    else:
        from repairer import *
        from model.plan import *

        domain_file = os.path.join(args.input_directory
                                   , args.domain_file)
        task_file = os.path.join(args.input_directory
                                 , args.task_file)
        white_plan_file = os.path.join(args.input_directory
                                       , args.white_plan_file)
        out_file = os.path.join(args.output_directory
                                , "repairs")

        domain = Domain(domain_file)
        task = Task(task_file)
        white_plan_list = [PositivePlan(white_plan_file)]

        repairer = Repairer(
            domain
            , [(task, white_plan_list)]
        )

        if args.pickl_dump:
            save_variable_to_folder(args.pickl_dump, repairer, args.input_directory.split("/")[-1])

        action_sequence = None
        h = Heurisitc(h_name="G_HMAX", relaxation="none")
        print("Initial Heuristic value was:", h.evaluate(domain, task, action_sequence))

        repairer.write(out_file)
