from repairer import Repairer
from model.plan import PositivePlan, apply_action_sequence
from typing import List
import logging
import copy
import time
from fd.pddl.conditions import Conjunction, Atom
from fd.pddl.predicates import Predicate
from heuristic_tools.heuristic import Heurisitc
from search_partial_grounding.lifted_pddl_grounder import ground_pddl, exhaustive_groundings
import traceback
import sys



FF = 'True'
RELAXATION = 2

HEURISTIC_ = rf"Heurisitc(h_name='L_HADD', relaxation='unary', use_ff={FF})"

if RELAXATION in (1, 2):
    DELETE_RELAXATION = True
else:
    DELETE_RELAXATION = False
PREC_RELAX_CONFIG = ['missing', 'missing-and-negative', 'all', 'exhaust']
PREC_RELAX = PREC_RELAX_CONFIG[RELAXATION]



class Node:
    original_domain = None
    original_task = None
    logger = None
    

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
                 h_cost_needed=False,
                 heuristic_relaxation=None
                 ):
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
        self.grounding_time = None
        self.h_relaxation = heuristic_relaxation
        self.num_neighbours = 0

        if is_initial_node:
            assert len(ground_action_sequence) == 0
            assert depth == 0
            self.depth = depth
            self.g_cost = 0
            self.h_cost = 0
            self.h_cost_time = 0.0
            self.f_cost = 0
            self.repaired_domain = copy.deepcopy(self.original_domain)
            self.ground_repair_solution = None
        else:
            self.depth = depth
            self.g_cost, self.ground_repair_solution, self.repaired_domain = self._ground_repair()
            if self.h_cost_needed:
                start_time = time.time()
                self.h_cost = self.compute_h_cost()
                end_time = time.time()
                self.h_cost_time = end_time - start_time
            else:
                self.h_cost = 0
                self.h_cost_time = 0
            
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
        
    
    def calculate_current_state(self, delete_relaxation=False):
        domain = copy.deepcopy(self.repaired_domain)
        task = copy.deepcopy(self.original_task)
        plan = PositivePlan(self.ground_action_sequence)
        plan.compute_subs(self.repaired_domain, task)
        try:
            state = apply_action_sequence(domain, task, plan, delete_relaxed=delete_relaxation)
            return state
        except Exception as e:
            # Handle the exception
            print(f"domain: {domain.to_pddl()}")
            print(f"task: {task.to_pddl()}")
            print(f"plan: {plan._steps}")
            raise


    def compute_h_cost(self):
        if len(self.lifted_action_sequence)==0:
            return 0
        
        task = copy.deepcopy(self.original_task)
        current_state = self.calculate_current_state(delete_relaxation=False)
        task.set_init_state(current_state)
        try:
            #TODO: this is dirty AF
            h = eval(HEURISTIC_)
            h_cost = h.evaluate(self.original_domain, task, self.lifted_action_sequence)
            return h_cost
        except Exception as e:
            # with open('lifted_actions.pkl', 'wb') as f:
            #     pickle.dump(self.lifted_action_sequence, f)
            print(f"Error in heuristic computation: {str(e)}")
            print("Stack trace:")
            print()
            traceback.print_exc()
            print(e)
            log_data_error = {
                'current_node': self.to_dict(include_state=True)
            }
            self.logger.log(issuer="node", event_type="error", level=logging.ERROR, message=log_data_error)
            sys.exit(1)

    def get_neighbors(self):
        # don't try to expand this node if the cost is infinite (no repairs)
        if self.f_cost == float('inf'):
            raise ValueError("Can't expand this node.")
        
        current_state = self.calculate_current_state(delete_relaxation=DELETE_RELAXATION)
        task = copy.deepcopy(self.original_task)
        task.set_init_state(current_state)
        domain = copy.deepcopy(self.repaired_domain)

        # Precondition relaxation
        next_action_name = self.lifted_action_sequence[0][0]
        action = domain.get_action(next_action_name)

        grounder = ground_pddl
        if PREC_RELAX == 'exhaust':
            grounder = exhaustive_groundings
        elif PREC_RELAX == 'all':
            action.precondition = Predicate('dummy-true', [])
        elif PREC_RELAX in ('missing', 'missing-and-negative'):
            curr_state_names = [p.predicate for p in current_state if isinstance(p, Atom)]
            relaxed_pre = [literal for literal in action.precondition.parts if literal.predicate in curr_state_names]
            if relaxed_pre and PREC_RELAX == 'missing-and-negative':
                relaxed_pre = [literal for literal in relaxed_pre if not literal.negated]
            if relaxed_pre:
                action.precondition = Conjunction(relaxed_pre)
            else:
                action.precondition = Predicate('dummy-true', [])   
        else: raise ValueError

        try:
            next_action_pddl = f"({' '.join(self.lifted_action_sequence[0])})"

            start_time = time.time()
            possible_groundings = grounder(domain, task, next_action_pddl)
            end_time = time.time()
            self.grounding_time = end_time - start_time
        except Exception as e:
            print(e)
            log_data_error = {
                'current_node': self.to_dict(include_state=True)
            }
            self.logger.log(issuer="node", event_type="error", level=logging.ERROR, message=log_data_error)
            raise

        neighbours = []

        for grounding in possible_groundings:
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
            neighbours.append(next_node)
        
        self.num_neighbours = len(neighbours)

        return neighbours


    def is_goal(self):
        return len(self.lifted_action_sequence) == 0 and self.f_cost != float('inf')


    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.ground_action_sequence == other.ground_action_sequence


    def to_dict(self, include_state=False):
        next_lifted = None if len(self.lifted_action_sequence) == 0 else str(self.lifted_action_sequence[0])
        d = {
            "depth": self.depth,
            "ground_actions": self.ground_action_sequence,
            "repair_set": self.ground_repair_solution,
            "g_cost": self.g_cost,
            "h_cost": self.h_cost,
            "f_cost": self.f_cost,
            "next_lifted_action": next_lifted,
            "num_neighbours": self.num_neighbours
            # "first_10_possible_groundings": self.possible_groundings[:10] if self.possible_groundings is not None else self.possible_groundings
        }
        if include_state:
            # d["current_state"] = repr([x.pddl() for x in self.current_state])[1:-1]
            d["current_state"] = 'not implemented!'
        
        return d
    
    def get_timings(self):
        if self.grounding_time is None:
            raise NotImplementedError("The grounder function has not been used yet")
        return self.h_cost_time, self.grounding_time
        

    def __str__(self):
        node_dict = self.to_dict()
        return "\n".join([f"> {key}: {value}" for key, value in node_dict.items()])

    def __repr__(self):
        return self.__str__()


    def __lt__(self, other):
        return self.f_cost < other.f_cost


    def __hash__(self):
        return hash(tuple(self.ground_action_sequence))
