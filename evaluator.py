import os
import sys
import logging
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument(
    "benchmarks_dir", type=str,
    help="path to the directory of benchmarks")
parser.add_argument(
    "--num_cpus", type=int,
    help="number of CPUs used")
args = parser.parse_args()


def clean_plan(plan_file, out_file, negative=False):
    lines = []
    idx = None
    with open(plan_file, "r") as f:
        for i, line in enumerate(f):
            if "-copy" in line:
                continue
            if "turning" in line:
                continue
            if "-stop" in line:
                if negative:
                    idx = i // 2
                continue
            lines.append(line)
    with open(out_file, "w") as f:
        for line in lines:
            f.write(line)
    return idx


def eval(root):
    task_names = filter(
            lambda x: os.path.isdir(os.path.join(root, x)),
            os.listdir(root))
    for task_name in task_names:
        task_dir = os.path.join(root, task_name)
        white_dir = os.path.join(task_dir, "white-list")
        black_dir = os.path.join(task_dir, "black-list")
        _filter = lambda x: "plan" in x
        white_plans = filter(_filter, os.listdir(white_dir))
        for plan in white_plans:
            plan_file = os.path.join(white_dir, plan)
            plan_outfile = os.path.join(white_dir, "val-"+plan)
            _ = clean_plan(plan_file, plan_outfile)
        black_plans = filter(_filter, os.listdir(black_dir))
        for plan in black_plans:
            plan_file = os.path.join(black_dir, plan)
            plan_outfile = os.path.join(black_dir, "inval-"+plan)
            idx = clean_plan(plan_file, plan_outfile, True)
            with open(plan_outfile+".idx", "w") as f:
                f.write(str(idx))
    cmd = [
            sys.executable,
            "main.py",
            root,
            "--domain_file",
            "domain-modified.pddl"]
    subprocess.run(cmd)


if __name__ == '__main__':
    benchmarks = []
    for domain_name in os.listdir(args.benchmarks_dir):
        domain_dir = os.path.join(
            args.benchmarks_dir, domain_name)
        benchmarks.append(domain_dir)
    for benchmark in benchmarks:
        eval(benchmark)
