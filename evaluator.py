import os
import sys
import logging
import argparse
import subprocess
import multiprocessing

from tqdm import tqdm

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "benchmarks_dir", type=str,
    help="path to the directory of benchmarks")
parser.add_argument(
    "--num_cpus", type=int,
    help="number of CPUs used")
parser.add_argument(
    "--time_out", type=str,
    default="300", help="timeout for running the repairer")
parser.add_argument(
    "--iters", type=int,
    default=5, help="number of repeated iterations")
args = parser.parse_args()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    filename="log",
    filemode="w")

# Function to clean up plan files
def clean_plan(plan_file, out_file, negative=False):
    lines = []
    idx = None
    with open(plan_file, "r") as f:
        for i, line in enumerate(f):
            # Skip certain types of actions
            if "-copy" in line or "turning" in line:
                continue
            if "-stop" in line:
                if negative:
                    idx = i // 2
                continue
            lines.append(line)
    # Write cleaned plan to output file
    with open(out_file, "w") as f:
        for line in lines:
            f.write(line)
    return idx

# Main evaluation function
def evaluate(root):
    # Get all task directories
    task_names = filter(
        lambda x: os.path.isdir(os.path.join(root, x)),
        os.listdir(root))
    
    for task_name in task_names:
        task_dir = os.path.join(root, task_name)
        white_dir = os.path.join(task_dir, "white-list")
        black_dir = os.path.join(task_dir, "black-list")
        
        # Clean white-list plans
        _filter = lambda x: ("plan" in x) and ("val-plan" not in x) and ("inval-plan" not in x)
        white_plans = filter(_filter, os.listdir(white_dir))
        for plan in white_plans:
            plan_file = os.path.join(white_dir, plan)
            plan_outfile = os.path.join(white_dir, "val-" + plan)
            _ = clean_plan(plan_file, plan_outfile)
        
        # Clean black-list plans
        black_plans = filter(_filter, os.listdir(black_dir))
        for plan in black_plans:
            plan_file = os.path.join(black_dir, plan)
            plan_outfile = os.path.join(black_dir, "inval-" + plan)
            idx = clean_plan(plan_file, plan_outfile, True)
            with open(plan_outfile + ".idx", "w") as f:
                f.write(str(idx))
    
    # Run repair system multiple times
    for i in range(args.iters):
        outfile = os.path.join(root, "repairs.{}".format(i + 1))
        cmd = [
            "time",
            "timeout",
            args.time_out,
            sys.executable,
            "main.py",
            root,
            "--domain_file",
            "domain-modified.pddl",
            "--outfile",
            outfile]
        cmd = " ".join(cmd)
        
        # Run the command and capture output
        proc = subprocess.Popen(
            cmd, executable="/bin/bash",
            shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        _, errs = proc.communicate()
        
        # Check for timeout or other errors
        if proc.returncode != 0:
            domain = root.split("/")[-1]
            logging.error(domain + ":" + errs)
            break
        
        # Parse and save execution time
        times = [e for e in errs.split("\n") if e]
        wall_time = times[-3].split('\t')[-1]
        minutes, seconds = wall_time.split("m")[0], wall_time.split("m")[-1][:-1]
        total_secs = float(minutes) * 60 + float(seconds)
        time_file = os.path.join(root, "time.{}".format(i + 1))
        with open(time_file, "w") as f:
            f.write(str(total_secs))

if __name__ == '__main__':
    # Collect all benchmark directories
    benchmarks = []
    for domain_name in os.listdir(args.benchmarks_dir):
        domain_dir = os.path.join(
            args.benchmarks_dir, domain_name)
        benchmarks.append(domain_dir)
    
    # Set up multiprocessing
    num_cpus = multiprocessing.cpu_count()
    if args.num_cpus is not None:
        num_cpus = args.num_cpus
    
    # Run evaluation in parallel
    with multiprocessing.Pool(num_cpus) as p:
        _ = list(tqdm(p.imap_unordered(evaluate, benchmarks), total=len(benchmarks)))