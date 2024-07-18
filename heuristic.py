#TODO: could allow to reduce datalog model

H_NAMES = ["L_HMAX", "L_HADD", "L_HFF", "G_HMAX", "G_HADD", "G_HFF", "G_LM_CUT"]
RELAXATIONS = ["NONE", "UNARY", "ZERO_ARY"]

from relaxation_generator.shortcuts import ground
from fd.pddl.tasks import Task
import copy

INPUT_MODEL_DOMAIN = "domain-in.pddl"
INPUT_MODEL_PROBLEM = "problem-in.pddl"
OUTPUT_MODEL_DOMAIN = "domain-out.pddl"
OUTPUT_MODEL_PROBLEM = "problem-out.pddl"
DATALOG_THEORY = "datalog.theory"
DATALOG_MODEL = "datalog.model"
GROUNDED_OUTPUT_SAS = "out.sas"

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

        # Calling the grounder with executable 'none' executes all of its preprocessing steps and generates the
        # according datalog files, but does not actually ground the problem yet
        ground(domain=INPUT_MODEL_DOMAIN,
               problem=INPUT_MODEL_PROBLEM,
               theory_outp=DATALOG_THEORY,
               model_outp=DATALOG_MODEL,
               lpopt_enabled=True,
               grounder='none')

        sas_task = None
        if self.h_name.startswith("G_"):
            # Heuristic is grounded -> ground the model

            assert False, "TODO implement me"
            sas_task = "TODO"
        else:
            assert self.h_name.startswith("L_"), (f"{self.h_name} should either start with L_ to indicate a lifted"
                                                  "or G to indicate a grounded heuristic")
            assert False, "Lifted heuristics are not supported yet"

        assert False, "TODO compute heuristic"
