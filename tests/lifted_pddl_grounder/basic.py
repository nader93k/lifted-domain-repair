from lifted_pddl import Parser


# /home/projects/u7899572/conda-envs/grounder/bin/python3 tests/lifted_pddl_grounder/basic.py
def basic_test():
    parser = Parser()

    # parser.parse_domain('./tests/test_files/lifted_pddl_grounder/mprime/domain-pprob31-err-rate-0-5.pddl')
    # parser.parse_problem('./tests/test_files/lifted_pddl_grounder/mprime/pprob31-err-rate-0-5.pddl')
    
    parser.parse_domain('./tests/lifted_pddl_grounder/test_files/woodworking-opt08-strips/domain-pp01-err-rate-0-1.pddl')
    parser.parse_problem('./tests/lifted_pddl_grounder/test_files/woodworking-opt08-strips/pp01-err-rate-0-1.pddl')


    print("\nApplicable actions in PDDL format:\n", parser.encode_ground_actions_as_pddl(parser.get_applicable_actions(), 'str'))


if __name__ == '__main__':
    basic_test()
