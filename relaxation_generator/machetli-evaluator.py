import os.path
from shortcuts import get_machetli_info_file, get_tmp_file, call_test_and_write_to, get_output_was

from machetli import pddl, tools
import tests
import pickle

def evaluate(state):
    with open(get_machetli_info_file(), "rb") as f:
        data = pickle.load(f)
        first_output = data['last_output']
        test_f = data['test_f']
        first_run_time_err = data['run_time_err']

    with pddl.temporary_files(state) as (domain_filename, problem_filename):
        tmp_file = get_tmp_file('run.log')
        err_file = get_tmp_file('run.err')
        call_test_and_write_to(test_f, problem_filename, domain_filename, tmp_file, err_file)
        outp = get_output_was(tmp_file)
        run_time_err = os.stat(err_file).st_size == 0

        return outp == first_output and run_time_err == first_run_time_err