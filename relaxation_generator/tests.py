import os
import sys
import subprocess
from utils import find_domain_filename
from shortcuts import *

def standard_test_start(domain, problem, all_output, call_f, opt_model=None):
    tmp_file1 = get_tmp_file("1.theory")
    tmp_file2 = get_tmp_file("2.theory")

    def return_wrap(msg):
        return msg, tmp_file1, tmp_file2

    try:
        ground(domain, problem, tmp_file1, opt_model)
    except Exception as e:
        if all_output:
            print(e)
        return return_wrap("ground threw exception")
    try:
        call_f(tmp_file1, tmp_file2)
    except Exception as e:
        if all_output:
            print(e)
        return return_wrap("read_write threw exception")

    return return_wrap(None)


def mutex_printout_equal(domain, problem, all_output=False):
    base_theory = get_tmp_file("3.theory")

    danfis_mutex = get_tmp_file("1.mutex")
    mutexes_as_dl = get_tmp_file("1.theory")
    mutexes_as_dl_extended = get_tmp_file("4.theory")
    theory_file = get_tmp_file("2.theory")

    try:
        create_mutex_rules(domain, problem, mutexes_as_dl, danfis_mutex)
    except Exception as e:
        if all_output:
            print(e)
        return "Wasn't able to create mutexes."

    if all_output:
        print("CPDDL call sucesful.")

    try:
        ground(domain, problem, base_theory)
    except Exception as e:
        if all_output:
            print(e)
        return "ground threw exception"
    
    try:
        concat_theory(mutexes_as_dl, base_theory, mutexes_as_dl_extended)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to cancat theory files"

    try:
        read_write(mutexes_as_dl_extended, theory_file)
    except Exception as e:
        if all_output:
            print(e)
        return "Wasn't able to read write mutex theory file."

    if not mutex_printout_equal_check(theory_file, danfis_mutex, all_output):
        return "mutex groups were not equal"
    
    if all_output:
        print("Check done.")

    return None


def naive_del_comparison(domain, problem, all_output=False):
    base_theory = get_tmp_file("1.theory")
    mutexes_as_dl = get_tmp_file("5.theory")
    base_theory_with_mutex = get_tmp_file("2.theory")

    transformer_result = get_tmp_file("3.theory")
    naive = get_tmp_file("4.theory")

    try:
        get_action_conditions_with_add_del(domain, problem, base_theory)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to create theory file"

    try:
        create_mutex_rules(domain, problem, mutexes_as_dl)
    except Exception as e:
        if all_output:
            print(e)
        return "Wasn't able to create mutexes."

    try:
        concat_theory(mutexes_as_dl, base_theory, base_theory_with_mutex)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to append mutex file"
    
    try:
        filter_add_del_annotation(base_theory_with_mutex, transformer_result)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to perform mutex transformation"
    
    try:
        naive_del_filter(base_theory, naive)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to perform naive del annotation"

    if not same_dels(naive, transformer_result, all_output):
        return "del annotations did not match"

    return None


def reducer_test(domain, problem, all_output=False):
    model_file_1 = get_tmp_file("1.model")
    model_file_2 = get_tmp_file("2.model")

    tmp_file1 = get_tmp_file("1.theory")
    tmp_file2 = get_tmp_file("2.theory")
    tmp_file3 = get_tmp_file("3.theory")
    tmp_file4 = get_tmp_file("4.theory")
    tmp_file5 = get_tmp_file("5.theory")

    try:
        ground(domain, problem, tmp_file1, model_file_1)
    except Exception as e:
        if all_output:
            print(e)
        return "ground threw exception"

    try:
        create_action_theory(domain, problem, tmp_file3)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to create action theory model"

    try:
        linearize_action_task(tmp_file3, tmp_file2)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to create action theory model"

    try:
        reduce(tmp_file2, tmp_file5)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't to build reducer theory"

    try:
        combine_action_atoms(tmp_file5, model_file_1, tmp_file4)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to create action theory model"

    try:
        lp_ground(tmp_file4, model_file_2)
    except Exception as e:
        if all_output:
            print(e)
        return "ground (2) threw exception"

    try:
        only_keep_reduced(model_file_2)
    except Exception as e:
        if all_output:
            print(e)
        return "wasn't able to adjust model file according to reduced atoms"

    if not atoms_supset(model_file_1, model_file_2, all_output):
        if all_output:
            print_atom_diff(model_file_1, model_file_2)
        return "no valid superset"

    if not properly_reduced(model_file_2, tmp_file3):
        return "not properly reduced"

    return None


def read_write_output_equal(domain, problem, all_output=False):
    msg, tmp_file1, tmp_file2 = standard_test_start(domain, problem, all_output, read_write)
    
    if msg:
        return msg

    if not atoms_match(tmp_file1, tmp_file2):
        if all_output:
            print_atom_diff(tmp_file1, tmp_file2)
        return "atoms do not match"

    if not rules_match(tmp_file1, tmp_file2):
        if all_output:
            print_rule_diff(tmp_file1, tmp_file2)
        return "rules do not match"

    return None


def traverse_directory(directory_path, test_f, err_seen):
    files = [item for item in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, item)) and item.endswith('.pddl')]
    folder = [item for item in os.listdir(directory_path) if not os.path.isfile(os.path.join(directory_path, item))]
    sorted_files = list(sorted(files, key=lambda f: os.path.getsize(os.path.join(directory_path, f))))[:2]
    for item in sorted_files:
        item_path = os.path.join(directory_path, item)
        if '-d' not in item and 'domain' not in item:
            domain = find_domain_filename(item_path)
            print("calling", domain, item_path, test_f.__name__)
            err = test_f(domain, item_path)
            if err:
                err_seen.append((err, domain, item_path))
                print("returned err msg", (err))
        
    for item in folder:
        item_path = os.path.join(directory_path, item)
        traverse_directory(item_path, test_f, err_seen)  


TESTS = [
    read_write_output_equal,
    reducer_test,
    mutex_printout_equal,
    naive_del_comparison
]
HTG_DOMAINS = "../htg-domains/"


if __name__ == '__main__':
    if len(sys.argv) == 1 or len(sys.argv) == 2:
        if len(sys.argv) == 2 and sys.argv[1] not in locals():
            print("Test function", sys.argv[1], "unknown")
            exit(1)
        tests = TESTS if len(sys.argv) == 1 else [locals()[sys.argv[1]]]
        print("running tests on all htg domains for the followin test functions:")
        for f in tests:
            print(f.__name__)
        errs = []
        for test in tests:
            err = []
            traverse_directory(HTG_DOMAINS, test, err)
            errs += [(test, e) for e in err]

        if len(errs) == 0:
            print("All tests sucessful.")
        else:
            for func, (err, domain, problem) in errs:
                print("=== List of errors ===")
                print(f"Function {func.__name__} led to error {err} on domain {domain} and problem {problem}")
    elif len(sys.argv) == 4:
        _, func, domain, problem = tuple(sys.argv)
        outp = locals()[func](domain, problem, True)
        print("Output was:", outp)
    else:
        print("""Either call without arguments to execute all tests 
or pass <func_name> to run only func_name tests
or pass <func_name> <domain> <problem> to execute this exact test with additional info
        """)

        exit(1)
