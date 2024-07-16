# Import necessary modules and classes
from repairer import *
from model.plan import *
import os
import argparse


# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--input_directory", type=str)
parser.add_argument("--domain_file", type=str, default="domain.pddl")
parser.add_argument("--task_file", type=str, default="task.pddl")
parser.add_argument("--white_plan_file", type=str, default="white_plan.pddl")

parser.add_argument("--output_directory", type=str,
                    help="the output file containing found repairs")

args = parser.parse_args()


if __name__ == '__main__':
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

    repairer.write(out_file)
