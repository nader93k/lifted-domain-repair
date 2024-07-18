# General idea:
# - Output cannonical model for original task (via Gringo + LPOPT == best config from Correa 2023 ICAPS paper)
# - Build action conditions model with cons/produced atoms via Lifted Mutex groups
# - Add the facts of the original cannoncial model to the condition model to again run (Gringo + LPOPT)
# - Create a reduced model (similar to how the Full reducer works described in Correa 2020)
# - Obtain the reduced facts via the reduced model
# - Construct LP via original cannonical model and reduced facts
# - Pass to LP solver that outpus solution to readable format

#TODO: should reintegrate some kind of reduction
#TODO: Should minify ids used BIG_PREDICATE -> p1

# options
ADD_NONE_ATOMS = False
PRINT_MUTEXES = False

import os
import sys
import subprocess
from utils import find_domain_filename
from shortcuts import *

# TODO: option for different decompostion/grounder
# TODO: option for add / del add
# TODO: only keep needed files
# TODO: make reduction step optional
# TODO: option to omit binarization of rules

# TODO: could provide options for task transformations, in particular:
# TODO:   - unary relxation
# TODO:   - homomorphisms

# TODO: could provide options for different optimization criteria

# TODO: could provide options unary relaxation

def generate(domain, problem, outpfile):
    model_file_1 = get_tmp_file("1.model")
    model_file_2 = get_tmp_file("2.model")
    model_file_3 = get_tmp_file("3.model")
    model_file_4 = get_tmp_file("4.model")
    model_file_5 = get_tmp_file("5.model")
    model_file_6 = get_tmp_file("6.model")
    model_file_7 = get_tmp_file("7.model")
    model_file_8 = get_tmp_file("8.model")
    model_file_9 = get_tmp_file("9.model")
    model_file_10 = get_tmp_file("10.model")
    model_file_11 = get_tmp_file("11.model")
    model_file_12 = get_tmp_file("12.model")

    tmp_file1 = get_tmp_file("1.theory")
    tmp_file2 = get_tmp_file("2.theory")
    tmp_file3 = get_tmp_file("3.theory")
    tmp_file4 = get_tmp_file("4.theory")
    tmp_file5 = get_tmp_file("5.theory")
    tmp_file6 = get_tmp_file("6.theory")
    tmp_file7 = get_tmp_file("7.theory")
    tmp_file8 = get_tmp_file("8.theory")
    tmp_file9 = get_tmp_file("9.theory")
    tmp_file10 = get_tmp_file("10.theory")
    tmp_file11 = get_tmp_file("11.theory")
    tmp_file12 = get_tmp_file("12.theory")
    tmp_file13 = get_tmp_file("13.theory")
    tmp_file14 = get_tmp_file("14.theory")
    tmp_file15 = get_tmp_file("15.theory")
    tmp_file16 = get_tmp_file("16.theory")
    tmp_file17 = get_tmp_file("17.theory")
    tmp_file18 = get_tmp_file("18.theory")
    tmp_file19 = get_tmp_file("19.theory")
    tmp_file20 = get_tmp_file("20.theory")
    tmp_file21 = get_tmp_file("21.theory")
    tmp_file22 = get_tmp_file("22.theory")
    tmp_file23 = get_tmp_file("23.theory")
    tmp_file24 = get_tmp_file("24.theory")
    tmp_file25 = get_tmp_file("25.theory")
    tmp_file26 = get_tmp_file("26.theory")
    tmp_file27 = get_tmp_file("27.theory")
    tmp_file28 = get_tmp_file("28.theory")
    tmp_file29 = get_tmp_file("29.theory")
    tmp_file30 = get_tmp_file("30.theory")
    tmp_file31 = get_tmp_file("31.theory")
    tmp_file32 = get_tmp_file("32.theory")
    tmp_file33 = get_tmp_file("33.theory")
    tmp_file34 = get_tmp_file("34.theory")
    tmp_file35 = get_tmp_file("35.theory")
    tmp_file36 = get_tmp_file("36.theory")
    tmp_file37 = get_tmp_file("37.theory")
    tmp_file38 = get_tmp_file("38.theory")
    tmp_file39 = get_tmp_file("39.theory")
    tmp_file40 = get_tmp_file("40.theory")
    tmp_file41 = get_tmp_file("41.theory")
    tmp_file42 = get_tmp_file("42.theory")

    cpddl_log = get_tmp_file("cpddl.log")
    lp_rules = get_tmp_file("lprules.mzn")

    pot_output = outpfile

    pot_map = get_tmp_file("potmap.log")


    print("=== Starting Potential computation ===")

    # Step 1 -- Create datalog model and perform delete relaxed exploration
    #           to obtain all delete relaxed reachable atoms
    print("=== Step 1 ===")
    ground(domain, problem, tmp_file1, model_file_1, True)
    # tmp_file1 has trivial DL representation of the task
    # model_file_1 contains all delete relaxed reachable atoms

    # Step 2 -- Obtain mutex groups, based on the mutex groups create datalog rules
    #           that match the desired LP description
    print("=== Step 2 ===")
    create_mutex_rules(domain, problem, tmp_file6, cpddl_log)
    get_action_conditions_with_add_del(domain, problem, tmp_file3)
    linearize_action_task(tmp_file3, tmp_file2)
    concat_theory(tmp_file6, tmp_file2, tmp_file8)

    filter_add_del_annotation(tmp_file8, tmp_file25)  #TODO: should write some tests for this
    # tmp_file9 contains naive encoding, corresponding to the LP rules without any splitting,
    # with the corresponding annoation which add/del are guaranteed
    stash_annotation_hack(tmp_file25, tmp_file26, model_file_10, tmp_file9)
    # tmp_file26 contains hack annotation
    # model_file_10 contains hack annotation as fulfilled atoms

    # hack to add all add/del atoms for the already existing atoms
    integrate_add_del_rules(tmp_file9, tmp_file4)
    combine_action_atoms(tmp_file4, model_file_1, tmp_file15)
    lp_ground(tmp_file15, model_file_11)
    concat_files(model_file_10, model_file_11, model_file_5) # forward init atoms from mutex annotation hack

    # Step 3 -- Use the tree decomposition optimizer on the datalog rules matching the LP description and
    #           ground the representation
    print("=== Step 3 ===")
    atoms_and_rules_only(tmp_file9, tmp_file10) # removes mutex annoation
    combine_action_atoms(tmp_file10, model_file_5, tmp_file7) # add all delete-relaxed reachable atoms as initial state
    lpopt_optimize(tmp_file7)
    #TODO: option to binarize_rules(tmp_file4, tmp_file13)
    #TODO: or option to use the iterated grounding with superset pars
    superset_pars(tmp_file7, tmp_file13)
    lp_ground(tmp_file13, model_file_2)

    # Step 4 -- Reduce the datalog representation of the LP similar to the reduction step in a full reducer
    print("=== Step 4 ===")
    #combine_action_atoms(tmp_file13, model_file_2, tmp_file11)
    # TODO: remove obviously unnesc rules like the artif. del add rules
    #reduce(tmp_file11, tmp_file5)
    #lp_ground(tmp_file5, model_file_3)
    #only_keep_reduced(model_file_3, model_file_4)
    # TODO prune zero rules upward/downward

    # Step 4.5 -- Extend goal rule
    print("=== Step 4.5 ===")
    combine_action_atoms(tmp_file13, model_file_2, tmp_file12)
    combine_action_action_atoms(tmp_file12, tmp_file6, tmp_file17)
    rm_rules(tmp_file17, tmp_file29)
    equalize_add_guaranteed_atoms(tmp_file29, tmp_file28)
    equalize_guaranteed_atoms(tmp_file28, tmp_file19)

    lp_ground(tmp_file19, model_file_6)
    assert subset_atoms(tmp_file19, model_file_6)
    cut_off_guaranteed(model_file_6, model_file_7)

    append_files(model_file_7, tmp_file22, tmp_file42)
    add_mutex_max_rules(tmp_file42, tmp_file27)
    lp_ground(tmp_file27, model_file_8)
    assert subset_atoms(tmp_file27, model_file_8)
    cut_off_max_mutex(model_file_8, model_file_9)
    append_files(model_file_7, tmp_file17, tmp_file18)
    append_files(model_file_9, tmp_file18, tmp_file23)
    add_mutex_max_rule_from_file(tmp_file16, tmp_file23, tmp_file21)
    extend_goal_rule(tmp_file21, tmp_file40)
    stash_annotation_hack(tmp_file40, tmp_file39, model_file_12, tmp_file20)
    # tmp_file39 contains hack annotation
    # model_file_12 can be ignored
    concat_files(tmp_file39, tmp_file26, tmp_file41)

    atoms_and_rules_only(tmp_file20, tmp_file30)

    # Step 4.75 -- Extend action rules according to mutex
    print("=== Step 4.75 ===")
    # tmp_file41 contains extended hack annotation
    concat_files(tmp_file30, tmp_file41, tmp_file31)
    reintegrate_mutex_rules(tmp_file31, tmp_file32)
    concat_files(tmp_file6, tmp_file32, tmp_file33) # combine with original mutex rules
    order_rules_first(tmp_file33, tmp_file37, tmp_file36, tmp_file35)
    if ADD_NONE_ATOMS:
        add_none_rules(tmp_file35, tmp_file34)
    else:
        add_hacky_zero_if_not_unique(tmp_file35, tmp_file34)
    atoms_and_rules_only(tmp_file34, tmp_file24)

    # Step 5 -- Create the LP Representation
    print("=== Step 5 ===")
    # hack to encode original intital state that should be marked as maximization criterion -- TODO: add other options for maximization
    add_maximization_atoms(tmp_file24, tmp_file1, tmp_file14)
    minizinc_constraints(tmp_file14, lp_rules)


    #TODO: could do some cleanup here: e.g.:
    # - deleting unreachable rules
    # - remvoing +/- the same value (add_ and del_ in one rule)
    # - removing 0-values as far as possible

    # Step 6 -- Pass to LP solver
    print("=== Step 6 ===")

    with open(pot_map, 'w') as file:
        #subprocess.check_call([get_zinc_executable(), "--solver", "COIN-BC", lp_rules], stdout=file)
        #subprocess.check_call([get_zinc_executable(), "--solver", "Gecode", lp_rules], stdout=file)
        subprocess.check_call([get_zinc_executable(), "--solver", "CPLEX", "--cplex-dll", get_cplex_dll(), lp_rules], stdout=file)

    print("Potentials printed to", pot_map)

    # Step 7 -- Append mutex info
    print("=== Step 7 ===")
    if PRINT_MUTEXES:
        print_grounded_mutexes(tmp_file14, tmp_file38)
        concat_files(pot_map, tmp_file38, pot_output)
    else:
        shutil.copyfile(pot_map, pot_output)

    print("Final output was printed to", pot_output)


    print("=== Potential computation done ===")


if __name__ == '__main__':
    if len(sys.argv) == 4:
        _, domain, problem, outp = tuple(sys.argv)
        generate(domain, problem, outp)
    else:
        print("Call with <domain> <problem> <outpfile>")

        exit(1)
