# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from repairer import *
from model.domain import *
from model.plan import *

import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "root", type=str,
    help="the root directory of the problem instance")
parser.add_argument(
    "--domain_file",
    type=str, default="domain.pddl",
    help="the name of the domain file")
parser.add_argument(
    "--white_list_dir",
    type=str, default="white-list",
    help="the name of the directory containing white list plans")
parser.add_argument(
    "--white_plan",
    type=str, default="val-plan",
    help="the name of each white list plan file")
parser.add_argument(
    "--black_list_dir",
    type=str, default="black-list",
    help="the name of the directory containing black list plans")
parser.add_argument(
    "--black_plan",
    type=str, default="inval-plan",
    help="the name of each black list plan file")
parser.add_argument(
    "--task_name", type=str,
    help="the prefix of the directories containing the tasks")
parser.add_argument(
    "--outfile", type=str,
    help="the output file containing found repairs")
args = parser.parse_args()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    root = args.root
    domain_file = os.path.join(root, args.domain_file)
    domain = Domain(domain_file)
    _filter = lambda x: os.path.isdir(os.path.join(root, x))
    if args.task_name is not None:
        _filter = lambda x: x[:len(args.task_name)] == args.task_name
    task_names = filter(_filter, os.listdir(root))
    instances = []
    for task_name in task_names:
        task_dir = os.path.join(root, task_name)
        task_file = os.path.join(root, task_name + ".pddl")
        task = Task(task_file)
        white_dir = os.path.join(task_dir, args.white_list_dir)
        black_dir = os.path.join(task_dir, args.black_list_dir)
        _plan_filter = lambda x: lambda y: y[:len(x)] == x
        plans = []
        white_list = filter(
            _plan_filter(args.white_plan),
            os.listdir(white_dir))
        black_list = filter(
            _plan_filter(args.black_plan),
            os.listdir(black_dir))
        for plan in white_list:
            plan_file = os.path.join(white_dir, plan)
            plans.append(PositivePlan(plan_file))
        for plan in black_list:
            plan_file = os.path.join(black_dir, plan)
            with open(plan_file + ".idx", "r") as f:
                idx = int(f.readline())
            plans.append(NegativePlan(plan_file, idx))
        if len(plans) == 0:
            continue
        instances.append((task, plans))
    repairer = Repairer(domain, instances)
    outfile = os.path.join(root, "repairs")
    if args.outfile is not None:
        outfile = args.outfile
    repairer.write(outfile)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
