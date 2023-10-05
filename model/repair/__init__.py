from fd.pddl.conditions import Conjunction, Atom, NegatedAtom
from fd.pddl.actions import Action
from fd.pddl.conditions import Truth
from fd.pddl.effects import Effect

from typing import Union


class Repair:
    def __init__(self,
                 action_name: str,
                 atom: Union[Atom, NegatedAtom],
                 operation: int):
        self._action_name = action_name
        self._atom = atom
        self._operation = operation
        self._condition = False

    def __hash__(self):
        return hash((self._action_name, self._atom, self._operation))

    def __eq__(self, other):
        return (self.__class__ is other.__class__
                and self._action_name == other.target
                and self._atom == other.atom
                and self._operation == other.operation)

    def __repr__(self):
        return str(self)

    def apply(self, action: Action) -> Action:
        pass
    
    @property
    def target(self):
        return self._action_name

    @property
    def atom(self):
        return self._atom

    @property
    def operation(self):
        return self._operation

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value):
        self._condition = value


class RepairPrec(Repair):
    def __init__(self,
                 action_name: str,
                 atom: Union[Atom, NegatedAtom],
                 operation: int):
        super().__init__(action_name, atom, operation)

    def __str__(self):
        if self._operation == -1:
            return "Delete {} from Precondition: {}".format(
                    self._atom, self._action_name)
        else:
            return "Add {} to Precondition: {}".format(
                    self._atom, self._action_name)

    def apply(self, action: Action) -> Action:
        literals = (action.precondition,)
        if isinstance(action.precondition, Conjunction):
            literals = action.precondition.parts
        lits = []
        if self._operation == -1:
            lits = [l for l in literals if l != self._atom]
        elif self._operation == 1:
            lits = [l for l in literals]
            lits.append(self._atom)
        prec = Conjunction(lits)
        return Action(self._action_name,
                      action.parameters,
                      action.num_external_parameters,
                      prec, action.effects,
                      action.cost)


class RepairEffs(Repair):
    def __init__(self,
                 action_name: str,
                 atom: Union[Atom, NegatedAtom],
                 operation: int):
        super().__init__(action_name, atom, operation)

    def __str__(self):
        if self._operation == -1:
            return "Delete {} from Effects: {}".format(
                    self._atom, self._action_name)
        else:
            return "Add {} to Effects: {}".format(
                    self._atom, self._action_name)

    def apply(self, action: Action) -> Action:
        effects = []
        effs = action.effects
        if self._operation == -1:
            effects = [e for e in effs if e.literal != self._atom]
        elif self._operation == 1:
            effects = [e for e in effs]
            effects.append(Effect([], Truth(), self._atom))
        return Action(self._action_name,
                      action.parameters,
                      action.num_external_parameters,
                      action.precondition,
                      effects, action.cost)

    def negate(self):
        return {RepairEffs(self._action_name,
                           self._atom,
                           -1 * self._operation),
                RepairEffs(self._action_name,
                           self._atom.negate(),
                           self._operation)}