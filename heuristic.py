import subprocess
from pathlib import Path

from relaxation_generator.shortcuts import ground
from fd.pddl.tasks import Task
import copy

#TODO: could allow to reduce datalog model
#TODO: some h+ computation?

# for now this is just for you to know which options you have
# should later add a check that makes sure the options match
H_NAMES = ["L_HMAX", "L_HADD", "L_HFF", "G_HMAX", "G_HADD", "G_HFF", "G_LM_CUT"]
RELAXATIONS = ["none", "unary", "zeroary"]

INPUT_MODEL_DOMAIN = "domain-in.pddl"
INPUT_MODEL_PROBLEM = "problem-in.pddl"
OUTPUT_MODEL_DOMAIN = "domain-out.pddl"
OUTPUT_MODEL_PROBLEM = "problem-out.pddl"
DATALOG_THEORY = "datalog.theory"
DATALOG_MODEL = "datalog.model"
GROUNDED_OUTPUT_SAS = "out.sas"

transform_to_fd = {
    "G_HMAX": "hmax",
    "G_HADD": "add",
    "G_HFF": "ff",
    "G_LM_CUT": "lmcut"
}

transform_to_pwl = {
    "L_HMAX": "hmax",
    "L_HADD": "add",
    "L_HFF": "ff"
}

current_dir = Path(__file__).resolve().parent
POWERLIFTED_PY = current_dir / 'pwl' / 'powerlifted.py'
FAST_DOWNWARD_PY = current_dir / 'fd2' / 'fast-downward.py'

def get_heuristic(command, look_for):
    output_file = "heuristic_value.tmp"
    with open(output_file, "w") as f:
        subprocess.run(command, stdout=f)

    with open(output_file, "r") as file:
        for line in file:
            if look_for in line:
                return int(line.split(":")[1].strip())

    assert False, "shouldn't reach this"
    return None

def get_fd_value(heuristic, domain_file, instance_file):
    heuristic = transform_to_fd[heuristic]

    command = [
        "python3", FAST_DOWNWARD_PY,
        domain_file, instance_file,
        "--search", f"astar({heuristic}())"
    ]

    print("Calling", *command)
    return get_heuristic(command, "Initial heuristic value for")

def get_pwl_value(heuristic, domain_file, instance_file):
    search_algorithm = "print-initial-h"
    heuristic = transform_to_pwl[heuristic]
    generator = "yannakakis"

    command = [
        "python3", POWERLIFTED_PY,
        "-d", domain_file,
        "-i", instance_file,
        "-s", search_algorithm,
        "-e", heuristic,
        "-g", generator
    ]

    print("Calling", *command)
    return get_heuristic(command, "Initial heuristic value is:")

def unprotect(s):
    """
    Creates an attribute name for all attributes _name in s.
    """
    d = dir(s)
    for attr in d:
        if attr.startswith('_') and not attr.startswith('__'):
            value = getattr(s, attr)
            new_attr = attr[1:]
            if new_attr not in d:
                setattr(s, new_attr, value)

def revert_to_fd_structure(_domain, _task):
    """
    Return domain, task in fd.pddl format for given _domain, _task in model.domain format
    """
    domain = copy.deepcopy(_domain)
    task = copy.deepcopy(_task)
    unprotect(domain)
    setattr(domain, "functions", [])
    setattr(domain, "requirements", type('requirements', (object,), {'pddl': lambda self: ''})())
    unprotect(task)
    setattr(task, "constants", domain._constants)
    setattr(task, "use_min_cost_metric", False)
    setattr(task, "domain_name", domain.domain_name)
    return domain, task


def print_domain(domain, path):
    with open(path, "w") as f:
        print(Task.domain(domain), file=f)

def print_problem(problem, path):
    with open(path, "w") as f:
        print(Task.problem(problem), file=f)

class Heurisitc:
    def __init__(self, h_name, relaxation):
        self.h_name = h_name
        self.relaxation = relaxation

    def evaluate(self, _domain, _task, action_sequence):
        # Here we revert Songtuans datastructure to match the original FD translator format again
        # This allows us to use the provided printout functions of the translator
        # To pass it on to another program as .pddl
        # ---
        # Copying here is definetly a big performance bottle neck
        # But we ignore this for now
        domain, task = revert_to_fd_structure(_domain, _task)
        print_domain(domain, INPUT_MODEL_DOMAIN)
        print_problem(task, INPUT_MODEL_PROBLEM)

        GROUND_CMD = {
            "domain": INPUT_MODEL_DOMAIN,
            "problem": INPUT_MODEL_PROBLEM,
            "theory_outp": DATALOG_THEORY,
            "model_outp": DATALOG_MODEL,
            "domain_print": OUTPUT_MODEL_DOMAIN,
            "problem_print": OUTPUT_MODEL_PROBLEM,
            "lpopt_enabled": True
        }

        if self.h_name.startswith("L_"):
            # Calling the grounder with executable 'none' executes all of its preprocessing steps and generates the
            # according datalog and .pddl files, but does not actually ground the problem yet
            GROUND_CMD["grounder"] = 'none'
        else:
            assert self.h_name.startswith("G_"), (f"{self.h_name} should either start with L_ to indicate a lifted"
                                                  "or G to indicate a grounded heuristic")
            # For now we also do not use the efficient grounder, as we would have to do an additional translation
            # the splitting by lpopt should suffice to make the FD grounder sufficiently performant for
            # a first evaluation
            GROUND_CMD["grounder"] = 'none'

        if self.relaxation:
            GROUND_CMD["relaxation"] = self.relaxation

        ground(**GROUND_CMD)

        if self.h_name.startswith("L_"):
            return get_pwl_value(self.h_name, OUTPUT_MODEL_DOMAIN, OUTPUT_MODEL_PROBLEM)
        else:
            return get_fd_value(self.h_name, OUTPUT_MODEL_DOMAIN, OUTPUT_MODEL_PROBLEM)
