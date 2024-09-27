import logging
from pathlib import Path
import re
from model.plan import Domain, Task
from search_partial_grounding import read_ground_actions, read_action_names
from typing import List, Dict, Generator
import random


class Instance:
    def __init__(self
                 , domain_class: str
                 , instance_name: str
                 , identifier: str
                 , error_rate: str
                 , planning_task_file: Path
                 , planning_domain_file: Path
                 , white_plan_file: Path
                 ):
        self.domain_class = domain_class
        self.instance_name = instance_name
        self.identifier = identifier

        self.error_rate = error_rate

        self.planning_task_file = planning_task_file
        self.planning_domain_file = planning_domain_file
        self.white_plan_file = white_plan_file

        self.plan_length = len(read_action_names(self.white_plan_file))

        self.planning_task = None
        self.planning_domain = None
        self.lifted_plan = None
        self.ground_plan = None

    def load_to_memory(self):
        with open(self.planning_task_file, 'r') as f:
            file_content = f.read()
            self.planning_task = Task(file_content)

        with open(self.planning_domain_file, 'r') as f:
            file_content = f.read()
            self.planning_domain = Domain(file_content)

        self.lifted_plan = read_action_names(self.white_plan_file)
        self.ground_plan = read_ground_actions(self.white_plan_file)


def _list_folders(directory: Path):
    return [f for f in directory.iterdir() if f.is_dir()]


def _list_files(directory: Path):
    return [f for f in directory.iterdir() if f.is_file()]


def _find_err_rate_substring(s):
    match = re.search(r'err-rate.*$', s, re.IGNORECASE)

    if match:
        return match.group(0)
    else:
        raise ValueError("Substring 'err-rate' not found in the given text")


def list_instances(benchmark_path: Path, instance_id=None):
    """
    instance id example: 'blocks/pprobBLOCKS-5-0-err-rate-0-5'
    """
    folders = _list_folders(benchmark_path)

    folders.sort()
    planning_folders = folders[::2]

    instance_list = []
    for planning_folder in planning_folders:
        plan_folder = Path(str(planning_folder) + '_plans')
        logging.debug(f"Planning folder: {planning_folder}\n")

        
        for task_file in [f for f in _list_files(planning_folder) if not f.name.startswith("domain")]:
            domain_file = task_file.with_name('domain-' + task_file.name)
            plan_file = Path(plan_folder / task_file.stem).with_suffix(".plan")

            error_rate = _find_err_rate_substring(task_file.stem)

            instance = Instance(
                  domain_class=planning_folder.name
                , instance_name=task_file.stem
                , identifier = planning_folder.name + '/' + task_file.stem
                , planning_task_file=task_file
                , planning_domain_file=domain_file
                , error_rate=error_rate
                , white_plan_file=plan_file)

            if instance_id and instance.identifier != instance_id:
                continue

            instance_list.append(instance)

            logging.debug(f"task_file: {task_file}")
            logging.debug(f"domain_file: {domain_file}")
            logging.debug(f"plan_file: {plan_file}\n")
        
    return(instance_list)
        
        
def smart_instance_generator(instances: List[Instance], min_length, max_length) -> Generator[Instance, None, None]:
    random.seed(0)
    # Group instances by domain_class
    domain_classes: Dict[str, List[Instance]] = {}
    for instance in instances:
        if instance.domain_class not in domain_classes:
            domain_classes[instance.domain_class] = []
        domain_classes[instance.domain_class].append(instance)
    
    # Filter instances by plan length
    for domain_class in domain_classes:
        domain_classes[domain_class] = [
            inst for inst in domain_classes[domain_class]
            if min_length <= inst.plan_length <= max_length and inst.instance_name.endswith("err-rate-0-5")
        ]
    
    # Remove empty domain classes
    domain_classes = {k: v for k, v in domain_classes.items() if v}
    
    used_identifiers = set()
    
    while domain_classes:
        # Choose a random domain class
        domain_class = random.choice(list(domain_classes.keys()))
        
        # Choose a random instance from the selected domain class
        instance = random.choice(domain_classes[domain_class])
        
        # Ensure the instance hasn't been used before
        if instance.identifier not in used_identifiers:
            used_identifiers.add(instance.identifier)
            yield instance
        
        # Remove the instance from the list
        domain_classes[domain_class].remove(instance)
        
        # If the domain class is empty, remove it
        if not domain_classes[domain_class]:
            del domain_classes[domain_class]
        