H_NAMES = ["L_HMAX", "L_HADD", "L_HFF", "G_HMAX", "G_HADD", "G_HFF", "G_LM_CUT"]
RELAXATIONS = ["NONE", "UNARY", "ZERO_ARY"]

from relaxation_generator.shortcuts import ground
from pddl_out.files import write_files

INPUT_MODEL_DOMAIN = "domain-in.pddl"
INPUT_MODEL_PROBLEM = "problem-in.pddl"
OUTPUT_MODEL_DOMAIN = "domain-out.pddl"
OUTPUT_MODEL_PROBLEM = "problem-out.pddl"
GROUNDED_OUTPUT_SAS = "out.sas"

class Heurisitc:
    def __init__(self, h_name, relaxation):
        self.h_name = h_name
        self.relaxation = relaxation

    def evaluate(self, domain, task, action_sequence):
        if self.h_name.startswith("L_"):
            # Heuristic is lifted -> obtain PDDL model
            assert False, "TODO implement me"
        else:
            assert self.h_name.startswith("G_"), self.h_name

            write_files(domain, task, INPUT_MODEL_DOMAIN, INPUT_MODEL_PROBLEM)
            assert False, "TODO, output model to pddl"

            assert False, "TODO, transform pddl to output"

            # Heuristic is grounded -> obtain SAS+ model
            assert False, "TODO, generate ASP model"

