#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import uuid

from shortcuts import lpopt_optimize

from subprocess import Popen, PIPE

import pkg_resources
pkg_resources.require("tarski==0.4.0")
from tarski.reachability import create_reachability_lp, run_clingo
from tarski.theories import Theory
from tarski.utils.command import silentremove, execute
from tarski.syntax.transform.universal_effect_elimination import expand_universal_effect, compile_universal_effects_away

from utils import *

if __name__ == '__main__':
    args = parse_arguments()

    domain_file = args.domain
    instance_file = args.instance
    if not os.path.isfile(domain_file):
        sys.stderr.write("Error: Domain file does not exist.\n")
        sys.exit()
    if not os.path.isfile(instance_file):
        sys.stderr.write("Error: Instance file does not exist.\n")
        sys.exit()

    theory_output = args.theory_output
    theory_output_with_actions = args.theory_output.replace(".theory", "-with-actions.theory")
    print("Saving extra copy of theory with actions to %s" % theory_output_with_actions)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if args.fd_split or args.htd_split:
        command = [dir_path+'/src/translate/pddl_to_prolog.py', domain_file, instance_file]
        if args.htd_split:
            command.extend(['--htd', '--only-output-htd-program'])
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)
    else:
        command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
                 instance_file, '--only-output-direct-program']
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)

    # Produces extra theory file with actions
    command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
                 instance_file, '--only-output-direct-program']
    if args.inequality_rules:
        command.extend(['--inequality-rules'])
    execute(command, stdout=theory_output_with_actions)
    print("ASP model *with actions* being copied to %s" % theory_output_with_actions)

    assert False, "TODO: integrate actions"
    assert False, "TODO: use relaxation"

    if args.lpopt_preprocessor:
        lpopt_optimize(theory_output)

    assert False, "TODO: superset actions"

    grounderopt = args.grounder
    if grounderopt != 'none':
        model_output = args.model_output
        suppress_output = args.suppress_output

        run_grounder(model_output, suppress_output, theory_output, grounderopt)

    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
