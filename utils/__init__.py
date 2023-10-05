from fd.pddl.actions import Action
from fd.pddl.conditions import Atom, NegatedAtom, Conjunction
from fd.pddl.pddl_types import TypedObject
from model.domain import Domain

from typing import List, Dict, Union


def find_all_tuples(combs):
    if len(combs) == 0:
        return [tuple()]
    results = set()
    tail = combs.pop(-1)
    heads = find_all_tuples(combs)
    for e in tail:
        for t in heads:
            t = list(t)
            t.append(e)
            results.add(tuple(t))
    return results


def match_atoms(
        literals: List[Union[Atom, NegatedAtom]],
        var_mapping: Dict[str, TypedObject],
        target: Union[Atom, NegatedAtom]):
    matched = set()
    for lit in literals:
        grounding = tuple(var_mapping[p].name for p in lit.args)
        atom = Atom(lit.predicate, grounding)
        if lit.negated:
            atom = atom.negate()
        if atom == target:
            matched.add(lit)
    return matched


def match_precondition(
        action: Action,
        var_mapping: Dict[str, TypedObject],
        target: Union[Atom, NegatedAtom]):
    literals = (action.precondition, )
    if isinstance(action.precondition, Conjunction):
        literals = action.precondition.parts
    return match_atoms(literals, var_mapping, target)


def match_existing_effs(
        action: Action,
        var_mapping: Dict[str, TypedObject],
        target: Union[Atom, NegatedAtom]):
    literals = [eff.literal for eff in action.effects]
    return match_atoms(literals, var_mapping, target)


def match_missing_effs(
        action: Action,
        var_mapping: Dict[str, TypedObject],
        target: Union[Atom, NegatedAtom]):
    matched_paras = []
    results = set()
    for obj in target.args:
        candidates = []
        for para in action.parameters:
            if var_mapping[para.name].name == obj:
                candidates.append(para.name)
        if len(candidates) == 0:
            return set()
        matched_paras.append(candidates)
    pos_paras = find_all_tuples(matched_paras)
    for paras in pos_paras:
        if target.negated:
            results.add(NegatedAtom(target.predicate, paras))
        else:
            results.add(Atom(target.predicate, paras))
    return results