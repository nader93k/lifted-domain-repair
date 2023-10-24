import os
import sys
import logging
import argparse

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


if __name__ == '__main__':
    benchmarks = []
    for domain_name in os.listdir(args.benchmarks_dir):
        domain_dir = os.path.join(
            args.benchmarks_dir, domain_name)
        benchmarks.append(domain_dir)
