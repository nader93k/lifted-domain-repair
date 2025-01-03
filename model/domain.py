from fd.pddl.parser import parse_nested_list
from fd.pddl.tasks import parse_domain, parse_task
from fd.pddl.conditions import Condition
from fd.pddl.predicates import Predicate



class Domain:
    def __init__(self, domain_string):
        domain_string = domain_string.strip()
        parsed_domain = parse_nested_list(domain_string.splitlines())
        # Extract domain components
        (self._domain_name,
         self._domain_requirements,
         self._types, self._constants,
         self._predicates, _,
         self._actions, _) = parse_domain(parsed_domain)

        # remove cost functionality
        for action in self._actions:
            if hasattr(action, 'cost'):
                action.cost = None
       
        # remove '=' predicates
        self._predicates = list(filter(lambda p: p.name != '=', self._predicates))

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
    

    def to_pddl(self, action_filter=None):
        """Generates the PDDL string representation of the domain."""

        pddl_string = f"(define (domain {self._domain_name})\n"

        pddl_string += f"  {self._domain_requirements.pddl()}\n"  # Added requirements here

        pddl_string += "  (:types\n"
        for type_obj in list([t.pddl() for t in self._types]):
            if type_obj not in ('object', 'object - object'):
                pddl_string += "    " + str(type_obj) + "\n"
        pddl_string += "  object)\n"

        pddl_string += "  (:constants\n"
        for const in self._constants:
            pddl_string += "    " + const.pddl() + "\n"
        pddl_string += "  )\n"

        pddl_string += "  (:predicates\n"
        pddl_string += "    " + '(dummy-true)' + "\n"
        for pred in self._predicates:
            pddl_string += "    " + pred.pddl() + "\n"
        pddl_string += "  )\n"

        if action_filter:
            actions_to_output = [a for a in self._actions if a.name == action_filter]
        else:
            actions_to_output = self._actions
        for action in actions_to_output:
            pddl_string += action.pddl(hide_cost=True) + "\n"

        pddl_string += ")\n"

        return pddl_string


class Task:
    def __init__(self, task_string):
        self.task_string = task_string.strip()
        parsed_task = parse_nested_list(self.task_string.splitlines())

        # Extract task components
        (self._task_name, self._task_domain_name,
         self._task_requirements, self._objects,
         self._init, self._goal, _) = parse_task(parsed_task)

        # remove function related stuff
        self._init = [x for x in self._init if not x.pddl().startswith('(=')]

        # Create a dictionary of objects for quick lookup
        self._obj_dict = {o.name: o for o in self._objects}

    def get_object(self, name):
        # Return object if it exists, otherwise return None
        if name not in self._obj_dict:
            return None
        return self._obj_dict[name]

    def copy(self):
        return Task(self.to_pddl())

    def set_goal_empty(self):
        self._goal = Condition(tuple())
    
    def set_init_state(self, state):
        self._init = state

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

    def __repr__(self):
        return f"Task(name='{self._task_name}', domain='{self._task_domain_name}', objects={len(self._objects)}, init={bool(self._init)}, goal={bool(self._goal)})"

    def __str__(self):
        return self.__repr__()
    
    def to_pddl(self):
        """Generates the PDDL string representation of the task."""

        pddl_string = f"(define (problem {self._task_name})\n"
        pddl_string += f"  (:domain {self._task_domain_name})\n"
        pddl_string += "  " + self._task_requirements.pddl() + "\n"

        pddl_string += "  (:objects\n"
        for obj in self._objects:
            pddl_string += "    " + obj.pddl() + "\n"
        pddl_string += "  )\n"

        pddl_string += "  (:init\n"
        pddl_string += "    " + '(dummy-true)' + "\n"
        for atom in self._init:
            pddl_string += "    " + atom.pddl() + "\n"
        pddl_string += "  )\n"

        pddl_string += "  (:goal\n"
        pddl_string += "    " + self._goal.pddl() + "\n"
        pddl_string += "  )\n"

        pddl_string += ")\n"

        return pddl_string
