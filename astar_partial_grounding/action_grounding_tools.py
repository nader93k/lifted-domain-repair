import copy
import heuristic
import subprocess
import os
from pathlib import Path
from collections import defaultdict
import re


class ActionGrounding:
    """
    A class representing a double dictionary for storing and retrieving possible groundings for actions.

    This class allows indexing by both action name and step number to access lists of possible groundings.
    It uses a nested defaultdict structure to automatically create new entries as needed.

    Attributes:
        data (defaultdict): A nested defaultdict storing the action groundings.
    """

    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(list))

    def __setitem__(self, action_name, step, value):
        self.data[action_name][step] = value
    
    def get(self, action_name, step):
        return self.data[action_name][step]

    def append(self, action_name, step, item):
        self.data[action_name][step].append(item)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        lines = []
        for action_name, steps in self.data.items():
            lines.append(f"Action: {action_name}")
            for step, groundings in steps.items():
                lines.append(f"  Step {step}: {groundings}")
        return "\n".join(lines)


def read_action_names(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('('):
                first_word = line.split()[0][1:]  # Remove the opening parenthesis
                result.append(first_word)
    return result


def read_ground_actions(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('('):
                result.append(line)
    return result


def _one_action_groundings(action, domain, task):
    """
    Compute possible groundings for a lifted action.

    :param action: The lifted action
    :param domain: The domain
    :param task: The task
    :return: A list of possible groundings (variable mappings)
    """
    possible_groundings = []
    objects = task.objects + domain.constants

    def recursive_ground(param_index, current_grounding):
        if param_index == len(action.parameters):
            possible_groundings.append(current_grounding.copy())
            return

        param = action.parameters[param_index]
        for obj in objects:
            if obj.type == param.type:
                current_grounding[param.name] = obj
                recursive_ground(param_index + 1, current_grounding)

    recursive_ground(0, {})
    return possible_groundings


def all_action_groundings(white_action_names, domain, task):
    all_groundings = {}
    for name in set(white_action_names):
        all_groundings[name] = []
        lifted_action = domain.get_action(name)
        grounded_action = _one_action_groundings(lifted_action, domain, task)
        for g in grounded_action:
            s = '(' + lifted_action.name
            for param in lifted_action.parameters:
                s = s + ' ' + g[param.name].name
            s = s + ')'
            all_groundings[name].append(s)

    return all_groundings



def smart_grounder(domain_in, task_in, action_sequence):
    aux_folder = r'heuristic_aux_files/'
    domain_path = aux_folder + "pass_to_grounder_domain.pddl"
    task_path = aux_folder + "pass_to_grounder_task.pddl"
    sas_path = aux_folder + 'out.sas'

    domain = copy.deepcopy(domain_in) # verbose
    task = copy.deepcopy(task_in) # verbose

    # transform action_sequence to be a list of tuples,
    # because of how integrate_action_sequence is impelemented.
    if not all(isinstance(item, tuple) for item in action_sequence):
        tuple_action_sequence = [(s,) if not isinstance(s, tuple) else s for s in action_sequence]
    else:
        tuple_action_sequence = action_sequence
    heuristic.integrate_action_sequence(domain, task, tuple_action_sequence)

    
    heuristic.revert_to_fd_structure(domain, task)
    heuristic.print_domain(domain, domain_path)
    heuristic.print_problem(task, task_path)

    project_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    grounder = os.path.join(project_path, 'fd2', 'src', 'translate', 'translate.py')

    # TODO: change file transactions to memory transactions for efficiency later. 
    with open('/dev/null', 'w') as devnull:
        subprocess.run(
            [grounder, domain_path, task_path, "--sas-file", sas_path],
            check=True,
            stdout=devnull,
            stderr=devnull
        )
    
    return _sas_parser(Path(sas_path))


def _sas_parser(file_path: Path):
    def has_nx_pattern(l):
        # To see if there are any parameters of type n1..n10..nx which is only ariticially added by the grounder
        pattern = r'^n\d+$'
        return any(re.match(pattern, str(item)) for item in l)


    with file_path.open('r') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]
    filtered_lines = [lines[i+1] for i in range(len(lines)-1) if lines[i] == "begin_operator"]


    groundings = ActionGrounding()
    
    for l in filtered_lines:
        parts = l.split()
        action_name, step = parts[0].split('-step-')
        step = int(step)
        parameters = parts[1:]
        ground_action = '(' + action_name + ' ' + ' '.join(map(str, parameters)) + ')'

        if has_nx_pattern(parameters):
            continue
        
        groundings.append(action_name, step, ground_action)

    return groundings
