from lifted_pddl import Parser


parser = Parser()
parser.parse_domain('./debug_data_2/mprime/domain-pprob31-err-rate-0-5.pddl')

# Parse logistics problem
parser.parse_problem('./debug_data_2/mprime/pprob31-err-rate-0-5.pddl')
print("\nApplicable actions in PDDL format:\n", parser.encode_ground_actions_as_pddl(parser.get_applicable_actions(), 'str'))
