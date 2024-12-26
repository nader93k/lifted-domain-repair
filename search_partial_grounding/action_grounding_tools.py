import copy
from heuristic_tools import heuristic
import subprocess
import os
from pathlib import Path
import re
from typing import List
import random



def read_lifted_actions(file_path, lift_prob=0.0, random_seed=0) -> List[List[str]]:
    random.seed(random_seed)
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('('):
                line = line.lstrip('(').rstrip(')')

                parts = line.split()
                if not parts:
                    continue
                    
                action_name = parts[0]
                parameters = parts[1:]
                
                # Process parameters - maybe add ? to each
                processed_params = []
                for param in parameters:
                    if random.random() < lift_prob:
                        processed_params.append('?' + param)
                    else:
                        processed_params.append(param)
                
                processed_line = [action_name] + processed_params
                result.append(processed_line)

    return result


def read_ground_actions(file_path: str) -> List[str]:
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


# def all_smart_groundings(domain_in, task_in, action_sequence) -> Dict[int, List[str]]:
#     d = {}
#     for i, action in enumerate(action_sequence):
#         d[i] = _smart_grounder_single_action(domain_in, task_in, action)
#     return d
    

def smart_grounder(domain_in, task_in, lifted_action) -> List[str]:
    aux_folder = r'heuristic_tools/'
    domain_path = aux_folder + "pass_to_grounder_domain.pddl"
    task_path = aux_folder + "pass_to_grounder_task.pddl"
    sas_path = aux_folder + 'out.sas'

    domain = copy.deepcopy(domain_in) # verbose
    task = copy.deepcopy(task_in) # verbose

    heuristic.integrate_action_sequence(domain, task, [lifted_action])
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
    
    return _sas_parser(Path(sas_path), lifted_action[0])


def _sas_parser(file_path: Path, action_name_in: str) -> List[str]:
    def has_nx_pattern(l):
        # To see if there are any parameters of type n1..n10..nx which is only ariticially added by the grounder
        pattern = r'^n\d+$'
        return any(re.match(pattern, str(item)) for item in l)


    with file_path.open('r') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]
    filtered_lines = [lines[i+1] for i in range(len(lines)-1) if lines[i] == "begin_operator"]


    groundings = []
    
    for l in filtered_lines:
        parts = l.split()
        action_name, step = parts[0].split('-step-')
        step = int(step)
        parameters = parts[1:]

        assert action_name == action_name_in, f"Grounder is passing unspected actionname={action_name}, while we are waiting for action_name_in={action_name_in}"

        ground_action = '(' + action_name + ' ' + ' '.join(map(str, parameters)) + ')'

        if has_nx_pattern(parameters):
            continue
        
        groundings.append(ground_action)

    return groundings
