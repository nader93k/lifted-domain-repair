from shortcuts import *

def generate(domain, problem, outpfile):
    model_file_1 = get_tmp_file("1.model")
    model_file_2 = get_tmp_file("2.model")
    model_file_5 = get_tmp_file("5.model")
    model_file_10 = get_tmp_file("10.model")
    model_file_11 = get_tmp_file("11.model")

    tmp_file1 = get_tmp_file("1.theory")
    tmp_file2 = get_tmp_file("2.theory")
    tmp_file3 = get_tmp_file("3.theory")
    tmp_file4 = get_tmp_file("4.theory")
    tmp_file6 = get_tmp_file("6.theory")
    tmp_file7 = get_tmp_file("7.theory")
    tmp_file8 = get_tmp_file("8.theory")
    tmp_file9 = get_tmp_file("9.theory")
    tmp_file10 = get_tmp_file("10.theory")
    tmp_file13 = get_tmp_file("13.theory")
    tmp_file15 = get_tmp_file("15.theory")
    tmp_file25 = get_tmp_file("25.theory")
    tmp_file26 = get_tmp_file("26.theory")

    cpddl_log = get_tmp_file("cpddl.log")

    ground(domain, problem, tmp_file1, model_file_1, True)
    create_mutex_rules(domain, problem, tmp_file6, cpddl_log)
    get_action_conditions_with_add_del(domain, problem, tmp_file3)
    linearize_action_task(tmp_file3, tmp_file2)
    concat_theory(tmp_file6, tmp_file2, tmp_file8)

    filter_add_del_annotation(tmp_file8, tmp_file25)
    stash_annotation_hack(tmp_file25, tmp_file26, model_file_10, tmp_file9)

    integrate_add_del_rules(tmp_file9, tmp_file4)
    combine_action_atoms(tmp_file4, model_file_1, tmp_file15)
    lp_ground(tmp_file15, model_file_11)
    concat_files(model_file_10, model_file_11, model_file_5)

    atoms_and_rules_only(tmp_file9, tmp_file10)
    combine_action_atoms(tmp_file10, model_file_5, tmp_file7)
    lpopt_optimize(tmp_file7)
    superset_pars(tmp_file7, tmp_file13)
    lp_ground(tmp_file13, model_file_2)

    #combine_action_atoms(tmp_file13, model_file_2, tmp_file11)
    #reduce(tmp_file11, tmp_file5)
    #lp_ground(tmp_file5, model_file_3)
    #only_keep_reduced(model_file_3, model_file_4)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        _, domain, problem, outp = tuple(sys.argv)
        generate(domain, problem, outp)
    else:
        print("Call with <domain> <problem> <outpfile>")

        exit(1)
