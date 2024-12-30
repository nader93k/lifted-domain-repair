import collections
import itertools
import shutil
import subprocess
from pathlib import Path
from io import UnsupportedOperation
from fd.pddl.effects import add_effect
import fd.pddl.conditions
from relaxation_generator.shortcuts import ground
from fd.pddl.tasks import Task
import copy
import pickle
import contextlib
import os
import sys
import time
import heapq

# next two definitions copied from Fast Downward

class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.start_clock = self._clock()

    def _clock(self):
        times = os.times()
        return times[0] + times[1]

    def __str__(self):
        return "[%.3fs CPU, %.3fs wall-clock]" % (
            self._clock() - self.start_clock,
            time.time() - self.start_time)

DEBUG = False
@contextlib.contextmanager
def timing(text, block=False):
    if DEBUG:
        timer = Timer()
        if block:
            print("%s..." % text)
        else:
            print("%s..." % text, end=' ')
        sys.stdout.flush()
    yield
    if DEBUG:
        if block:
            print("%s: %s" % (text, timer))
        else:
            print(timer)
        sys.stdout.flush()

#TODO: could allow to reduce datalog model
#TODO: some h+ computation?

# for now this is just for you to know which options you have
# should later add a check that makes sure the options match
H_NAMES = ["L_HMAX", "L_HADD", "L_HFF", "G_HMAX", "G_HADD", "G_HFF", "G_LM_CUT"]
RELAXATIONS = ["none", "unary", "zeroary"]

dprint = lambda *args, **kwargs: None
if not DEBUG:
    dprint = print

BASE_FOLDER = r'heuristic_tools/'
INPUT_MODEL_DOMAIN = BASE_FOLDER + "domain-in.pddl"
INPUT_MODEL_PROBLEM = BASE_FOLDER + "problem-in.pddl"
OUTPUT_MODEL_DOMAIN = BASE_FOLDER + "domain-out.pddl"
OUTPUT_MODEL_PROBLEM = BASE_FOLDER + "problem-out.pddl"
OLD_OUTPUT_MODEL_DOMAIN = BASE_FOLDER + "old-domain-out.pddl"
OLD_OUTPUT_MODEL_PROBLEM = BASE_FOLDER + "old-problem-out.pddl"
DATALOG_THEORY = BASE_FOLDER + "datalog.theory"
DATALOG_MODEL = BASE_FOLDER + "datalog.model"
GROUNDED_OUTPUT_SAS = BASE_FOLDER + "out.sas"

transform_to_fd = {
    "G_HMAX": "hmax",
    "G_HADD": "add",
    "G_HFF": "ff",
    "G_LM_CUT": "lmcut"
}

transform_to_pwl = {
    "L_HMAX": "hmax",
    "L_HADD": "add",
    "L_HFF": "ff"
}

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
POWERLIFTED_PY = parent_dir / 'pwl' / 'powerlifted.py'
FAST_DOWNWARD_PY = parent_dir / 'fd2' / 'fast-downward.py'

def _get_heuristic(command, look_for):
    output_file = BASE_FOLDER + "heuristic_value.tmp"

    with timing("Calling Heuristic", block=True):
        with open(output_file, "w") as f:
            dprint("Running", *command)
            subprocess.run(command, stdout=f)

    with timing("Parsing Heuristic Value", block=True):
        with open(output_file, "r") as file:
            for line in file:
                if look_for in line:
                    return line.split(":")[1].strip()

    assert False, "shouldn't reach this"
    return None

def get_heuristic(command, look_for):
    val = _get_heuristic(command, look_for)
    if val == 'infinity':
        return -1
    return int(val)

def get_fd_value(heuristic, domain_file, instance_file):
    heuristic = transform_to_fd[heuristic]

    command = [
        "python3", FAST_DOWNWARD_PY,
        domain_file, instance_file,
        "--search", f"astar({heuristic}())"
    ]

    # print("Calling", *command)
    return get_heuristic(command, "Initial heuristic value for")

def get_pwl_value(heuristic, domain_file, instance_file):
    search_algorithm = "print-initial-h"
    heuristic = transform_to_pwl[heuristic]
    generator = "yannakakis"

    command = [
        "python3", POWERLIFTED_PY,
        "-d", domain_file,
        "-i", instance_file,
        "-s", search_algorithm,
        "-e", heuristic,
        "-g", generator
    ]

    # print("Calling", *command)
    return get_heuristic(command, "Initial heuristic value is:")

def unprotect(s):
    """
    Creates an attribute name for all attributes _name in s.
    """
    d = dir(s)
    for attr in d:
        if attr.startswith('_') and not attr.startswith('__'):
            value = getattr(s, attr)
            new_attr = attr[1:]
            if new_attr not in d:
                setattr(s, new_attr, value)

def revert_to_fd_structure(domain, task):
    """
    Return domain, task in fd.pddl format for given _domain, _task in model.domain format
    """
    unprotect(domain)
    setattr(domain, "functions", [])
    setattr(domain, "requirements", type('requirements', (object,), {'pddl': lambda self: ''})())
    unprotect(task)
    setattr(task, "constants", domain._constants)
    setattr(task, "use_min_cost_metric", False)
    setattr(task, "domain_name", domain.domain_name)


def print_domain(domain, path):
    with open(path, "w") as f:
        print(Task.domain(domain), file=f)

def print_problem(problem, path):
    with open(path, "w") as f:
        print(Task.problem(problem), file=f)

def make_eff(eff):
    res = []
    eff = eff.normalize()
    add_effect(eff, res)
    assert len(res) == 1
    return res[0]

FREE_PRED = 'empty___precondition'
GOAL_PRED = 'final___goal'
COUNTER_PRED = 'current_plan_step'
APPLIED_PRED = 'applied_plan_step'
NUM_PAR = '?next_plan_step_num'
fix_obj_start = "fix_obj_"
obj_pred = lambda obj: f"{fix_obj_start}{obj}"
make_num = lambda i: f"n{i}"
to_eff = lambda lit: make_eff(fd.pddl.effects.SimpleEffect(lit))

def add_to_eff(atom, action):
    action.effects.append(to_eff(atom))

def add_to_pre(atom, action):
    pre = action.precondition
    if type(pre) == fd.pddl.conditions.Conjunction:
        pre.parts = tuple(list(pre.parts) + [atom])
    elif type(pre) == fd.pddl.conditions.Atom:
        pre = fd.pddl.conditions.Conjunction([pre])
        pre.parts = tuple(list(pre.parts) + [atom])
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

def datalog_pre(action):
    li = []
    _datalog_pre(li, action.precondition)
    return li

def _datalog_pre(acc, pre):
    if type(pre) == fd.pddl.conditions.Conjunction:
        for part in pre.parts:
            _datalog_pre(acc, part)
    elif type(pre) == fd.pddl.conditions.Atom or type(pre) == fd.pddl.conditions.NegatedAtom:
        if not pre.negated:
            acc.append(pre)
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

make_copy_pred = lambda pred, i: f"{pred}__copy_{i}"

def duplicate_pre(pre, duplications):
    if type(pre) == fd.pddl.conditions.Conjunction:
        for cond in pre.parts:
            duplicate_pre(cond, duplications)
    elif issubclass(type(pre), fd.pddl.conditions.Literal):
        duplications[pre.predicate] += 1
        pre.predicate = make_copy_pred(pre.predicate, duplications[pre.predicate]-1)
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

def remap_vars_condition(pre, var_remap):
    if type(pre) == fd.pddl.conditions.Conjunction:
        for cond in pre.parts:
            remap_vars_condition(cond, var_remap)
    elif issubclass(type(pre), fd.pddl.conditions.Literal):
        pre.args = tuple(arg if arg not in var_remap else var_remap[arg] for arg in pre.args)
    else:
        raise UnsupportedOperation(f"type {type(pre)} not supported yet")

def remap_vars_effect(effs, var_remap):
    for eff in effs:
        assert type(eff.condition) == fd.pddl.conditions.Truth or type(eff.condition) == fd.pddl.conditions.Falsity, "Conditional effects not supported yet"
        remap_vars_condition(eff.literal, var_remap)
def remap_vars(action, var_remap):
    remap_vars_condition(action.precondition, var_remap)
    remap_vars_effect(action.effects, var_remap)

def integrate_action_sequence(domain, task, action_sequence):
    old_actions = domain._actions
    name_to_action = dict((action.name, action) for action in old_actions)

    domain._constants += [fd.pddl.pddl_types.TypedObject(make_num(i), 'object') for i in range(len(action_sequence)+1)]
    domain._predicates += [fd.pddl.predicates.Predicate(COUNTER_PRED, [fd.pddl.pddl_types.TypedObject(NUM_PAR, 'object')]),
                           fd.pddl.predicates.Predicate(APPLIED_PRED, [fd.pddl.pddl_types.TypedObject(NUM_PAR, 'object')])]

    # copy action schema per plan step
    to_be_fixed = set()
    new_actions = []
    for i, action_step in enumerate(action_sequence):
        action_name = action_step[0]
        action_constants = [(obj, j) for j, obj in enumerate(action_step[1:]) if obj[0] != '?']
        to_be_fixed |= set(obj for obj, _ in action_constants)

        new_action = copy.deepcopy(name_to_action[action_name]) # verbose
        var_remap = dict((new_action.parameters[j].name, obj) for obj, j in action_constants)
        remap_vars(new_action, var_remap)
        new_action.name += f"-step-{i}"

        # conditions to increase counter
        add_to_pre(fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(i)]), new_action)
        for var, obj in var_remap.items():
            add_to_pre(fd.pddl.conditions.Atom(obj_pred(obj), [var]), new_action)

        add_to_eff(fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(i+1)]), new_action)
        add_to_eff(fd.pddl.conditions.Atom(APPLIED_PRED, [make_num(i)]), new_action)
        add_to_eff(fd.pddl.conditions.NegatedAtom(COUNTER_PRED, [make_num(i)]), new_action)

        new_actions.append(new_action)

    task._init.append(fd.pddl.conditions.Atom(COUNTER_PRED, [make_num(0)]))
    for obj in to_be_fixed:
        task._init.append(fd.pddl.conditions.Atom(obj_pred(obj), [obj]))

    domain._predicates += [fd.pddl.predicates.Predicate(obj_pred(obj), [fd.pddl.pddl_types.TypedObject(NUM_PAR, 'object')]) for obj in to_be_fixed]

    domain._actions = new_actions
    task._goal = fd.pddl.conditions.Conjunction([
        fd.pddl.conditions.Atom(APPLIED_PRED, [make_num(i)]) for i in range(len(action_sequence))
    ])

def integrate_pre_repair(domain, task, ref_action):
    # only use the ref_action
    domain._actions = [action for action in domain._actions if action.name == ref_action[0]]
    assert len(domain._actions) == 1, domain._actions
    action = domain._actions[0]
    action_constants = [(obj, j) for j, obj in enumerate(ref_action[1:]) if obj[0] != '?']

    var_remap = dict((action.parameters[j].name, obj) for obj, j in action_constants)
    remap_vars(action, var_remap)

    duplications = collections.defaultdict(lambda: 0)
    duplicate_pre(action.precondition, duplications)

    olds_preds = dict((pred.name, pred) for pred in domain.predicates)
    old_init = collections.defaultdict(lambda: [])
    for atom in task.init:
        old_init[atom.predicate].append(atom)

    new_preds = []
    new_init = []
    for p, am in duplications.items():
        for i in range(am):
            pred = olds_preds[p]
            new_pred = copy.deepcopy(pred)
            new_name = make_copy_pred(new_pred.name, i)
            new_pred.name = new_name
            new_preds.append(new_pred)

            for atom in old_init[pred.name]:
                new_atom = copy.deepcopy(atom)
                new_atom.predicate = new_name
                new_init.append(new_atom)

    domain._predicates = new_preds
    domain._predicates.append(fd.pddl.predicates.Predicate(GOAL_PRED, []))
    task._init = new_init

    # set effect to goal pred
    action.effects = []
    add_to_eff(fd.pddl.conditions.Atom(GOAL_PRED, []), action)

    # set goal to singlet goal pred
    task._goal = fd.pddl.conditions.Conjunction([
        fd.pddl.conditions.Atom(GOAL_PRED, [])
    ])

class DatalogRule:
    def __init__(self, head, body, cost):
        assert type(cost) is int or type(cost) is float
        self.head = head
        self.body = body
        self.cost = cost

DL_GOAL = "pred_dl_goal"
def pddl_to_datalog_rules(domain):
    rules = []

    for action in domain.actions:
        rule_body = datalog_pre(action)

        for eff in action.effects:
            assert type(eff.condition) is fd.pddl.conditions.Truth

            lit = eff.literal
            if not lit.negated:
                rules.append(DatalogRule(lit, rule_body, action.cost))

    return rules

def add_goal_rule(domain, task):
    rule_body = []
    _datalog_pre(rule_body, task.goal)
    domain.predicates.append(fd.pddl.predicates.Predicate(DL_GOAL, []))
    pars = [] # formally -- but since grounded always empty -- list(set(arg for atom in rule_body for arg in atom.args if arg[0] == "?"))
    domain.actions.append(fd.pddl.actions.Action(
        name="achieve___goal",
        parameters=pars,
        num_external_parameters=len(pars),
        precondition=fd.pddl.conditions.Conjunction(rule_body),
        effects=[to_eff(fd.pddl.conditions.Atom(GOAL_PRED, []))],
        cost=0
    ))

def add_free_atom(task):
    task.init.append(fd.pddl.conditions.Atom(FREE_PRED, []))

def get_pars(atom):
    return set(arg for arg in atom.args if arg[0] == "?")

tmp_pred = lambda i: f"tmp___pred{i}"

def binarize_datalog(dl_rules):
    new_rules = []

    for rule in dl_rules:
        if len(rule.body) == 0:
            rule.body.append(fd.pddl.conditions.Atom(FREE_PRED, []))
        else:
            head_pars = get_pars(rule.head)
            par_count = collections.defaultdict(lambda: 0)
            removed = set()
            temporaries = [atom for atom in rule.body]
            def local_superset(el1, el2):
                pars_el2 = get_pars(el2)

                for par in get_pars(el1):
                    if not ((par in pars_el2) or (par_count[par] == 1) or (par in head_pars)):
                        return False

                return True

            def add_rule(i, j):
                assert i not in removed
                assert i != j
                assert i < len(rule.body)
                assert j < len(rule.body)
                removed.add(i)
                local_par_count = collections.defaultdict(lambda: 0)
                for atom in [first, second]:
                    for arg in set(atom.args):
                        if arg[0] == "?":
                            local_par_count[arg] += 1

                tmp_pars = list(sorted(set(par for par in itertools.chain(get_pars(temporaries[i]),get_pars(temporaries[j])) if (par in head_pars or par_count[par] > local_par_count[par]))))
                tmp_atom = fd.pddl.Atom(tmp_pred(len(new_rules)), tmp_pars)
                temporaries[j] = tmp_atom

                new_rules.append(DatalogRule(tmp_atom, [temporaries[i], temporaries[j]], 0))

                for arg in tmp_pars:
                    par_count[arg] += 1

                for arg, val in local_par_count.items():
                    par_count[arg] -= val

            def get_unremoved(i=0):
                while True:
                    if i not in removed:
                        return i
                    i += 1

            for atom in rule.body:
                for arg in set(atom.args):
                    if arg[0] == "?":
                        par_count[arg] += 1

            while len(rule.body) > len(removed)+1:
                old_removed_count = len(removed)
                for i, first in enumerate(rule.body):
                    if i in removed:
                        continue
                    if old_removed_count != len(removed):
                        break
                    for j, second in enumerate(rule.body):
                        if first == second:
                            continue
                        if j in removed:
                            continue
                        if local_superset(first, second):
                            add_rule(i, j)
                            break

                if old_removed_count == len(removed):
                    i = get_unremoved()
                    j = get_unremoved(i+1)
                    add_rule(i, j)

            new_rules.append(DatalogRule(rule.head, [temporaries[get_unremoved()]], rule.cost))

    return new_rules

def other_pos(pos):
    assert pos == 0 or pos == 1
    return 1 if pos == 0 else 0

def intersection(li):
    result = li[0]

    for s in li[1:]:
        result = result.intersection(s)

    return result

def vars_of(atom):
    return set(arg for arg in atom.args if arg[0] == "?")

def create_creator(atoms, proj_vars):
    seen = set()
    creator = []
    for j, atom in enumerate(atoms):
        for i, v in enumerate(atom.args):
            if v in proj_vars and v not in seen:
                for k in proj_vars[v]:
                    creator.append((j, i, k))
                seen.add(v)

    return creator

def combine_or_project(atoms, combiner, pos_to_const):
    res = [None for _ in range(len(combiner)+len(pos_to_const))]

    for atom_pos, arg_pos, end_pos in combiner:
        res[end_pos] = atoms[atom_pos].args[arg_pos]

    for i, arg in pos_to_const.items():
        res[i] = arg

    assert not any(a == None for a in res)
    return tuple(res)

def can_match(gr_atom, l_atom):
    assert gr_atom.predicate == l_atom.predicate
    assigned = dict()
    for g_arg, l_arg in zip(gr_atom.args, l_atom.args):
        if l_arg[0] != "?":
            if g_arg != l_arg:
                return False
        else:
            if l_arg in assigned and assigned[l_arg] != g_arg:
                return False
            assigned[l_arg] = g_arg

    return True

def pos_to_const(atom):
    return dict((i, arg) for i, arg in enumerate(atom.args) if arg[0] != "?")


def dl_exploration(init, rules, comb_f=max):
    #TODO: could think about how to queue non-repairs first and delaying generation of repair atoms

    fact_cost = dict()
    priority_queue = []

    for el in init:
        if type(el) is fd.pddl.Atom:
            priority_queue.append((0, el))
            fact_cost[el] = 0
        else:
            assert type(el) is fd.pddl.f_expression.Assign and el.expression.value == 0 and el.fluent.symbol == 'total-cost'

    heapq.heapify(priority_queue)

    matching_rules = collections.defaultdict(lambda: list())
    for i, rule in enumerate(rules):
        for j, atom in enumerate(rule.body):
            matching_rules[atom.predicate].append((i, j))

    for k, v in matching_rules.items():
        matching_rules[k] = list(sorted(set(v)))

    projections = dict()
    combinations = dict()
    rule_body_pos_container = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
    for i, rule in enumerate(rules):
        assert 1 <= len(rule.body) <= 2, rule.body
        shared_vars = list(sorted(intersection([vars_of(atom) for atom in rule.body])))
        shared_vars = dict((v, [i]) for i, v in enumerate(shared_vars))

        for j, atom in enumerate(rule.body):
            creator = create_creator([atom], shared_vars)
            projections[(i, j)] = creator

            matching_rules[atom.predicate].append((i, j))

        v_to_pos = collections.defaultdict(lambda: [])
        for z, arg in enumerate(rule.head.args):
            if arg[0] == "?":
                v_to_pos[arg].append(z)
        combinations[i] = (create_creator(rule.body, v_to_pos), pos_to_const(rule.head))

    GOAL_FACT = fd.pddl.conditions.Atom(GOAL_PRED, [])
    while GOAL_FACT not in fact_cost:
        if not priority_queue:
            break

        current_cost, current_fact = heapq.heappop(priority_queue)

        if current_fact in fact_cost and fact_cost[current_fact] < current_cost:
            continue
        fact_cost[current_fact] = current_cost

        for rule_id, body_pos in matching_rules[current_fact.predicate]:
            _rule = rules[rule_id]
            if not can_match(current_fact, _rule.body[body_pos]):
                continue

            projection = combine_or_project([atom], projections[(rule_id, body_pos)], dict())
            rule_body_pos_container[(rule_id, other_pos(body_pos))][projection].add(current_fact)

            if len(rule.body) == 2:
                contained = rule_body_pos_container[(rule_id, other_pos(body_pos))][projection]

                for other_fact in contained:
                    other_f_cost = fact_cost[other_fact]
                    combined_cost = _rule.cost + comb_f(current_cost, other_f_cost)

                    to_combine = [current_fact, other_fact] if body_pos == 0 else [other_fact, current_fact]
                    combined_args = combine_or_project(to_combine, *combinations[rule_id])
            else:
                assert len(rule.body) == 1
                combined_cost = _rule.cost + current_cost
                combined_args = combine_or_project([current_fact], *combinations[rule_id])

            combined_fact = fd.pddl.conditions.Atom(_rule.head.predicate, combined_args)

            if combined_fact in fact_cost and fact_cost[combined_fact] <= current_cost:
                continue

            fact_cost[combined_fact] = combined_cost
            heapq.heappush(priority_queue, (combined_cost, combined_fact))

    INFTY = -1
    return fact_cost[GOAL_FACT] if GOAL_FACT in fact_cost else INFTY


UNREPAIRABLE = {COUNTER_PRED, APPLIED_PRED}
def integrate_repair_actions(domain):
    new_preds = []

    for action in domain._actions:
        action.cost = 0

    for pred in domain._predicates:
        if pred.name in UNREPAIRABLE or pred.name.startswith(fix_obj_start):
            continue

        new_pred_name = pred.name + "__for_free"
        new_preds.append(fd.pddl.predicates.Predicate(new_pred_name, []))

        action_args = copy.deepcopy(pred.arguments)

        pre_atom = fd.pddl.conditions.Atom(new_pred_name, [])
        eff_atom = fd.pddl.conditions.Atom(pred.name, [arg.name for arg in action_args])

        domain._actions.append(fd.pddl.actions.Action(name=f"activate_{new_pred_name}",
                                                      parameters=action_args,
                                                      num_external_parameters=len(action_args),
                                                      precondition=pre_atom,
                                                      effects=[to_eff(eff_atom)],
                                                      cost=1))

    for pred in new_preds:
        domain._predicates.append(pred)


class Heurisitc:
    def __init__(self, h_name, relaxation):
        self.h_name = h_name
        self.relaxation = relaxation
        self.no_legacy = True

    def get_val(self, domain, task):
        if self.no_legacy:
            return self.new_get_val(domain, task)
        else:
            return self.legacy_get_val()

    def new_get_val(self, domain, task):
        add_goal_rule(domain, task)
        add_free_atom(task)
        dl_rules = pddl_to_datalog_rules(domain)
        binarized_dl_rules = binarize_datalog(dl_rules)
        return dl_exploration(task.init, binarized_dl_rules, max if "HMAX" in self.h_name else lambda x,y: x+y)

    def legacy_get_val(self):
        GROUND_CMD = {
            "domain": INPUT_MODEL_DOMAIN,
            "problem": INPUT_MODEL_PROBLEM,
            "theory_outp": DATALOG_THEORY,
            "model_outp": DATALOG_MODEL,
            "domain_print": OUTPUT_MODEL_DOMAIN,
            "problem_print": OUTPUT_MODEL_PROBLEM,
            "lpopt_enabled": True
        }

        if self.h_name.startswith("L_"):
            # Calling the grounder with executable 'none' executes all of its preprocessing steps and generates the
            # according datalog and .pddl files, but does not actually ground the problem yet
            GROUND_CMD["grounder"] = 'none'
        else:
            assert self.h_name.startswith("G_"), (f"{self.h_name} should either start with L_ to indicate a lifted"
                                                  "or G to indicate a grounded heuristic")
            # For now we also do not use the efficient grounder, as we would have to do an additional translation
            # the splitting by lpopt should suffice to make the FD grounder sufficiently performant for
            # a first evaluation
            GROUND_CMD["grounder"] = 'none'

        if self.relaxation:
            GROUND_CMD["relaxation"] = self.relaxation

        with timing("Grounding/Transforimng", block=True):
            ground(**GROUND_CMD)

        dprint("GROUNDED", "now computing heuristic")

        with timing("Calculating heuristic value", block=True):
            if self.h_name.startswith("L_"):
                val = get_pwl_value(self.h_name, OUTPUT_MODEL_DOMAIN, OUTPUT_MODEL_PROBLEM)
            else:
                val = get_fd_value(self.h_name, OUTPUT_MODEL_DOMAIN, OUTPUT_MODEL_PROBLEM)
        return val

    def re_run(self, __domain, __task, action_sequence):
        if not self.no_legacy:
            shutil.copyfile(OUTPUT_MODEL_DOMAIN, OLD_OUTPUT_MODEL_DOMAIN)
            shutil.copyfile(OUTPUT_MODEL_PROBLEM, OLD_OUTPUT_MODEL_PROBLEM)

        domain = copy.deepcopy(__domain) # verbose
        task = copy.deepcopy(__task) # verbose

        integrate_pre_repair(domain, task, action_sequence[0])

        if self.no_legacy:
            integrate_repair_actions(domain)

        revert_to_fd_structure(domain, task)

        if not self.no_legacy:
            print_domain(domain, INPUT_MODEL_DOMAIN)
            print_problem(task, INPUT_MODEL_PROBLEM)

        # hack to evaluate this with h_add
        old_h = self.h_name
        self.h_name = self.h_name[:2] + "HADD"
        val = self.get_val()
        self.h_name = old_h

        assert val > 0, "Since last value was inf this needs to be > 0"

        return val

    def evaluate(self, __domain, __task, action_sequence):
        with timing("Copying domain and task", block=True):
            domain = copy.deepcopy(__domain) # verbose
            task = copy.deepcopy(__task) # verbose

        with timing("Integrating action sequence", block=True):
            integrate_action_sequence(domain, task, action_sequence)


        if self.no_legacy:
            with timing("Adding repair actions", block=True):
                integrate_repair_actions(domain)

        # Here we revert Songtuans datastructure to match the original FD translator format again
        # This allows us to use the provided printout functions of the translator
        # To pass it on to another program as .pddl
        # ---
        # Copying here is definetly a big performance bottle neck
        # But we ignore this for now
        with timing("Reverting to FD structure", block=True):
            revert_to_fd_structure(domain, task)

        with timing("Dumping files", block=True):
            if not self.no_legacy:
                print_domain(domain, INPUT_MODEL_DOMAIN)
                print_problem(task, INPUT_MODEL_PROBLEM)

        try:
            val = self.get_val(domain, task)
        except Exception as e:
            with open('domain.pkl', 'wb') as file:
                pickle.dump(__domain, file)
            with open('task.pkl', 'wb') as file:
                pickle.dump(__task, file)
            with open('actions.pkl', 'wb') as file:
                pickle.dump(action_sequence, file)
            print(f"Saved pickles.")
            raise

        ### DEBUG #TODO: remove this
        # print(f">>  Calculating H fro node with grounding:\n{self.ground_action_sequence}")
        # actions = [(l,) for l in self.lifted_action_sequence]
        # with open('domain.pkl', 'wb') as file:
        #     pickle.dump(self.original_domain, file)
        # with open('task.pkl', 'wb') as file:
        #     pickle.dump(task, file)
        # with open('actions.pkl', 'wb') as file:
        #     pickle.dump(actions, file)
        ### DEBUG Ends ####

        if val != -1:
            return val #TODO: (0, val) would be better
        else: # returned infinity == add repair is not sufficient
            # print("No single action was applicable, rerunning to precondition repair.")
            return self.re_run(__domain, __task, action_sequence) #TODO: (self.re_run(__domain, __task, action_sequence), 0)
