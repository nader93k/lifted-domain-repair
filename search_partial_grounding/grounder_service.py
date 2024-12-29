# this has to be called as a separate process with a separate python interpreted with tarski Version: 0.8.2 installed
# with did this to avoid conflict with tarski==0.4.0 required by our project.
#TODO: review this before release.

import sys
import argparse
from pathlib import Path
from lifted_pddl import Parser


def main():
    arg_parser = argparse.ArgumentParser(description='Returns possible groundings for an action schema.')
    arg_parser.add_argument('--domain_path', required=True, help='Path to input domain in RAM disk')
    arg_parser.add_argument('--task_path', required=True, help='Path to input task in RAM disk')
    args = arg_parser.parse_args()
    
    try:        
        parser = Parser()
        parser.parse_domain(args.domain_path)
        parser.parse_problem(args.task_path)
        actions = parser.get_applicable_actions()
        grounded_actions = parser.encode_ground_actions_as_pddl(actions, 'str')   
        print(grounded_actions)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()