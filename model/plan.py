from fd.pddl.conditions import Conjunction, Atom
from .domain import *
from .repair import *
from utils import *
from typing import List, Tuple, Set


def applicable(action, state, var_mapping):
    # Check if an action is applicable in a given state
    literals = (action.precondition,)
    if isinstance(action.precondition, Conjunction):
        literals = action.precondition.parts
    for literal in literals:
        grounded_paras = tuple(var_mapping[para].name for para in literal.args)

        atom = Atom(literal.predicate, grounded_paras)
        if (not literal.negated) and (atom not in state):
            return atom
        if literal.negated and (atom in state):
            return atom.negate()
    return None


def check_goal(state, goal):
    # Check if a goal is satisfied in a given state
    if goal is None:
        return None
    for atom in goal.parts:
        if (not atom.negated) and (atom not in state):
            return atom
        if atom.negated and (atom in state):
            return atom
    return None


def apply_action_sequence(domain: Domain, task: Task, plan, delete_relaxed) -> List[Atom]:
    state = set(task.init)
    
    for pos, step in enumerate(plan._steps):
        action = domain.get_action(step[0])
        var_mapping = plan._var_mapping[pos][-1]
        unsat_atom = applicable(action, state, var_mapping)
        if unsat_atom is not None:
            raise ValueError(f"Action {action} not applicable in current state")
        state = next_state(action, var_mapping, state, delete_relaxed=delete_relaxed)
    
    state = list(state)
    return state


def next_state(action, var_mapping, current, delete_relaxed=False):
    # Compute the next state after applying an action
    pos_effs, neg_effs = set(), set()
    for eff in action.effects:
        assert (len(eff.parameters) == 0)
        literal = eff.literal
        grounded_paras = tuple(var_mapping[para].name for para in literal.args)
        atom = Atom(literal.predicate, grounded_paras)
        if literal.negated:
            neg_effs.add(atom)
        else:
            pos_effs.add(atom)
    if delete_relaxed:
        state = current
    else:
        state = current.difference(neg_effs)
    state = state.union(pos_effs)
    return state


class Plan:
    def __init__(self, action_sequence):
        # Initialize a plan from a file
        self.action_sequence = action_sequence
        self._steps: List[Tuple] = []
        self._var_mapping = []
        self._parse_plan(action_sequence)
        self._succeed = False
        self._pos = None
        self._atom = None


    def _parse_plan(self, lines):
        for line in lines:
            line = line.strip()
            if line:
                if line[0] == "(" and line[-1] == ")":
                    line = line[1:-1]
                    parts = line.split(" ")
                    self._steps.append(tuple(parts))


    @property
    def executable(self):
        return self._succeed


    @property
    def position(self):
        return self._pos

    @property
    def atom(self):
        return self._atom

    def compute_subs(self, domain, task):
        # Compute substitutions for the plan
        for step in self._steps:
            mapping = {}
            action = domain.get_action(step[0])
            for idx, para in enumerate(action.parameters):
                object = task.get_object(step[idx + 1])
                if object is None:
                    object = domain.get_constant(step[idx + 1])
                if object is None:
                    raise KeyError("Undefined object")
                mapping[para.name] = object
            mapping.update([(c.name, c) for c in domain.constants])
            self._var_mapping.append((step[0], mapping))

    def step(self, idx):
        return self._steps[idx]

    def substitution(self, idx):
        return self._var_mapping[idx]

    def execute(self, domain: Domain, task: Task):
        pass

    def compute_conflict(self, domain: Domain):
        pass


class PositivePlan(Plan):
    def __init__(self, action_sequence):
        super().__init__(action_sequence)

    def execute(self, domain: Domain, task: Task):
        # Execute a positive plan
        state = set()
        for p in task.init:
            state.add(p)
        for pos, step in enumerate(self._steps):
            action = domain.get_action(step[0])
            var_mapping = self._var_mapping[pos][-1]
            unsat_atom = applicable(action, state, var_mapping)
            if unsat_atom is not None:
                self._succeed = False
                self._pos = pos
                self._atom = unsat_atom
                return False
            state = next_state(action, var_mapping, state)
        unsat_atom = check_goal(state, task.goal)
        if unsat_atom is not None:
            self._succeed = False
            self._pos = len(self._steps)
            self._atom = unsat_atom
            return False
        return True

    def compute_conflict(self, domain: Domain) -> Set[Repair]:
        # Compute conflicts for a positive plan
        conflict = set()
        if self._pos < len(self._steps):
            # if we are repairing to reach the goal then self._pos == len(self.steps) and this block won't run
            # this block repairs (removes) preconditions of an action
            name = self._steps[self._pos][0]
            action = domain.get_action(name)
            prec = match_existing_prec(
                action,
                self._var_mapping[self._pos][-1],
                self._atom)
            for atom in prec:
                repair = RepairPrec(name, atom, -1)
                conflict.add(repair)
        for idx in range(self._pos - 1, -1, -1):
            has_neg_conf = False
            name = self._steps[idx][0]
            action = domain.get_action(name)
            missing = match_missing_effs(
                action,
                self._var_mapping[idx][-1],
                self._atom)
            for atom in missing:
                repair = RepairEffs(name, atom, 1)
                conflict.add(repair)
                for r in repair.negate():
                    if r in domain.repairs:
                        has_neg_conf = True
            if not self._atom.negated:
                existing = match_existing_effs(
                    action,
                    self._var_mapping[idx][-1],
                    self._atom.negate())
            else:
                existing = match_existing_effs(
                    action,
                    self._var_mapping[idx][-1],
                    self._atom)
            if len(existing) > 0:
                for atom in existing:
                    repair = RepairEffs(name, atom, -1)
                    conflict.add(repair)
                break
            if has_neg_conf:
                break
        for r in domain.repairs:
            for neg in r.negate():
                if neg in conflict:
                    conflict.remove(neg)
                    r.condition = True
                    conflict.add(r)
        return conflict


class NegativePlan(PositivePlan):
    def __init__(self, plan_file, idx):
        super().__init__(plan_file)
        self._idx = idx

    def execute(self, domain: Domain, task: Task):
        # Execute a negative plan
        state = {p for p in task.init}
        for pos, step in enumerate(self._steps):
            if pos > self._idx:
                break
            action = domain.get_action(step[0])
            var_mapping = self._var_mapping[pos][-1]
            unsat_atom = applicable(action, state, var_mapping)
            if unsat_atom is not None:
                if pos != self._idx:
                    self._succeed = False
                    self._pos = pos
                    self._atom = unsat_atom
                    return False
                else:
                    return True
            else:
                if pos == self._idx:
                    self._pos = None
                    return False
            state = next_state(action, var_mapping, state)
        return False

    def compute_conflict(self, domain: Domain):
        # Compute conflicts for a negative plan
        if self._pos is not None and self._pos < self._idx:
            return super().compute_conflict(domain)
        name = self._steps[self._idx][0]
        action = domain.get_action(name)
        conflict = set()
        atoms = match_missing_prec(action, domain)
        for atom in atoms:
            if atom.predicate == "=":
                continue
            repair = RepairPrec(name, atom, 1)
            has_neg_repair = False
            for neg in repair.negate():
                if neg in domain.repairs:
                    neg.condition = True
                    conflict.add(neg)
                    has_neg_repair = True
            if has_neg_repair:
                continue
            conflict.add(repair)
        literals = (action.precondition, )
        if isinstance(action.precondition, Conjunction):
            literals = action.precondition.parts
        for literal in literals:
            var_mapping = self._var_mapping[self._idx][-1]
            grounded_paras = tuple(var_mapping[para].name for para in literal.args)
            target = Atom(literal.predicate, grounded_paras)
            if literal.negated:
                target = target.negate()
            for idx in range(self._idx - 1, -1, -1):
                prev_action = domain.get_action(self._steps[idx][0])
                prev_mapping = self._var_mapping[idx][-1]
                missing = match_missing_effs(
                        prev_action,
                        prev_mapping,
                        target.negate())
                for atom in missing:
                    if atom.predicate == "=":
                        continue
                    if atom.negated and (atom.negate() in set(eff.literal for eff in prev_action.effects)):
                        continue
                    repair = RepairEffs(prev_action.name, atom, 1)
                    has_neg_repair = False
                    for neg in repair.negate():
                        if neg in domain.repairs:
                            neg.condition = True
                            conflict.add(neg)
                            has_neg_repair = True
                    if has_neg_repair:
                        continue
                    conflict.add(repair)
                existing = match_existing_effs(
                        prev_action,
                        prev_mapping,
                        target)
                if len(existing) > 0:
                    for atom in existing:
                        if atom.predicate == "=":
                            continue
                        repair = RepairEffs(prev_action.name, atom, -1)
                        has_neg_repair = False
                        for neg in repair.negate():
                            if neg in domain.repairs:
                                neg.condition = True
                                conflict.add(neg)
                                has_neg_repair = True
                        if has_neg_repair:
                            continue
                        conflict.add(repair)
                    break
        return conflict
