import os.path
import sys
import pickle
from shortcuts import get_machetli_info_file, get_tmp_file, CURRENT_DIR, call_test_and_write_to, get_output_was
from machetli import pddl, search

def run_machetli(test_f, domain, problem):
    initial_state = pddl.generate_initial_state(domain, problem)
    successor_generators = [pddl.RemoveActions(), pddl.RemoveObjects(), pddl.RemovePredicates(replace_with="true")]
    evaluator_filename = os.path.join(CURRENT_DIR, "machetli-evaluator.py")

    tmp_file = get_tmp_file('run.log')
    err_file = get_tmp_file('run.err')
    call_test_and_write_to(test_f, problem, domain, tmp_file, err_file)
    outp = get_output_was(tmp_file)
    run_time_err = os.stat(err_file).st_size == 0

    with open(get_machetli_info_file(), "wb") as f:
        pickle.dump({
            'last_output': outp,
            'test_f': test_f,
            'run_time_err': run_time_err
        }, f)

    result = search(initial_state, successor_generators, evaluator_filename)

    d = os.path.join(CURRENT_DIR, "reduced_domain.pddl")
    p = os.path.join(CURRENT_DIR, "reduced_problem.pddl")
    pddl.write_files(result, d, p)

if __name__ == '__main__':
    if len(sys.argv) == 4:
        _, func, domain, problem = tuple(sys.argv)
        run_machetli(func, domain, problem)
    else:
        print("Call <func_name> <domain> <problem> to create a reduced domain, problem for w.r.t. func.")
        exit(1)


