from search_partial_grounding.action_grounding_tools import smart_grounder
from model.plan import PositivePlan, apply_action_sequence
from vanilla_runs.run_songtuans_vanilla import ground_repair
from exptools import list_instances
from pathlib import Path
import sys


# (/home/projects/u7899572/conda-envs/main) u7899572@xcs-vnode-1:~/lifted-white-plan-domain-repair$ python3 debug_grounder.py
# ['(feast learning grapefruit ham alsace quebec)', '(feast learning ham muffin alsace quebec)', '(feast learning muffin ham alsace quebec)']

# new grounder says:
# Applicable actions in PDDL format:
#  {'(feast learning grapefruit ham alsace quebec)'}



def calculate_current_state(domain, task, ground_action_sequence):
    plan = PositivePlan(ground_action_sequence)
    plan.compute_subs(domain, task)
    state = apply_action_sequence(domain, task, plan, delete_relaxed=False)
    return state


benchmark_path = './debug_grounder_data'
instance_id = 'mprime/pprob31-err-rate-0-5'
instance = list_instances(benchmark_path, instance_ids=[instance_id], lift_prob=1)[0]
instance.load_to_memory()

domain = instance.planning_domain
task = instance.planning_task


# ground_action_sequence = ['(feast love ham muffin quebec kentucky)', '(overcome prostatitis learning grapefruit earth saturn)']
# current_state = calculate_current_state(domain, task, ground_action_sequence)
# print(current_state)
# task.set_init_state(current_state)

lifted_action = ['feast', '?learning', '?muffin', '?ham', '?alsace', '?quebec']
possible_groundings = smart_grounder(domain, task, lifted_action)
print(possible_groundings)




# ground_actions:
# - (feast love ham muffin quebec kentucky)
# - (overcome prostatitis learning grapefruit earth saturn)
# - (feast learning muffin ham alsace quebec)


# repair_set: feast,(craves ?v ?n1),precPos,-1
# ground equivalent: feast, craves(learning, muffin)

# preconditions of - (feast learning grapefruit ham alsace quebec)
# (craves learning grapefruit)
# (food grapefruit)
# (food ham)
# (pleasure learning)
# (eats grapefruit ham)
# (locale grapefruit quebec)
# (attacks alsace quebec)

# preconditions of - (feast learning muffin ham alsace quebec)
# (craves learning muffin) # not satisfied
# (food muffin)
# (food ham)
# (pleasure learning)
# (eats muffin ham)
# (locale muffin quebec)
# (attacks alsace quebec)

# preconditions of - (feast learning ham muffin alsace quebec)
# (craves learning ham) # not satisfied
# (food ham)
# (food muffin)
# (pleasure learning)
# (eats ham muffin)
# (locale ham quebec)
# (attacks alsace quebec)


# Action definition
# (:action feast
# 	:parameters (?v - object
# 		?n1 - object
# 		?n2 - object
# 		?l1 - object
# 		?l2 - object)
# 	:precondition (and
# 		(craves ?v ?n1)
# 		(food ?n1)
#       (food ?n2)
# 		(pleasure ?v)
# 		(eats ?n1 ?n2)
# 		(locale ?n1 ?l2)
# 		(attacks ?l1 ?l2))
# 	:effect (and
# 		(not (craves ?v ?n1))
# 		(craves ?v ?n2)
# 		(not (locale ?n1 ?l2))
# 		(locale ?n1 ?l1)))


# current state after (feast love ham muffin quebec kentucky) and (overcome prostatitis learning grapefruit earth saturn)
# [<Atom eats(haroset, chocolate)>, <Atom harmony(rest, mars)>, <Atom pain(prostatitis)>, <Atom craves(loneliness, pistachio)>, <Atom province(kentucky)>, <Atom pleasure(learning)>, <Atom craves(triumph, lemon)>, <Atom craves(anger, lemon)>, <Atom pain(dread)>, <Atom craves(hangover, chicken)>, <Atom eats(chicken, muffin)>, <Atom food(grapefruit)>, <Atom pleasure(rest)>, <Atom pleasure(love)>, <Atom locale(snickers, kentucky)>, <Atom eats(cantelope, bacon)>, <Atom eats(muffin, ham)>, <Atom harmony(understanding, neptune)>, <Atom pleasure(triumph)>, <Atom pain(sciatica)>, <Atom pain(depression)>, <Atom eats(haroset, grapefruit)>, <Atom locale(lemon, alsace)>, <Atom pain(grief)>, <Atom orbits(saturn, neptune)>, <Atom craves(learning, grapefruit)>, <Atom harmony(love, saturn)>, <Atom eats(muffin, snickers)>, <Atom attacks(quebec, kentucky)>, <Atom craves(abrasion, muffin)>, <Atom eats(grapefruit, ham)>, <Atom pain(loneliness)>, <Atom food(cantelope)>, <Atom eats(pistachio, lemon)>, <Atom eats(snickers, pistachio)>, <Atom eats(bacon, lemon)>, <Atom pain(abrasion)>, <Atom pain(hangover)>, <Atom locale(ham, quebec)>, <Atom harmony(triumph, saturn)>, <Atom food(bacon)>, <Atom pain(angina)>, <Atom eats(ham, muffin)>, <Atom harmony(expectation, mars)>, <Atom province(quebec)>, <Atom craves(angina, lemon)>, <Atom locale(cantelope, quebec)>, <Atom eats(chocolate, haroset)>, <Atom planet(saturn)>, <Atom province(alsace)>, <Atom eats(bacon, chicken)>, <Atom eats(snickers, muffin)>, <Atom craves(understanding, chicken)>, <Atom craves(expectation, muffin)>, <Atom food(chicken)>, <Atom locale(chocolate, quebec)>, <Atom food(pistachio)>, <Atom craves(sciatica, ham)>, <Atom food(snickers)>, <Atom eats(lemon, pistachio)>, <Atom food(haroset)>, <Atom craves(love, muffin)>, <Atom eats(lemon, bacon)>, <Atom pleasure(expectation)>, <Atom locale(pistachio, alsace)>, <Atom attacks(alsace, quebec)>, <Atom locale(haroset, alsace)>, <Atom food(muffin)>, <Atom harmony(aesthetics, neptune)>, <Atom craves(dread, cantelope)>, <Atom pain(anger)>, <Atom planet(neptune)>, <Atom planet(mars)>, <Atom orbits(neptune, mars)>, <Atom craves(aesthetics, bacon)>, <Atom eats(chocolate, cantelope)>, <Atom pleasure(intoxication)>, <Atom harmony(intoxication, saturn)>, <Atom eats(cantelope, ham)>, <Atom eats(bacon, cantelope)>, <Atom food(lemon)>, <Atom eats(cantelope, chocolate)>, <Atom craves(depression, cantelope)>, <Atom locale(muffin, quebec)>, <Atom craves(intoxication, snickers)>, <Atom planet(earth)>, <Atom eats(grapefruit, haroset)>, <Atom eats(chicken, bacon)>, <Atom eats(muffin, chicken)>, <Atom locale(grapefruit, quebec)>, <Atom craves(grief, grapefruit)>, <Atom eats(ham, grapefruit)>, <Atom harmony(learning, earth)>, <Atom pleasure(aesthetics)>, <Atom food(ham)>, <Atom locale(chicken, quebec)>, <Atom eats(ham, cantelope)>, <Atom orbits(earth, saturn)>, <Atom craves(rest, haroset)>, <Atom pleasure(understanding)>, <Atom food(chocolate)>, <Atom eats(pistachio, snickers)>, <Atom locale(bacon, alsace)>]


# possible groundings:
# ['(feast expectation cantelope bacon alsace quebec)', '(feast expectation cantelope chocolate alsace quebec)', '(feast expectation cantelope ham alsace quebec)', '(feast expectation chicken bacon alsace quebec)', '(feast expectation chicken muffin alsace quebec)', '(feast expectation chocolate cantelope alsace quebec)', '(feast expectation chocolate haroset alsace quebec)', '(feast expectation grapefruit ham alsace quebec)', '(feast expectation grapefruit haroset alsace quebec)', '(feast expectation ham cantelope alsace quebec)', '(feast expectation ham grapefruit alsace quebec)', '(feast expectation ham muffin alsace quebec)', '(feast expectation muffin chicken alsace quebec)', '(feast expectation muffin ham alsace quebec)', '(feast expectation muffin snickers alsace quebec)', '(feast expectation snickers muffin alsace quebec)', '(feast expectation snickers muffin quebec kentucky)', '(feast expectation snickers pistachio alsace quebec)', '(feast expectation snickers pistachio quebec kentucky)', '(feast intoxication cantelope bacon alsace quebec)', '(feast intoxication cantelope chocolate alsace quebec)', '(feast intoxication cantelope ham alsace quebec)', '(feast intoxication chicken bacon alsace quebec)', '(feast intoxication chicken muffin alsace quebec)', '(feast intoxication chocolate cantelope alsace quebec)', '(feast intoxication chocolate haroset alsace quebec)', '(feast intoxication grapefruit ham alsace quebec)', '(feast intoxication grapefruit haroset alsace quebec)', '(feast intoxication ham cantelope alsace quebec)', '(feast intoxication ham grapefruit alsace quebec)', '(feast intoxication ham muffin alsace quebec)', '(feast intoxication muffin chicken alsace quebec)', '(feast intoxication muffin ham alsace quebec)', '(feast intoxication muffin snickers alsace quebec)', '(feast intoxication snickers muffin alsace quebec)', '(feast intoxication snickers muffin quebec kentucky)', '(feast intoxication snickers pistachio alsace quebec)', '(feast intoxication snickers pistachio quebec kentucky)', '(feast learning cantelope bacon alsace quebec)', '(feast learning cantelope chocolate alsace quebec)', '(feast learning cantelope ham alsace quebec)', '(feast learning chicken bacon alsace quebec)', '(feast learning chicken muffin alsace quebec)', '(feast learning chocolate cantelope alsace quebec)', '(feast learning chocolate haroset alsace quebec)', '(feast learning grapefruit ham alsace quebec)', '(feast learning grapefruit haroset alsace quebec)', '(feast learning ham cantelope alsace quebec)', '(feast learning ham grapefruit alsace quebec)', '(feast learning ham muffin alsace quebec)', '(feast learning muffin chicken alsace quebec)', '(feast learning muffin ham alsace quebec)', '(feast learning muffin snickers alsace quebec)', '(feast learning snickers muffin alsace quebec)', '(feast learning snickers muffin quebec kentucky)', '(feast learning snickers pistachio alsace quebec)', '(feast learning snickers pistachio quebec kentucky)', '(feast love cantelope bacon alsace quebec)', '(feast love cantelope chocolate alsace quebec)', '(feast love cantelope ham alsace quebec)', '(feast love chicken bacon alsace quebec)', '(feast love chicken muffin alsace quebec)', '(feast love chocolate cantelope alsace quebec)', '(feast love chocolate haroset alsace quebec)', '(feast love grapefruit ham alsace quebec)', '(feast love grapefruit haroset alsace quebec)', '(feast love ham cantelope alsace quebec)', '(feast love ham grapefruit alsace quebec)', '(feast love ham muffin alsace quebec)', '(feast love muffin chicken alsace quebec)', '(feast love muffin ham alsace quebec)', '(feast love muffin snickers alsace quebec)', '(feast love snickers muffin alsace quebec)', '(feast love snickers muffin quebec kentucky)', '(feast love snickers pistachio alsace quebec)', '(feast love snickers pistachio quebec kentucky)', '(feast understanding cantelope bacon alsace quebec)', '(feast understanding cantelope chocolate alsace quebec)', '(feast understanding cantelope ham alsace quebec)', '(feast understanding chicken bacon alsace quebec)', '(feast understanding chicken muffin alsace quebec)', '(feast understanding chocolate cantelope alsace quebec)', '(feast understanding chocolate haroset alsace quebec)', '(feast understanding grapefruit ham alsace quebec)', '(feast understanding grapefruit haroset alsace quebec)', '(feast understanding ham cantelope alsace quebec)', '(feast understanding ham grapefruit alsace quebec)', '(feast understanding ham muffin alsace quebec)', '(feast understanding muffin chicken alsace quebec)', '(feast understanding muffin ham alsace quebec)', '(feast understanding muffin snickers alsace quebec)', '(feast understanding snickers muffin alsace quebec)', '(feast understanding snickers muffin quebec kentucky)', '(feast understanding snickers pistachio alsace quebec)', '(feast understanding snickers pistachio quebec kentucky)']













# ------------------------------------------
# benchmark_path = './input/benchmarks-G1'
# instance_id = 'mprime/pprob31-err-rate-0-5'
# instance = list_instances(benchmark_path, instance_ids=[instance_id], lift_prob=1)[0]
# instance.load_to_memory()
# domain = instance.planning_domain
# task = instance.planning_task

# lifted_action = ['invert-single-gene-a', '?sub3']
# possible_groundings = smart_grounder(domain, task, lifted_action)
# print(possible_groundings)

# prints:
# ['(invert-single-gene-a sub1)', '(invert-single-gene-a sub2)', '(invert-single-gene-a sub3)']

# Songtuan's repair:
# invert-single-gene-a,(inverted ?x),effPos,1

# initial state
# (:INIT (NORMAL SUB2) (NORMAL SUB3) (NORMAL SUB1) (PRESENT SUB2)
#                (PRESENT SUB3) (PRESENT SUB1) (CW SUB1 SUB2)
#                (CW SUB3 SUB1) (CW SUB2 SUB3) (IDLE) (= (TOTAL-COST) 0))

# Songtuan's ground test plan
# (invert-single-gene-a sub3)

# action's definition in the flawed domain
# (:action invert-single-gene-a
# 	:parameters (?x - object)
# 	:precondition (and
# 		(idle )
# 		(normal ?x))
# 	:effect (and
# 		(not (normal ?x))(increase (total-cost ) 1)))

