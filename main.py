# Import necessary modules and classes
from repairer import *
from model.domain import *
from model.plan import *
import os
import logging
import argparse

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--root", type=str, help="the root directory of the problem instance")
parser.add_argument("--domain_file", type=str, default="domain.pddl", help="the name of the domain file")
parser.add_argument("--white_list_dir", type=str, default="white-list", help="the name of the directory containing white list plans")
parser.add_argument("--white_plan", type=str, default="val-plan", help="the name of each white list plan file")
parser.add_argument("--black_list_dir", type=str, default="black-list", help="the name of the directory containing black list plans")
parser.add_argument("--black_plan", type=str, default="inval-plan", help="the name of each black list plan file")
parser.add_argument("--task_name", type=str, help="the prefix of the directories containing the tasks")
parser.add_argument("--outfile", type=str, default="repairs", help="the output file containing found repairs")
parser.add_argument("--log", type=str, default="INFO", help="level for logging")
args = parser.parse_args()

# Set up logging
logging.basicConfig(level=getattr(logging, args.log.upper()),
                    format="%(asctime)s %(name)-5s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M",
                    filename="log",
                    filemode="w")

if __name__ == '__main__':
    # Set up paths and load domain
    root = args.root
    domain_file = os.path.join(root, args.domain_file)
    domain = Domain(domain_file)
    
    # Filter task directories
    _filter = lambda x: os.path.isdir(os.path.join(root, x))
    if args.task_name is not None:
        _filter = lambda x: x[:len(args.task_name)] == args.task_name
    task_names = filter(_filter, os.listdir(root))
    
    instances = []
    for task_name in task_names:
        # Set up paths for each task
        task_dir = os.path.join(root, task_name)
        task_file = os.path.join(task_dir, task_name + ".pddl")
        task = Task(task_file)
        white_dir = os.path.join(task_dir, args.white_list_dir)
        black_dir = os.path.join(task_dir, args.black_list_dir)
        
        # Filter plan files
        _plan_filter = lambda x: lambda y: y[:len(x)] == x and "idx" not in y
        plans = []
        white_list = filter(_plan_filter(args.white_plan), os.listdir(white_dir))
        black_list = filter(_plan_filter(args.black_plan), os.listdir(black_dir))
        
        # Load positive (white list) plans
        for plan in white_list:
            plan_file = os.path.join(white_dir, plan)
            plans.append(PositivePlan(plan_file))
        
        # Load negative (black list) plans
        for plan in black_list:
            plan_file = os.path.join(black_dir, plan)
            with open(plan_file + ".idx", "r") as f:
                idx = int(f.readline())
            plans.append(NegativePlan(plan_file, idx))
        
        if len(plans) > 0:
            instances.append((task, plans))
    
    # Create repairer and write repairs
    repairer = Repairer(domain, instances)
    outfile = os.path.join(root, "repairs")
    if args.outfile is not None:
        outfile = args.outfile
    repairer.write(outfile)