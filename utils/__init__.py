from fd.pddl.actions import Action
from fd.pddl.conditions import Atom, NegatedAtom, Conjunction
from fd.pddl.pddl_types import TypedObject
from model.domain import Domain
from .graph import *

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


def match_existing_prec(
        action: Action,
        var_mapping: Dict[str, TypedObject],
        target: Union[Atom, NegatedAtom]):
    literals = (action.precondition, )
    if isinstance(action.precondition, Conjunction):
        literals = action.precondition.parts
    return match_atoms(literals, var_mapping, target)


def match_missing_prec(action: Action,
                       domain: Domain):
    type_graph = TypeDGraph(domain.types)
    pos_predicates = []
    results = set()
    existing_atoms = set((action.precondition, ))
    if isinstance(action.precondition, Conjunction):
        existing_atoms = set(action.precondition.parts)
    for predicate in domain.predicates:
        candidates = []
        valid = True
        for arg in predicate.arguments:
            pos_args = []
            arg_name, arg_type = arg.name, arg.type
            for para in action.parameters:
                if type_graph.subtype(para.type, arg_type):
                    pos_args.append(para.name)
            if len(pos_args) == 0:
                valid = False
                break
            candidates.append(pos_args)
        if not valid:
            continue
        pos_predicates.append((predicate.name, candidates))
    for pos_predicate in pos_predicates:
        pos_paras = find_all_tuples(pos_predicate[-1])
        for paras in pos_paras:
            pos_atom = Atom(pos_predicate[0], paras)
            # neg_atom = pos_atom.negate()
            # if pos_atom not in existing_atoms and neg_atom not in existing_atoms:
            if pos_atom not in existing_atoms:
                results.add(pos_atom)
            # if neg_atom not in existing_atoms:
            #     results.add(neg_atom)
    return results


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
        # TODO: not adding existing atoms
        if target.negated:
            results.add(NegatedAtom(target.predicate, paras))
        else:
            results.add(Atom(target.predicate, paras))
    return results