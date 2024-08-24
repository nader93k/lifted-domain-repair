import sys
import subprocess
import os

CURRENT_FILE_PATH = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE_PATH)
TRANSLATOR_PY = os.path.join(CURRENT_DIR, "fd", "translate.py")

if len(sys.argv) != 4:
    print("Call with: validate_relaxed_plan.py <domain> <problem> <plan>")
    exit(1)

_, domain, problem, plan = sys.argv

DUMP_DOMAIN = "dump_domain.pddl"
DUMP_PROBLEM = "dump_problem.pddl"

get_relaxed_pddl = ["python3", TRANSLATOR_PY, domain, problem, "--dump-pddl", "--relaxed"]
print("Calling", *get_relaxed_pddl)
subprocess.check_call(get_relaxed_pddl)

print("==== FILES DUMPED ====")
print("==== STARTING VALIDATION ====")

def normalize(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()

    modified_content = file_content.replace("(= ", "(hack_equal ")
    modified_content = modified_content.replace("(hack_equal (total-cost", "(= (total-cost")
    
    with open(file_path, 'w') as file:
        file.write(modified_content)

normalize(DUMP_DOMAIN)
normalize(DUMP_PROBLEM)

validate = ["validate", DUMP_DOMAIN, DUMP_PROBLEM, plan]
print("Calling", *validate)
subprocess.check_call(validate)
