import subprocess
from pathlib import Path
from fd.pddl.tasks import Task
import os
import tempfile
import re
from lifted_pddl import Parser



class InvalidInputFormatError(Exception):
  """Custom exception raised for invalid input format."""
  pass


def extract_name_and_params(input_string):
    """
    Helper function to extract name and parameters from the input string.

    Raises:
        InvalidInputFormatError: if input format is invalid
    """

    
    if (not isinstance(input_string, str)) or \
            (not input_string.startswith("(")) or \
            (not input_string.endswith(")")):
        raise InvalidInputFormatError("Input string must be enclosed in parentheses and be a string.")

    content = input_string[1:-1].strip()
    if not content:
        raise InvalidInputFormatError("Input string cannot be empty within parentheses")

    parts = content.split()
    name = parts[0]
    params = parts[1:]
    return name, params


def filter_actions(input_action, actions_to_filter):
    """
    Filters a set of actions based on an input action.

    Args:
        input_action: A string representing the input action in the format
                     "(name param1 param2 ... paramN)", where params starting
                     with '?' are considered variables.
        actions_to_filter: A set of strings representing actions, each in the
                           same format as input_action.

    Returns:
        A new set containing the filtered actions.

    Raises:
        InvalidInputFormatError: If the input action or any action in the set 
                                has an invalid format, or if there is a parameter
                                length mismatch between the input action and an
                                action being filtered.
    """

    try:
        input_name, input_params = extract_name_and_params(input_action)
    except InvalidInputFormatError as e:
        raise InvalidInputFormatError(f"Invalid input_action format: {e}")

    filtered_actions = set()

    for action in actions_to_filter:
        try:
            action_name, action_params = extract_name_and_params(action)
        except InvalidInputFormatError as e:
            raise InvalidInputFormatError(f"Invalid action format in actions_to_filter: {e}")
        
        if input_name != action_name:
            continue

        if len(input_params) != len(action_params):
            raise InvalidInputFormatError(
                f"Parameter length mismatch: input action has {len(input_params)} "
                f"parameters but filtered action has {len(action_params)} parameters. "
                f"Input action: {input_action}, Filtered action: {action}"
            )

        valid = True
        for i in range(len(input_params)):
            if not input_params[i].startswith("?"):  # If not a variable
                if input_params[i] != action_params[i]:
                    valid = False
                    break

        if valid:
            filtered_actions.add(action)

    return filtered_actions


def ground_pddl(domain, task, lifted_action):
    """Grounds a PDDL domain and task.

    Args:
        domain: The PDDL domain.
        task: The PDDL task.
        lifted_action: The lifted action to be used in the domain. It must be a Python list like ['name', 'para1', '?para2'].

    Returns:
        The output of the grounder.

    Raises:
        subprocess.CalledProcessError: If the grounder fails.
        Exception: If there is an error running the grounder.
    """
    process_id = os.getpid()

    base_dir = Path("/dev/shm/pddl_files")
    base_dir.mkdir(parents=True, exist_ok=True)

    # debug path:
    # debug_dir = '/home/remote/u7899572/lifted-white-plan-domain-repair/search_partial_grounding'
    # with tempfile.TemporaryDirectory(dir=debug_dir) as temp_dir:
    with tempfile.TemporaryDirectory(dir="/dev/shm/pddl_files/") as temp_dir:
        base_folder = Path(temp_dir)

        input_action_name, _ = extract_name_and_params(lifted_action)

        domain_path = base_folder / f"domain_{process_id}.pddl"
        with open(domain_path, "w") as f:
            content = domain.to_pddl(input_action_name)
            f.write(content)

        task_path = base_folder / f"task_{process_id}.pddl"
        with open(task_path, "w") as f:
            content = task.to_pddl()
            f.write(content)

        python_path = "/home/projects/u7899572/conda-envs/grounder/bin/python3"
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        grounder_path = os.path.join(
            parent_dir, "search_partial_grounding", "grounder_service.py"
        )

        # import pdb; pdb.set_trace()

        
        parser = Parser()
        parser.parse_domain(domain_path)
        parser.parse_problem(task_path)
        actions = parser.get_applicable_actions()
        applicable_actions = parser.encode_ground_actions_as_pddl(actions, 'str')    
        filtered = filter_actions(lifted_action, applicable_actions)
        return list(filtered)
