from repairer import Repairer
from model.plan import PositivePlan, apply_action_sequence
from typing import List
import logging
import copy
from fd.pddl.conditions import Conjunction, Atom
from heuristic_tools.heuristic import Heurisitc
import pickle
import json



class Node:
    original_domain = None
    original_task = None
    grounder = None
    logger = None

    @classmethod
    def set_grounder(cls, value):
        cls.grounder = value
    

    @classmethod
    def set_domain(cls, value):
        cls.original_domain = value


    @classmethod
    def set_task(cls, value):
        cls.original_task = value

    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger


    def __init__(self,
                 lifted_action_sequence: List[str],
                 ground_action_sequence: List[str],
                 parent: 'Node' = None,
                 is_initial_node: bool = False,
                 depth=0,
                 h_cost_needed=False
                 ):
        if self.grounder is None:
            raise ValueError("Action grounder must be set before creating instances.")
        if self.original_domain is None:
            raise ValueError("Original domain must be set before creating instances.")
        if self.original_task is None:
            raise ValueError("Original task must be set before creating instances.")
        if self.logger is None:
            raise ValueError("Logger must be set before creating instances.")

        self.is_initial_node = is_initial_node
        self.ground_action_sequence = ground_action_sequence
        self.lifted_action_sequence = lifted_action_sequence
        self.h_cost_needed = h_cost_needed
        self.parent = parent
        self.neighbours = []
        self.possible_groundings = None


        if is_initial_node:
            # TODO: review the claim below
            # These values are arbitrary numbers and won't affect the results.
            assert len(ground_action_sequence) == 0
            assert depth == 0
            self.depth = depth
            self.g_cost = 0
            self.h_cost = 0
            self.f_cost = 0
            self.repaired_domain = copy.deepcopy(self.original_domain)
            self.ground_repair_solution = None
            init_atoms = [item for item in self.original_task.init if isinstance(item, Atom)]
            self.current_state = copy.deepcopy(init_atoms)
        else:
            self.depth = depth
            self.g_cost, self.ground_repair_solution, self.repaired_domain = self._ground_repair()
            if self.g_cost != float('inf'):
                self.current_state = self.calculate_current_state()
            else:
                self.current_state = None
            self.h_cost = self.compute_h_cost() if self.h_cost_needed else 0
            self.f_cost = self.g_cost + self.h_cost



    def _ground_repair(self):
        # plan.compute_subs(domain, task)
        # succeed = plan.execute(domain, task)

        domain = copy.deepcopy(self.original_domain)
        task = self.original_task.copy()

        if len(self.lifted_action_sequence) != 0:
            task.set_goal_empty()
        plan = [PositivePlan(self.ground_action_sequence + [''])]

        repairer = Repairer()
        if repairer.repair(domain, [(task, plan)]):
            return repairer.count_repair_lines(), repairer.get_repairs_string(), domain
        else:
            return float('inf'), None, None
        
    
    def calculate_current_state(self):
        task = copy.deepcopy(self.original_task)
        plan = PositivePlan(self.ground_action_sequence)
        plan.compute_subs(self.repaired_domain, task)
        state = apply_action_sequence(self.repaired_domain, task, plan, delete_relaxed=True)
        return state


    def compute_h_cost(self):
        # TODO: debug & check
        # will always be run after ground_repair(), and hence works with the repaired self.planning.domain.
        # should be sth like: h(y(self.domain), d(self.task), self.lifted_action_sequence)
        task = copy.deepcopy(self.original_task)
        task.set_init_state(self.current_state)
        h = Heurisitc(h_name="G_HMAX", relaxation="none")
        h_cost = h.evaluate(self.original_domain, task, [(l,) for l in self.lifted_action_sequence])

        # Debug #TODO: delete this
        # d = self.original_domain
        # t = task
        # a = [(l,) for l in self.lifted_action_sequence]
        # with open('variables.pickle', 'wb') as pickle_file:
        #     pickle.dump((d, t, a), pickle_file)


        return h_cost


    def get_neighbors(self):
        # don't try to expand this node if the cost is infinite (no repairs)
        if self.f_cost == float('inf'):
            raise ValueError("Can't expand this node.")
        
        next_action_name = self.lifted_action_sequence[0]
        task = copy.deepcopy(self.original_task)
        task.set_init_state(self.current_state)

        # Precondition relaxing
        # If a precondition is not satisfied then don't check it
        domain = copy.deepcopy(self.repaired_domain)
        action = domain.get_action(next_action_name)
        curr_state_names = [p.predicate for p in self.current_state if isinstance(p, Atom)]
        relaxed_pre = [part for part in action.precondition.parts if part.predicate in curr_state_names]
        action.precondition = Conjunction(relaxed_pre)

        # # TODO: remove this idea?
        # action.precondition = Conjunction([])

        try:
            self.possible_groundings = Node.grounder(domain, task, next_action_name)
        except Exception as error:
            print(f">/>/ An error occurred during grounding: {error}")
            self.logger.info(f'>/>/ Current node:\n{self}')
            self.logger.info(f'>/>/ Current state:\n{self.current_state}')
            raise

        self.neighbours = []
        for grounding in self.possible_groundings:
            next_node = Node(
                ground_action_sequence=self.ground_action_sequence + [grounding],
                lifted_action_sequence=self.lifted_action_sequence[1:],
                parent=self,
                is_initial_node=False,
                depth=self.depth+1,
                h_cost_needed=self.h_cost_needed
            )
            if next_node.f_cost == float('inf'):
                continue
            self.neighbours.append(next_node)

        return self.neighbours


    def is_goal(self):
        # check with @songtuan
        return len(self.lifted_action_sequence) == 0 and self.f_cost != float('inf')


    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.ground_action_sequence == other.ground_action_sequence


    def __str__(self):
        next_lifted = [] if len(self.lifted_action_sequence)==0 else self.lifted_action_sequence[0]
        return ("> Node instance:" + "\n"
                + f"> Depth={self.depth}" + "\n"
                + f"> Ground actions: {self.ground_action_sequence}" + "\n"
                + f"> Repair set:\n{self.ground_repair_solution}" + "\n"
                + f"> g_cost={self.g_cost}" + "\n"
                + f"> h_cost={self.h_cost}" + "\n"
                + f"> f_cost={self.f_cost}" + "\n"
                + f"> Next lifted action: {next_lifted}" + "\n"
                + f"> Possible groundings:\n{self.possible_groundings}" + "\n"
                + f"> #neighbours={len(self.neighbours)}" + "\n"
                + f"> Current state:\n{self.current_state}" + "\n"
                )

    def __repr__(self):
        return self.__str__()


    def __lt__(self, other):
        return self.f_cost < other.f_cost


    def __hash__(self):
        return hash(tuple(self.ground_action_sequence))
