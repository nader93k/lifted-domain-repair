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


if __name__ == '__main__':
    benchmarks = []
    for domain_name in os.listdir(args.benchmarks_dir):
        domain_dir = os.path.join(
                args.benchmarks_dir, domain_name)
        benchmarks.append(domain_dir)

