import subprocess
from pathlib import Path
from io import UnsupportedOperation

from fd.pddl.effects import add_effect

import fd.pddl.conditions
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

def revert_to_fd_structure(domain, task):
    """
    Return domain, task in fd.pddl format for given _domain, _task in model.domain format
    """
    unprotect(domain)
    setattr(domain, "functions", [])
    setattr(domain, "requirements", type('requirements', (object,), {'pddl': lambda self: ''})())
    unprotect(task)
    setattr(task, "constants", domain._constants)
    setattr(task, "use_min_cost_metric", False)
    setattr(task, "domain_name", domain.domain_name)


def print_domain(domain, path):
    with open(path, "w") as f:
        print(Task.domain(domain), file=f)

def print_problem(problem, path):
    with open(path, "w") as f:
        print(Task.problem(problem), file=f)

def make_eff(eff):
    res = []
    eff = eff.normalize()
    add_effect(eff, res)
    assert len(res) == 1
    return res[0]

COUNTER_PRED = 'current_plan_step'
NEXT_PRED = 'next_plan_step'
APPLIED_PRED = 'applied_plan_step'
NUM_PAR = '?next_plan_step_num'
make_num = lambda i: f"n{i}"
to_eff = lambda lit: make_eff(fd.pddl.effects.SimpleEffect(lit))

def add_to_eff(atom, action):
    action.effects.append(to_eff(atom))

def add_to_pre(atom, action):
    pre = action.precondition
    if type(pre) == fd.pddl.conditions.Conjunction:
        pre.parts = tuple(list(pre.parts) + [atom]) # verbose
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

def remap_vars_condition(pre, var_remap):
    if type(pre) == fd.pddl.conditions.Conjunction:
        for cond in pre.parts:
            remap_vars_condition(cond, var_remap)
    elif issubclass(type(pre), fd.pddl.conditions.Literal):
        pre.args = tuple(arg if arg not in var_remap else var_remap[arg] for arg in pre.args)
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

def remap_vars_effect(effs, var_remap):
    for eff in effs:
        assert type(eff.condition) == fd.pddl.conditions.Truth or type(eff.condition) == fd.pddl.conditions.Falsity, "Conditional effects not supported yet"
        remap_vars_condition(eff.literal, var_remap)
def remap_vars(action, var_remap):
    remap_vars_condition(action.precondition, var_remap)
    remap_vars_effect(action.effects, var_remap)

def integrate_action_sequence(domain, task, action_sequence):
    old_actions = domain._actions
    name_to_action = dict((action.name, action) for action in old_actions)

    domain._constants += [fd.pddl.pddl_types.TypedObject(make_num(i), 'object') for i in range(len(action_sequence)+1)]

    # copy action schema per plan step
    new_actions = []
    for i, action_step in enumerate(action_sequence):
        action_name = action_step[0]
        action_constants = [(obj, j) for j, obj in enumerate(action_step[1:]) if obj[0] != '?']

        new_action = copy.deepcopy(name_to_action[action_name]) # verbose
        var_remap = dict((new_action.parameters[j], obj) for obj, j in action_constants)
        remap_vars(new_action, var_remap)

        # conditions to increase counter
        add_to_pre(fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(i)]), new_action)

        add_to_eff(fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(i+1)]), new_action)
        add_to_eff(fd.pddl.conditions.Atom(APPLIED_PRED, [make_num(i)]), new_action)
        add_to_eff(fd.pddl.conditions.NegatedAtom(COUNTER_PRED, [make_num(i)]), new_action)

        new_actions.append(new_action)

    domain._actions = new_actions
    task._goal = fd.pddl.conditions.Conjunction([
        fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(i)]) for i in range(len(action_sequence))
    ])

class Heurisitc:
    def __init__(self, h_name, relaxation):
        self.h_name = h_name
        self.relaxation = relaxation

    def evaluate(self, __domain, __task, action_sequence):
        domain = copy.deepcopy(__domain) # verbose
        task = copy.deepcopy(__task) # verbose

        integrate_action_sequence(domain, task, action_sequence)

        # Here we revert Songtuans datastructure to match the original FD translator format again
        # This allows us to use the provided printout functions of the translator
        # To pass it on to another program as .pddl
        # ---
        # Copying here is definetly a big performance bottle neck
        # But we ignore this for now
        revert_to_fd_structure(domain, task)
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
