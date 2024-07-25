import sys
import fd.translate as translate
import subprocess
import os

CURRENT_FILE_PATH = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE_PATH)
TRANSLATOR_PY = os.path.join(CURRENT_DIR, "fd", "translate.py")

if len(sys.argv) != 4:
    print("Call with: validate_relaxed_plan.py <domain> <problem> <plan>")
    exit(1)

_, domain, problem, plan = sys.argv

get_relaxed_pddl = ["python3", TRANSLATOR_PY, domain, problem, "--dump-pddl", "--relaxed"]
subprocess.check_call(get_relaxed_pddl)

validate = ["validate", translate.DUMP_DOMAIN, translate.DUMP_PROBLEM, plan]
subprocess.check_call(validate)
