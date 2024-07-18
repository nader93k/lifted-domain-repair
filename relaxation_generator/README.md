Pascal (L.) says: 
This whole thing was copied from another project of mine. 
Please let me do a clean-up pass before publishing this.

The repository builds on the work of Corrêa et al. (ICAPS 2023)., we should make it clear
that we re-used the code. 

---

# ASP encoding to ground planning tasks

Encodes the relaxed-reachability of a PDDL planning task as a logic program. The
canonical model of this program is equivalent to all reachable atoms (and
actions). This can be used to find all possible ground atoms that are
relaxed-reachable in the planning task. In fact, this is how Fast Downward
grounds the input tasks. Similarly, this is how Powerlifted extracts
delete-relaxation heurisitics without grounding the problem.

You can either do the traditional grounding in one pass or do a two-step
grounding, which is slower but can ground larger tasks. For details, see Corrêa et al. (ICAPS 2023).

## Installation

We recommend using a Python virtual environment. You need to use Python >= 3.7 to execute the scripts.  Once inside the virtual
environment, you can run

```bash
$ python setup.py install
```

or

```bash
$ pip install -e .
```

while in the root directory of the repository. You also need to have the
grounder you want to use in your PATH (see below).

## Basic Usage

There are two main scripts in the repo: `generate-asp-model.py` and
`count-ground-actions.py`. The first one simply encodes the task as a Datalog
program (with some options) and then grounds it using some off-the-shelf
grounder; the second one counts or grounds (depending on the parameters) the
*actions* of the task given a set of relaxed-reachable atoms. Usually, to run
`count-ground-actions.py`, you need to have the output model from `generate-asp-model.py`
stored.

To run the program `generate-asp-model`, execute

```bash
$ ./generate-asp-model.py -i /path/to/instance.pddl [-m MODEL-OUTPUT] [-t THEORY-OUTPUT]
```

where `/path/to/instance.pddl` is the path to a *PDDL instance*. It is necessary
that there is a PDDL domain file in the same directory as `instance.pddl`,
though. The script will infer the domain file automatically or you can pass it
with parameter `-d`.

The program will generate the Datalog encoding corresponding to the PDDL task
and ground it using some selected grounder (default: `gringo` - [get here](https://potassco.org/clingo/)). The Datalog file
will be saved in `MODEL-OUTPUT` (default: `output.theory`); the canonical model
(together with any other output from the grounder) will be saved in
`THEORY-OUTPUT` (default: `output.model`).

There are some extra options one can use:

- `--ground-actions`: Use the encoding from Helmert (AIJ 2009) where action
  predicates are listed explcitly.
- `--grounder`: Select grounder to be used to ground the Datalog
  program. Current options are `clingo`, `gringo`, `idlv`, and `newground`. You must
  have the selected grounder on the `PATH`. (Default: `gringo`)
- `--lpopt-preprocessor`: Uses the `lpopt` preprocessor to rewrite the Datalog
  program. This option expects an environment variable called `LPOPT_BIN_PATH`
  to point to the binary file of `lpopt`. [(get here)](https://dbai.tuwien.ac.at/proj/lpopt/)
- `--fd-split`: Uses Fast Downward preprocessor to split rules of the Datalog
  program. This uses the method by Helmert (AIJ 2009).
- `--htd-split`: (This option is not fully functional yet.) Splits the rules
  based on the hypertree decompositions of the rule bodies. It expects
  `BalancedGo` to be on the `PATH`.


To run the `count-ground-actions program` for upper-bounding the number of
action atoms in the grounding and for computing alternative groundings, you
must set the following environment variables:

- `LPCNT_AUX_PATH` pointing to `/path/to/repo/build/bdist.linux-x86_64`.
- `GRINGO_BIN_PATH` pointing to `gringo`.
- `CLINGO_BIN_PATH` pointing to `clingo`.
- `LPCNT_BIN_PATH` pointing to the desired counting/solving script.

Then, you can execute

```bash
$ ./ count-ground-actions.py -m MODEL-OUTPUT -t THEORY-WITH-ACTIONS [--choices] [--output] [--extendedOutput] [--counter-path SCRIPT]
```

where `MODEL-OUTPUT` is the path to the `MODEL-OUTPUT` obtained with a call to
the program above, and `THEORY-WITH-ACTIONS` is the path to the theory file
containing action predicates obtained by the same call above (this file is
automatically generated with the name `output-with-actions.theory` by the
`generate-asp-model.py` script).

The key to this program is the counting/solving script used. The ones used in
the experiments (Corrêa et al. ICAPS 2023) are:
- `lpcnt`: Simple counting script to count number of ground actions. Outputs
  with `+` Sign indicate a lower bound.
- `lpgrnd`: Grounding via solving (see Corrêa et al. ICAPS 2023). But note that
  this script *does not output the model by default*. This is on purpose because
  some of the instances in the tested benchmark produce files larger than 10
  GiB.
- `lpgrnd_io`: Same as `lpgrnd` but outputting all ground actions. *Be careful
  to not produce very large files.*

There are other counting scripts in the codebase (`lpcnt_nopp`, `lpcnt_omni`,
`lpcnt_opt`). They are different configurations that might work better for
specific instances. However, they were not used in the aforementioned
experiments.


There are some extra options that one can optionally turn on:

- `--choices`: Use ASP choice rules, which is an alternative encoding that
  directly uses ASP choices, instead of SAT-like rules for guessing / deciding
  whether an action is contained in the grounding.
- `--output`: Compute the alternative grounding encoding and write it to stdout.
- `--extendedOutput`: Compute an alternative (extended) grounding encoding and
  write it to stdout.
- `--counter-path`: Set the used counting solver environment variable,
  giving the execution path within the path specified by the environment variable `VAR`.
   This option expects that `SCRIPT` points to a valid script for counting/solving. (default: `LPCNT_BIN_PATH`)
