# Lifted-White Plan Domain Repair

This repository implements the Lifted White Plan Domain Repair framework, providing tools to repair planning domains using lifted and partial grounding techniques. It supports multiple search algorithms, heuristic relaxations, structured logging, and batch execution of repair experiments.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Batch Solver](#batch-solver)
  - [Single Instance Solver](#single-instance-solver)
  - [Log Processing](#log-processing)
- [Directory Structure](#directory-structure)
- [Documentation](#documentation)
- [Tests](#tests)

## Features
- Batch processing of planning domain repair tasks with `batch_solver.py`.
- Single-instance execution with `instance_solver.py`.
- Supports lifted planning, ground repair, and partial grounding.
- Configurable search algorithms: A*, Greedy, DFS, Branch and Bound.
- Heuristic relaxations: zeroary, null, unary.
- Structured YAML logging and log-to-table utilities.

## Installation
Ensure you have Python 3.7+ and the following dependencies:

```bash
pip install pyyaml psutil
```

Install the package in editable mode:

```bash
git clone <repo-url>
cd lifted-white-plan-domain-repair
pip install -e .
```

## Configuration
Edit `config.yaml` in the project root to set experiment parameters:

```yaml
search_algorithm: g_astar
heuristic_relaxation: unary
lift_prob: 1.0
instance_ids: null
min_length: 1
max_length: 15
timeout_seconds: 900  # 15 minutes
order: increasing
benchmark_path: /path/to/benchmarks
log_folder: /path/to/output/logs
log_interval: 1000000
domain_class: null
```
【F:config.yaml†L4-L15】【F:config.yaml†L18-L35】

Supported values for configuration parameters are documented in `config.yaml`.

## Usage

### Batch Solver
Run batch experiments over a set of benchmark instances:

```bash
python -u batch_solver.py [path/to/config.yaml]
```
we used batch solver to run parallel solvers in a High performance computing server with many CPUs. It should be able to automatically check the number of available CPUs, but note that we have limited the RAM usage in instance_solver.py to 8GB and you have to be careful that you have enough RAM compared to the number of CPUs.
The batch solver reads the configuration, distributes instances across available CPUs, and writes per-instance YAML logs to the configured `log_folder`.
We have used 'container/source/ecai-os-python.def' to build a singularity image as a starting point to run on HPC.

### simplified batch solver
We have created a simplified version of batch_solver, since that's a long complex file. For using only one CPU to solve a folder of problems you can use main.py like this:
```bash
python -u main.py [path/to/config.yaml]
```

### Single Instance Solver
Solve a single instance identified by `<instance_id>`:

```bash
python -u instance_solver.py config.yaml <instance_id>
```

Use `instance_ids.json` (or your own list) to discover valid identifiers for your benchmarks.

### Log Processing
Convert generated YAML logs into CSV or tables:

```bash
# Generate a combined CSV summary:
python -u log_reader.py              > summary.csv

# Create a plain-text table:
python -u log_to_table.py <logs_dir> > table.txt

# Generate a LaTeX table:
python -u log_table_to_latex.py <logs_dir> > table.tex
```

Additional log utilities: `log_merger.py`, `log_table_to_latex_maxh.py`.

## Directory Structure

```
. 
├── batch_solver.py
├── instance_solver.py
├── config.yaml
├── custom_logger.py
├── exptools/                # Experiment utilities for instance and data management
├── heuristic_tools/         # Heuristic implementations and auxiliary files
├── relaxation_generator/    # Heuristic relaxation generators
├── repairer/                # Ground repair implementations
├── search_partial_grounding/ # Partial grounding search framework
├── model/                   # PDDL domain and task models
├── log_reader.py            # Log-to-CSV converter
├── log_to_table.py          # Formatter for log-based tables
├── log_table_to_latex.py    # LaTeX table generator from logs
├── tests/                   # Test suite (pytest)
└── utils/                   # Supporting utility modules
```

## Documentation
Additional documentation (e.g., heuristic research notes) is available in the `documentation/` folder.

## Tests
Run the test suite:

```bash
pytest tests/
```

## License
Specify license information here, if applicable.


## Build and using the code - without heuristic
We recomment using our docker image here: TODO add
install python Python 3.8.20, and install the packages in requirement.txt (for example by running pip install -r requirements.txt).
If you use algorithms that don't use heuristic (bfs (ucs), dfs), it should be enough to run the code like this:
python instance_solver.py config.yaml barman-mco14-strips__pp1-8-4-10-err-rate-0-1
#TODO: add how IDs are generated
#TODO: mention that batch_solver is for HPC.

### if you need the heuristic
We recomment using our docker image here: TODO add
However, you can also use the instructions below to build
You will need to build some libraries first:
* lpopt for tree decomposition optimization
    * Vienna university website
    * I printed the whole page, passed to Claude, got the installation commands
    * For lpopt I have a gist here
    * Me: You have to install htd first. Don’t install that in the default usr folder. Do it in another one and don’t use sudo. Then add the new folder to your Path. This is in my .bashrc:
        * # Custom PATH, LD_LIBRARY_PATH, and PKG_CONFIG_PATH
        * export PATH=$HOME/.local/bin:$PATH
        * export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH
        * export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
* Fast Downward: need to compile
    * The fd2 folder
* Powerlifted: need to compile
    * The pwl folder
* Clingo/Gringo for grounding
    * Linux package managers offer that, sources can be found in the university of vienna Github repo

## limitations
Note that in our codebase we use 'bfs', while it is really uniform cost search (UCS). We are aware that it needs refactoring, but if we do that all the experimental results and logs that we generated to publish the paper will still need a layer of confusion.
we are planning to fix this in a later version.


## to add
use_ff: False when the alg is bfs dfs, else can be true



TODO explain what checkpoints are in the logs folder.
TODO explain about CPU and mem limits... if they wanna use batch solver
also provided simplified main.py

TODO remove instance_ids.json and the option in the config that uses it.
TODO add license
TODO explain the folder structure assumption for dataset and how lifted whiteplans can be defined
TODO search for all todos
TODO commit the current changes
TODO add scripts from the server to the repo.
TODO change bfs to ucs?
Add: you can use the singularity container but you may have to run additional commands to install the project dependencies.
We have also included a set of useful commands in...