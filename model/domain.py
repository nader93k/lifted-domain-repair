from fd.pddl.pddl_file import parse_pddl_file
from fd.pddl.tasks import parse_domain, parse_task

class Domain:
    def __init__(self, domain_file):
        # Parse the domain file
        parsed_file = parse_pddl_file("domain", domain_file)
        # Extract domain components
        (self._domain_name,
         self._domain_requirements,
         self._types, self._constants,
         self._predicates, _,
         self._actions, _) = parse_domain(parsed_file)
        # Create a dictionary of constants for quick lookup
        self._constant_dict = {o.name: o for o in self._constants}
        # Initialize sets and dictionaries for repairs and actions
        self._repairs = set()
        self._updated_actions = {}
        self._name_to_action = {a.name: a for a in self._actions}
        self._repaired = False

    # Property getters and setters
    @property
    def repairs(self):
        return self._repairs

    @repairs.setter
    def repairs(self, value):
        self._repairs = value

    @property
    def constants(self):
        return self._constants

    @property
    def repaired(self):
        return self._repaired

    @repaired.setter
    def repaired(self, value):
        self._repaired = value

    @property
    def predicates(self):
        return self._predicates

    @property
    def types(self):
        return self._types

    def get_action(self, name):
        # Return updated action if it exists, otherwise return original action
        if name in self._updated_actions:
            return self._updated_actions[name]
        return self._name_to_action[name]

    def get_constant(self, name):
        # Return constant if it exists, otherwise return None
        if name not in self._constant_dict:
            return None
        return self._constant_dict[name]

    def update(self):
        # Apply all repairs to the domain
        self.clean()
        for repair in self._repairs:
            target = repair.target
            if target in self._updated_actions:
                action = self._updated_actions[target]
            else:
                action = self._name_to_action[target]
            updated_action = repair.apply(action)
            self._updated_actions[target] = updated_action

    def clean(self):
        # Reset updated actions
        self._updated_actions = {}


class Task:
    def __init__(self, task_file):
        # Parse the task file
        parsed_file = parse_pddl_file("task", task_file)
        # Extract task components
        (self._task_name, self._task_domain_name,
         self._task_requirements, self._objects,
         self._init, self._goal, _) = parse_task(parsed_file)
        # Create a dictionary of objects for quick lookup
        self._obj_dict = {o.name: o for o in self._objects}

    def get_object(self, name):
        # Return object if it exists, otherwise return None
        if name not in self._obj_dict:
            return None
        return self._obj_dict[name]

    # Property getters
    @property
    def init(self):
        return self._init

    @property
    def goal(self):
        return self._goal

    @property
    def objects(self):
        return self._objects
