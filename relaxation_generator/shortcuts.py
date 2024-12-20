import pkg_resources
pkg_resources.require("tarski==0.4.0")

import os, sys
import subprocess
from pathlib import Path
try:
    from .utils import run_grounder, find_lpopt
except ImportError:
    from utils import run_grounder, find_lpopt
from collections import defaultdict
import itertools
import uuid
from tarski.utils.command import execute
import shutil

#dprint = lambda *args, **kwargs: None
dprint = print

CURRENT_FILE_PATH = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE_PATH)
#TMP_DIR = os.path.join(CURRENT_DIR, ".tmp")
TMP_DIR = ".tmp"
Path(TMP_DIR).mkdir(parents=True, exist_ok=True)

def get_tmp_file(name):
    return os.path.join(TMP_DIR, name)

def get_machetli_info_file():
    return get_tmp_file("static_machetli.info")

def call_test_and_write_to(test_f, problem, domain, tmp_file, err_file):
    if os.path.exists(err_file):
        os.remove(err_file)

    with open(tmp_file, "w") as f:
        with open(err_file, "w") as f_err:
            command = [
                "python3",
                os.path.join(CURRENT_DIR, "tests.py"),
                test_f,
                domain,
                problem
            ]
            subprocess.check_call(command, stdout=f, stderr=f_err)

def get_output_was(tmp_file):
    with open(tmp_file, "r") as f:
        last_outp = None
        for line in f:
            line = line.strip()
            if line.startswith("Output was: "):
                last_outp = line[len("Output was: "):]
        assert last_outp is not None
        return last_outp

def get_action_conditions_with_add_del(domain, problem, outp):
    command = [
        "python3",
        os.path.join(CURRENT_DIR, "src", "translate", "pddl_to_prolog.py"),
        domain,
        problem,
        "--integrate-add-del-to-pre",
        "--only-output-direct-program",
        "--integrate-action-cost"
    ]
    # print("calling", *command)
    with open(outp, "w") as f:
        subprocess.check_call(command, stdout=f)

def lpopt_optimize(f_name):
    lpopt = find_lpopt()
    temporary_filename = str(uuid.uuid4())
    command = [lpopt, "-f", f_name]
    temp_file = open(temporary_filename, "w+t")
    execute(command, stdout=temporary_filename)
    os.rename(temporary_filename, f_name)

def ground(domain, problem, theory_outp=None, model_outp=None, lpopt_enabled=False, domain_print=None, problem_print=None, grounder=None, relaxation=None):
    command = [
        "python3",
        os.path.join(CURRENT_DIR, "generate-asp-model.py"),
        "--instance",
        problem,
        "--domain",
        domain
    ]
    if theory_outp:
        command += [
            "-t",
            theory_outp
        ]
    if model_outp:
        command += [
            "-m",
            model_outp
        ]
    if lpopt_enabled:
        command += [
            "--lpopt-preprocessor"
        ]
    if grounder:
        command += [
            "--grounder",
            grounder
        ]
    if domain_print:
        command += [
            "--domain-print",
            domain_print
        ]
    if problem_print:
        command += [
            "--problem-print",
            problem_print
        ]
    if relaxation:
        command += [
            "--r-mode",
            relaxation
        ]
    dprint("calling", *command)
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        dprint(f"subprocess results: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Error output:\n{e.stderr}")
    subprocess.check_call(command)

def adjust_type_name(_type):
    return _type.replace("-", "__")

def transform_mutex_to_rules(mutex_file, outp):
    """
    Creates datalog rules of the from mutex[_unqiue] :- <mutexgroup>
    """
    with open(mutex_file, "r") as f_in:
        with open(outp, "w") as f:
            for line in f_in:
                if "{" in line:
                    str_inside_set = line[line.find("{")+1:line.find("}")]
                    is_unique = ":=1" in line
                    contents = str_inside_set.split(", ")
                    f.write(f'mutexpred{"_unique" if is_unique else ""}:-')
                    for i, content in enumerate(contents):
                        content_split = content.split(" ")
                        f.write(f'{adjust_type_name(content_split[0])}(')
                        for j, pot_var in enumerate(content_split[1:]):
                            if ":" in pot_var: # is var
                                var, _type = tuple(pot_var.split(":"))
                                _type = adjust_type_name(_type)
                                indicator, num = var[0], var[1:]
                                f.write(f'Var_{"counted" if indicator == "C" else "enumerated"}_{num}_{_type}')
                            else: # is object
                                f.write(pot_var)
                            if j < len(content_split)-2:
                                f.write(',')
                        f.write(')')
                        if i != len(contents)-1:
                            f.write(',')
                    f.write('.\n')

def create_mutex_rules(domain, problem, outp, cpddl_log=None, mutex_file=None):
    if mutex_file is None:
        mutex_file = get_tmp_file("current_mutex_repr.mutex")

    command = [
        os.path.join(CURRENT_DIR, "cpddl", "bin", "pddl"),
    ] + ([
        "--log-out",
        cpddl_log
    ] if cpddl_log else []) + [
        "--lmg-stop", 
        "--lmg-out", 
        mutex_file, 
        domain, 
        problem
    ]
    subprocess.check_call(command)
    transform_mutex_to_rules(mutex_file, outp)

def split_atom_rule_lines(f1):
    atoms_lines = []
    rule_lines = []

    for l in f1:
        if ":-" in l:
            rule_lines.append(l)
        else:
            atoms_lines.append(l)

    return atoms_lines, rule_lines

def concat_theory(_f1, _f2, _to):
    with open(_f1, "r") as f1:
        with open(_f2, "r") as f2:
            with open(_to, "w") as to:
                atoms1, rules1 = split_atom_rule_lines(f1)
                atoms2, rules2 = split_atom_rule_lines(f2)
                
                for l in itertools.chain(atoms1, atoms2, rules1, rules2):
                    to.write(l)

def get_cplex_dll(): # TODO rm code duplication
    for s in ['/data/common/opt/cplex/v12.7.1.0/cplex/bin/x86-64_linux/libcplex1271.so', '/Applications/CPLEX_Studio2211/cplex/bin/arm64_osx/libcplex2211.dylib']:
        if os.path.exists(s):
            return s

    print("Cplex not found")
    sys.exit(-1)

def get_zinc_executable(): # TODO rm code duplication
    for s in ['minizinc', '/data/common/opt/minizinc/2.8.5/bin/minizinc']:
        if shutil.which(s) is not None:
            return s

    print("Minizinc not found")
    sys.exit(-1)

def get_gringo_executable(): # TODO rm code duplication
    for s in ['gringo', '/data/common/opt/clingo/5.7.1/bin/gringo']:
        if shutil.which(s) is not None:
            return s

    print("Gringo not found")
    sys.exit(-1)

def get_grounder_opt():
    return get_gringo_executable()

def lp_ground(theory, model):
    model_output = model
    grounderopt = get_grounder_opt()
    suppress_output = False
    theory_output = theory
    run_grounder(model_output, suppress_output, theory_output, grounderopt)

def _create_tmp(argument):
    return f"{argument}.tmp"

def call_transformer(inp, argument, outp):
    command = [
        os.path.join(CURRENT_DIR, "datalog_transformer_wrap.sh"),
        argument,
        inp
    ]
    # print("calling", *command)

    create_tmp = outp is None
    if create_tmp:
        outp = _create_tmp(argument)

    with open(outp, "w") as f:
        subprocess.check_call(command, stdout=f)

    if create_tmp:
        shutil.copyfile(outp, inp)

def extend_goal_rule(inp, outp):
    call_transformer(inp, "extend-goal-rule", outp)

def reduce(inp, outp):
    call_transformer(inp, "reducer", outp)

def split_var_arg(arg):
    split = tuple(arg.split(":"))
    assert len(split) == 2, split
    v, _type = split
    counted = v[0] == "C"
    num = v[1:]
    return counted, num, _type

def max_var_amount(parts):
    am = 0
    for part in parts:
        for arg in part.split(" ")[1:]:
            if ":" in arg:
                counted, num, _type = split_var_arg(arg)
                num = int(num)
                am = max(num, am)
    return am

def mutex_arg_normalize(arg, unique_type_obj_map, current_type_name_map, iptr):
    assert arg[-1] != " ", arg
    assert arg[-1] != ",", arg
    if ":" in arg:
        counted, num, _type = split_var_arg(arg)
        _type = adjust_type_name(_type)
        return f'{"C" if counted else "V"}{num}:{_type}'
    else:
        if arg in unique_type_obj_map:
            if arg in current_type_name_map:
                return current_type_name_map[arg]
            base = unique_type_obj_map[arg]
            transformed = base % iptr.i
            current_type_name_map[arg] = transformed
            iptr.i += 1
            return transformed
        return arg

class IntPtr:
    def __init__(self):
        self.i = 0

def mutex_el_normalize(part, unique_type_obj_map, current_type_name_map, iptr):
    parts = part.split(" ")
    pred = parts[0]
    args = parts[1:]
    args = [mutex_arg_normalize(arg, unique_type_obj_map, current_type_name_map, iptr) for arg in args]
    return f'{pred} {" ".join(args)}'

def mutex_normalize_process(l, unique_type_obj_map):
    if l.endswith(":S"):
        l = l[:-len(":S")]
    is_unique = l.endswith(":=1")
    if is_unique:
        l = l[:-len(":=1")]
    assert l[0] == "{", (l[0], l)
    assert l[-1] == "}", (l[-1], l)
    l = l[1:-1]
    parts = l.split(", ")
    iptr = IntPtr()
    iptr.i = max_var_amount(parts)
    iptr.i += 1
    current_type_name_map = dict()
    parts = [mutex_el_normalize(part, unique_type_obj_map, current_type_name_map, iptr) for part in parts]
    return f'{{{", ".join(parts)}}}{":=1" if is_unique else ""}'

def to_mutex_list(f, unique_type_obj_map):
    li = []
    less_started = False
    obj_count = defaultdict(lambda: 0)
    last_obj = dict()

    for l in f:
        l = l.strip()
        if l == ">":
            break
        if l == "< >":
            return []
        if l.startswith("<"):
            less_started = True
            if len(unique_type_obj_map) == 0:
                for _type, num in obj_count.items():
                    if num == 1:
                        unique_type_obj_map[last_obj[_type]] = "V%d:" + adjust_type_name(_type)

        if less_started:
            if l:
                if l.startswith("<"):
                    l = l[1:].strip()

                if l.startswith(","):
                    l = l[1:].strip()
                    
                li.append(mutex_normalize_process(l, unique_type_obj_map)) 
        elif ":-" not in l:
            if l.startswith("pddl_type_"):
                l = l[len("pddl_type_"):-1]
                assert l.endswith(")"), l
                l = l[:-1]
                _type, obj = tuple(l.split("("))

                last_obj[_type] = obj
                obj_count[_type] += 1

    li.sort()
    return li

def mutex_printout_equal_check(tmp_file1, tmp_file2, all_output=False):
    # if all_output:
    #     print("Checking mutex printout equal.")

    with open(tmp_file1, "r") as f1:
        with open(tmp_file2, "r") as f2:
            unique_type_obj_map = dict() # assumes tmp_file1 to contain init state

            l1 = to_mutex_list(f1, unique_type_obj_map)
            if all_output:
                print("unique_type_obj_map is", unique_type_obj_map)
            l2 = to_mutex_list(f2, unique_type_obj_map)
            if all_output:
                print("unique_type_obj_map (after call 2) is", unique_type_obj_map)

            if all_output:
                print("List 1 was", l1)
                print("List 2 was", l2)

            if len(l1) != len(l2):
                if all_output:
                    print("Lengths differed.")
                return False
            
            if all_output:
                print("In l1 but not l2:", set(l1).difference(set(l2)))
                print("In l2 but not l1:", set(l2).difference(set(l1)))

            return all(e1 == e2 for e1, e2 in zip(l1, l2))

def read_write(f1, f2):
    call_transformer(f1, "none", f2)

def linearize_action_task(f1, f2):
    call_transformer(f1, "linearize-action-task", f2)

def normalize_atom(atom):
    if "(" not in atom:
        return atom + "()"
    return atom

def normalize_rule(line):
    line = line.replace(":-",",")
    line_copy = [c for c in line]
    depth = 0
    for i, c in enumerate(line):
        if c == "(":
            assert depth == 0, depth
            depth = 1
        elif c == ")":
            assert depth == 1, depth
            depth = 0
        elif c == ",":
            if depth == 0:
                line_copy[i] = ";"
    line = "".join(line_copy)
    line_parts = list(map(normalize_atom,line.split(";")))
    return line_parts[0] + ":-" + ",".join(line_parts[1:])

def get_atoms_and_rules_from_file(f_path):
    atoms = []
    rules = []
    with open(f_path, "r") as f:
        for line in f:
            line = "".join(line.split()) # remove all white spaces ( https://stackoverflow.com/questions/3739909/how-to-strip-all-whitespace-from-string )
            if not line:
                continue
            if line.startswith("<"): # Mutex List
                break
            assert line[-1] == ".", line
            line = line[:-1]
            if ":-" in line:
                line = normalize_rule(line)
                rules.append(line)
            else:
                line = normalize_atom(line)
                atoms.append(line)
    return rules, atoms

def get_atoms_from_file(f):
    return get_atoms_and_rules_from_file(f)[1]

def get_rules_from_file(f):
    return get_atoms_and_rules_from_file(f)[0]

def atoms_match(tmp_file1, tmp_file2):
    a1 = set(get_atoms_from_file(tmp_file1))
    a2 = set(get_atoms_from_file(tmp_file2))
    return a1 == a2

def rules_match(tmp_file1, tmp_file2):
    r1 = set(get_rules_from_file(tmp_file1))
    r2 = set(get_rules_from_file(tmp_file2))
    return r1 == r2

def print_atom_diff(tmp_file1, tmp_file2):
    a1 = set(get_atoms_from_file(tmp_file1))
    a2 = set(get_atoms_from_file(tmp_file2))
    print("In a1 but not a2:", a1.difference(a2))
    print("In a2 but not a1:", a2.difference(a1))

def print_rule_diff(tmp_file1, tmp_file2):
    r1 = set(get_rules_from_file(tmp_file1))
    r2 = set(get_rules_from_file(tmp_file2))
    print("In r1 but not r2:", r1.difference(r2))
    print("In r2 but not r1:", r2.difference(r1))

def atoms_supset(tmp_file1, tmp_file2,all_output=False):
    a1 = set(get_atoms_from_file(tmp_file1))
    a2 = set(get_atoms_from_file(tmp_file2))

    if len(a1) == 0:
        if all_output:
            print("a1 empty")
        return False

    if len(a2) == 0:
        if all_output:
            print("a2 empty")
        return False

    return a1.issuperset(a2)

def filter_add_del_annotation(inp, outp):
    call_transformer(inp, "mutex-filter", outp)

def produce_domain(inp, outp):
    call_transformer(inp, "print-domain", outp)

def produce_problem(inp, outp):
    call_transformer(inp, "print-problem", outp)

def equalize_guaranteed_atoms(inp, outp):
    call_transformer(inp, "equalize-guaranteed-atoms", outp)

def equalize_add_guaranteed_atoms(inp, outp):
    call_transformer(inp, "equalize-add-guaranteed-atoms", outp)

def add_mutex_max_rules(inp, outp):
    call_transformer(inp, "add-max-mutex", outp)

def integrate_add_del_rules(inp, outp):
    call_transformer(inp, "integrate-add-del-rules", outp)

def superset_pars(inp, outp=None):
    call_transformer(inp, "superset-pars", outp)

def minizinc_constraints(inp, outp):
    call_transformer(inp, "minizinc-constraints", outp)

def binarize_rules(inp, outp):
    call_transformer(inp, "binarize-rules", outp)

def reintegrate_mutex_rules(inp, outp):
    call_transformer(inp, "reintegrate-mutex-rules", outp)

def print_grounded_mutexes(inp, outp):
    call_transformer(inp, "print-grounded-mutexes", outp)

def add_none_rules(inp, outp):
    call_transformer(inp, "add-none-rules", outp)

def add_hacky_zero_if_not_unique(inp, outp):
    call_transformer(inp, "add-hacky-zero-if-not-unique", outp)

def add_repair_actions(inp, outp=None):
    call_transformer(inp, "add-repair-actions", outp)

def zero_ary_relaxation(inp, outp=None):
    call_transformer(inp, "zero-ary-relaxation", outp)

def unary_relaxation(inp, outp=None):
    call_transformer(inp, "unary-relaxation", outp)

def split_rule(rule):
    head, body = tuple(rule.split(":-"))
    body = body.split("),")
    body = [cond if cond[-1] == ")" else cond+")" for cond in body]

    return head, body

def remove_adds(rule_li):
    new_rules = []
    for rule in rule_li:
        head, body = split_rule(rule)
        body = [el for el in body if not el.startswith("addpred_")]
        new_rules.append(f'{head}:-{",".join(body)}')

    return new_rules

def naive_del_filter(inp, outp):
    rule_li = get_rules_from_file(inp)
    with open(outp, "w") as f:
        for rule in rule_li:
            head, body = split_rule(rule)
            body_set = set(body)
            body = [el for el in body if not el.startswith("delpred_") or el[len("delpred_"):] in body_set]
            f.write(f'{head}:-{",".join(body)}.\n')

def same_dels(fname_1, fname_2, all_output=False):
    r1 = get_rules_from_file(fname_1)
    r2 = get_rules_from_file(fname_2)
    r1 = remove_adds(r1)
    r2 = remove_adds(r2)
    r1.sort()
    r2.sort()

    if all_output:
        print("List 1 was", r1)
        print("List 2 was", r2)

    if len(r1) != len(r2):
        if all_output:
            print("Lengths differed.")
        return False

    return all(e1 == e2 for e1, e2 in zip(r1, r2))

def only_keep_reduced(_f, __f):
    keep = []
    with open(_f, "r") as f:
        for l in f:
            if l.startswith("reduced_"):
                keep.append(l[len("reduced_"):])

    with open(__f, "w") as f:
        f.write("".join(keep))
def cut_off_generic(_from, _to, check):
    cut_off_i = None
    last_didnt = True

    with open(_from, "r") as f:
        for i, l in enumerate(f):
            if check(l):
                if last_didnt:
                    cut_off_i = i
                last_didnt = False
            else:
                last_didnt = True

    assert cut_off_i != None

    with open(_from, "r") as f:
        with open(_to, "w") as f2:
            for i, l in enumerate(f):
                if i >= cut_off_i:
                    f2.write(l)

def cut_off_guaranteed(_from, _to):
    check = lambda l: (l.startswith("addpred_") or l.startswith("delpred_")) and "guaranteed" in l
    return cut_off_generic(_from, _to, check)

def cut_off_max_mutex(_from, _to):
    check = lambda l: l.startswith("max_mutex_pred") or l.startswith("min_mutex_pred")
    return cut_off_generic(_from, _to, check)

def append_files(one, two, out):
    with open(out, "w") as out_f:
        with open(one, "r") as f:
            for l in f:
                out_f.write(l)
        with open(two, "r") as f:
            for l in f:
                out_f.write(l)

def create_action_theory(domain, problem, outp):
    command = [
        "python3",
        os.path.join(CURRENT_DIR, "src", "translate", "pddl_to_prolog.py"),
        domain,
        problem,
        "--only-output-direct-program"
    ]
    with open(outp, "w") as f:
        subprocess.check_call(command, stdout=f)

def combine_action_action_atoms(full, rules_only, outp):
    shutil.copyfile(full, outp)

    rules = get_rules_from_file(rules_only)
    with open(outp, "a") as f:
        for el in rules:
            f.write(el)
            f.write(".\n")


def combine_action_atoms(action_file, atom_file, outp):
    rules = get_rules_from_file(action_file)
    atoms = get_atoms_from_file(atom_file)

    with open(outp, "w") as f:
        for el in itertools.chain(atoms, rules):
            f.write(el)
            f.write(".\n")

def atoms_and_rules_only(inp, outp):
    with open(inp, "r") as f_in:
        with open(outp, "w") as f_out:
            for l in f_in:
                if l.startswith("<"):
                    break
                f_out.write(l)

def properly_reduced(atom_file, theory_file):
    rules = get_rules_from_file(theory_file)
    atoms = get_atoms_from_file(atom_file)

    assert False, "TODO: implement me :)"

    return True

def add_maximization_atoms(inp, atom_file, outp):
    atoms_for_maximization = get_atoms_from_file(atom_file)
    shutil.copyfile(inp, outp)

    with open(outp, 'a') as outfile:
        outfile.write("optimization__criterion__fact :- " + ", ".join(atoms_for_maximization) + ".")

def stash_annotation_hack(inp, hack_outp, hack_atom_outp, leftover_outp):
    with open(inp, "r") as f_in:
        with open(hack_outp, "w") as hack_out:
            with open(hack_atom_outp, "w") as hack_atom_out:
                with open(leftover_outp, "w") as lo_out:
                    for l in f_in:
                        if l.startswith("handle_not_guaranteed_hack"):
                            if ":-" in l:
                                hack_out.write(l)
                            else:
                                hack_atom_out.write(l)
                        else:
                            lo_out.write(l)

def rm_rules(inp, outp):
    with open(inp, "r") as f_in:
        with open(outp, "w") as out:
            for l in f_in:
                if ":-" not in l:
                    out.write(l)

def subset_atoms(tmp_file, model_file):
    tmp_atoms = get_atoms_from_file(tmp_file)
    model_atoms = get_atoms_from_file(model_file)

    return tmp_atoms == model_atoms[:len(tmp_atoms)]


def add_mutex_max_rule_from_file(mutex_file, append_to, outp):
    shutil.copyfile(append_to, outp)

    rules = get_rules_from_file(mutex_file)
    with open(outp, "a") as f:
        for el in rules:
            f.write(el)
            f.write(".\n")

def concat_files(inp1, inp2, out):
    os.system(f"cat {inp1} {inp2} > {out}")

def order_rules_first(inp, tmp1, tmp2, outp):
    with open(inp, "r") as f_in:
        with open(tmp1, "w") as t1_out:
            with open(tmp2, "w") as t2_out:
                for l in f_in:
                    if ":-" not in l:
                        t1_out.write(l)
                    else:
                        t2_out.write(l)

    concat_files(tmp1, tmp2, outp)