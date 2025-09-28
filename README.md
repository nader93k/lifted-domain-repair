# PDDL Domain Repair with Lifted Test Plans

This repository implements the **Lifted White List Plan Domain Repair framework**, providing tools to repair planning domains using lifted and partial grounding techniques. It supports multiple search algorithms, heuristic relaxations, structured logging, and batch execution of repair experiments.

Our work builds on the baseline repairer from [Songtuan Lin’s *Diagnoser* repository](https://github.com/Songtuan-Lin/diagnoser). We have extended and adapted that implementation to develop the lifted and partial grounding methods described in our [ECAI 2025 paper](#reference).

## Features

- Batch processing of planning domain repair tasks with `batch_solver.py`.
- Single-instance execution with `instance_solver.py`.
- Configurable search algorithms: A*, Greedy, DFS, Uniform-Cost-Search (UCS), Branch and Bound.
- Heuristic relaxations: zeroary, null, unary.
- Structured YAML logging and log-to-table utilities.

## Running by Docker

We provide a pre-built Docker image that should work out of the box:

```bash
docker pull nader93k/ecai2025-repairing-domains:0.1.0
```

This image contains all required dependencies and is the recommended way to get started quickly.

If you need to build the project, please see the explanation below.

## Setting the Environment & Building

This project requires several external tools and libraries in addition to the Python codebase.  
Below is a concise installation guide.

### Python Packages

- Tested with **Python 3.8**.  
- Install dependencies from `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

> ***For **blind search algorithms**, this is sufficient. If you use the heuristic, see the requirements below.***

### lpopt (Tree Decomposition Optimizer)

- Version: 2.2
- Build instructions: [lpopt installation guide](https://dbai.tuwien.ac.at/proj/lpopt/)  
- Requires **HTD** installed first.

#### HTD Installation Notes

- Avoid installing in system directories (e.g., `/usr`).  
- Install in a custom user path without `sudo`.  
- Add the following to your `.bashrc`:

```bash
export PATH=$HOME/.local/bin:$PATH
export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH
export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
```

- Extra build instructions: [HTD gist](https://gist.github.com/PLauerRocks/5e906f05526220b2f67eb11e92ffff92)

### Fast Downward

- Some of the source code from Fast Downward is copied in `./fd2/`.
- Must be compiled manually.
- Repository: [Fast Downward](https://www.fast-downward.org/latest/)  
- Version used: 23.06

### Powerlifted

- The code for this project is copied in `./pwl/`.
- Must be compiled manually.  
- Repository: [Powerlifted](https://github.com/abcorrea/powerlifted)  
- If you had any issues with the latest version, try commit "736b0cd".

### Clingo / Gringo

- Used for grounding.  
- Available through most Linux package managers.  
- Sources available at: [Clingo GitHub](https://github.com/potassco/clingo)

## Configuration

Experiment settings are defined in `config.yaml`. Below is a guide to the most important parameters:

```yaml
#  PART 1: THE MAIN PARAMETERS 

# Search method. Choices:
  #   ucs   = uniform cost search
  #   astar = A* search
  #   g_astar = greedy A*
  #   greedy = greedy best-first
  #   dfs   = depth-first search
  #   bb    = branch & bound
search_algorithm: g_astar        

# Heuristic relaxation type. Choices:
  #   zeroary, null, unary
heuristic_relaxation: unary      
                            
# FF relaxation for the heuristic
use_ff: True                     

# How successor states are generated. Choices:
  #   missing  = RELAX_PRE
  #   missing-and-negative = RELAX_DEL
  #   exhaust  = EXHAUST (see paper).
successor_generator: missing

# Path to benchmark PDDL problems.
benchmark_path: /path/to/benchmarks   

# Folder where logs will be stored.
log_folder: /path/to/output/logs


# Probability (0–1) of lifting action parameters. Useful only if you want to create a lifted benchmark using a grounded one. Set to 0 if the terms your whitelist traces don't need to be randomly lifted.
  #   1.0 = all objects lifted into variables
  #   any 0.0 < P < 1.0: Lift each term with a uniform probability of P.
  #   0.0 = all remain grounded                   
lift_prob: 1.0

# Per-instance time limit in seconds (default: 15 min).
timeout_seconds: 900    



#  PART 2: DEBUG AND HELPER PARAMETERS 

# Frequency of logging (in expansions).
#   Small values for debugging, large values (e.g., 1e6) for normal runs.
log_interval: 1000000    

# Explicit IDs of instances to run. Use null to run all.
# You can set it to a JSON file at the root project folder that contains a list of instance IDs that needs to picked and solved out of a possibly large dataset.
  # Example: filtered.json containing: ["domainName1__problemName1", "domainName1__problemName1"]. Note that the pattern of creating IDs for each instance is `"domainName" + "__" + "problemName"`.
instance_ids: null               

# Minimum and maximum plan length (integer > 0). Filters your problem set to contain the instances that have a whitelist plan of this specified range.
min_length: 1
max_length: 15

# Instance ordering: In what order should the problems be solved? You may want to set to increasing for debug, so that you start from smaller problems and fail faster.
# Choices:
  #   increasing = shorter action traces first
  #   random     = random order
order: increasing

# Domain restriction. Use null or specify a domain name (e.g., "mprime").
domain_class: null               
```

## Usage

### Batch Solver

Run batch experiments over a set of benchmark instances:

```bash
python3 -u batch_solver.py config.yaml
```

- Automatically detects available CPUs and distributes work across them.  
- Memory usage is capped at 8GB per instance in `instance_solver.py`; ensure you have enough RAM when scaling up CPU usage.  
- Produces per-instance YAML logs in `log_folder`.  
- For HPC: we used `container/source/ecai-os-python.def` to build a **Singularity image** as the execution environment. 
  - We include this Singularity image to be transparent about how we run our experiments. However, we recommend using the Docker file we mentioned above instead, we it should work out of the box.

### Simplified Batch Solver

If you want a single-CPU version with simpler usage, run:

```bash
python3 main.py config.yaml
```

This is useful for debugging or running small batches without HPC infrastructure.

### Single Instance Solver

Solve a single instance identified by `<instance_id>`:

```bash
python -u instance_solver.py config.yaml <instance_id>
# Example:
python3 instance_solver.py config.yaml zenotravel__pp01-err-rate-0-3
```

### Log Processing

Convert generated YAML logs into structured summaries. Note that the Paths of the inputs and outputs are hard-coded in each script. Check (and change) them before using.

```bash
cd exp_log_processing

# Per each domain: reads each YAML log file and generates a merged, single CSV file named "merged.csv".
python3 -u log_merger.py


# For all domains, "merged.csv" files are combined into two outputs: "main_table.csv", listing results of several algorithms per domain (as in the supplementary material), and "summary_table.csv", a compact version covering the full benchmark set (as in the main paper).
python3 -u log_to_table.py

# Generate a LaTeX table: converts "main_table.csv" and "summary_table.csv" to LaTeX tables. Note that I don't recommend using this script, since later we realized "pandas.DataFrame.to_latex" is much simpler and cleaner for creating LaTeX tables.
python3 -u log_table_to_latex.py
```

### Benchmark Folder Structure Assumptions

If you want to use the default data loader in `exptools/load_data.py` directly, you need to organize your repair problems like in `./input/benchmarks-G1`.

**Folder Structure Assumptions:**

- The **first-level folders** are domain names. These names will be used for reporting (i.e., rows in the output tables).
- Example: a `Blocks` domain is located in `./input/ExampleBenchmarks/Blocks`.

Inside the domain folder:

- Flawed domains must follow the format:  
  `domain-<problem_name>.pddl`  
  Example: `domain-prob1.pddl`
- Each flawed domain must have a **matching problem file**:  
  `<problem_name>.pddl`  
  Example: `prob1.pddl`
- A corresponding folder `<domain>_plans` must exist, containing partially whitelist plans:  
  Example: `./input/ExampleBenchmarks/Blocks_plans/prob1.plan`

Note that the benchmark set originates from the baseline work (grounded). By setting `lift_prob`, literals are randomly lifted to variables, producing a partially lifted benchmark set (as described in the paper).

## Directory Structure

```bash
.
├── container/               # Container definitions (e.g., Singularity, Docker support files)
├── exp_log_processing/      # Utilities for processing experimental logs
├── exp_logs_anu/            # Experiment logs, as reported in the paper.
├── exp_logs_csv/            # "exp_logs_anu" processed to CSV
├── exptools/                # Experiment utilities for instance and data management
├── fd/                      # Fast Downward: used in the baseline repairer and blind search.
├── fd2/                     # Fast Downward: used for the heuristic
├── heuristic_tools/         # Heuristic implementations and auxiliary files
├── hitter/                  # Hitting set solver
├── input/                   # Input benchmark datasets
├── model/                   # PDDL domain and task, and repair Python models
├── pwl/                     # Powerlifted build/resources: used in the heuristic
├── relaxation_generator/    # Heuristic relaxation generators: used in the heuristic
├── repairer/                # Baseline repair implementations
├── search_partial_grounding/ # Partial grounding search framework (main contribution)
├── utils/                   # Supporting utility modules (used mainly in the baseline repairer)
├── batch_solver.py          # Refer to README.md
├── config.yaml              # Refer to README.md
├── custom_logger.py         # A custom logger used for creating YAML logs which is the main output of the experimental results as well as logging errors and tracking execution.
├── instance_solver.py       # Refer to README.md
├── main.py                  # Refer to README.md
├── README.md                # Refer to README.md :-)
├── requirements.txt         # Refer to README.md
```

## Limitations

- You can't enforce identical grounding by using identical variable names in the input action sequence. The search procedure will try grounding each variable independently by using objects of the same type.
- In the experimental logs included in exp_logs_anu, `bfs` is internally equivalent to **Uniform Cost Search (UCS)**. The log_processing scripts rename `bfs` to `ucs` for creating the LaTeX table.

## Reference

If you use this code in your research, please cite our paper:

```bibtex
@InProceedings{Bavandpour2025LiftedTestPlans,
  author    = {Nader Karimi Bavandpour and Pascal Lauer and Songtuan Lin and Pascal Bercher},
  booktitle = {Proceedings of the 28th European Conference on Artificial Intelligence (ECAI 2025)},
  title     = {Repairing Planning Domains Based on Lifted Test Plans},
  year      = {2025},
  publisher = {IOS Press}
}
```

## License

This repository is distributed under the [GNU General Public License v3.0](LICENSE).

It incorporates or builds upon code from:

- [Diagnoser](https://github.com/Songtuan-Lin/diagnoser) – *no explicit license*
- [Fast Downward](https://github.com/aibasel/downward) – GPL v3
- [Powerlifted](https://github.com/abcorrea/powerlifted) – GPL v3
- [lpopt](https://dbai.tuwien.ac.at/proj/lpopt/) – GPL v3
- [clingo](https://github.com/potassco/clingo) – MIT

As required by the GPL, this repository as a whole is licensed under GPL v3.  
MIT-licensed portions retain their original license notices.
