import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, project_root)

import copy
from heuristic_tools import heuristic
from heuristic_tools import Heurisitc
import subprocess

from pathlib import Path
import re
from typing import List

from model.plan import *
from repairer import *



input_directory = os.path.join(project_root, "input/debug_problems/ged-opt14-strips")
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan.pddl"
output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__)))
aux_folder = os.path.join(project_root, "heuristic_tools")

domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_grounded_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")

with open(domain_file, 'r') as f:
        file_content = f.read()
        domain = Domain(file_content)

with open(task_file, 'r') as f:
    file_content = f.read()
    task = Task(file_content)

with open(white_plan_grounded_file, 'r') as f:
    ground_action_sequence = f.read()
    ground_action_sequence = ground_action_sequence.split('\n')

plan = [PositivePlan(ground_action_sequence)]


action_sequence = plan[0]._steps
h = Heurisitc(h_name="L_HMAX", relaxation="zeroary")
print("Initial Heuristic value was:", h.evaluate(domain, task, action_sequence))
