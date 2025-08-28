# Lifted-White Plan Domain Repair

This repository implements the **Lifted White Plan Domain Repair framework**, providing tools to repair planning domains using lifted and partial grounding techniques. It supports multiple search algorithms, heuristic relaxations, structured logging, and batch execution of repair experiments.

If you use this code in your research, please **refer to our ECAI 2025 paper** and cite it (see [Reference](#reference)).

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Batch Solver](#batch-solver)
  - [Simplified Batch Solver](#simplified-batch-solver)
  - [Single Instance Solver](#single-instance-solver)
  - [Log Processing](#log-processing)
- [Docker Usage](#docker-usage)
- [Directory Structure](#directory-structure)
- [Documentation](#documentation)
- [Tests](#tests)
- [Limitations](#limitations)
- [Reference](#reference)
- [License](#license)

---

## Features
- Batch processing of planning domain repair tasks with `batch_solver.py`.
- Single-instance execution with `instance_solver.py`.
- Supports lifted planning, ground repair, and partial grounding.
- Configurable search algorithms: A*, Greedy, DFS, Uniform-Cost-Search (UCS) Branch and Bound.
- Heuristic relaxations: zeroary, null, unary.
- Structured YAML logging and log-to-table utilities.

---

## Running by Docker
We provide a pre-built Docker image that should work out of the box:

```bash
docker pull nader93k/ecai2025-repairing-domains:latest
```

This image contains all required dependencies and is the recommended way to get started quickly.


If you need to build the project, please see see the explanation below.

## Setting the Environment & Building

This project requires several external tools and libraries in addition to the Python codebase.  
Below is a concise installation guide.

### Python Packages

- Tested with **Python 3.8**.  
- Install dependencies from `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

- For **blind search algorithms**, this is sufficient.  
- For heuristic search, additional tools must be compiled.


### lpopt (Tree Decomposition Optimizer)

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

- Must be compiled manually.  
- Official instructions: [Fast Downward](https://www.fast-downward.org/latest/)  
- Expected source directory: `fd2/`


### Powerlifted

- Must be compiled manually.  
- Repository: [Powerlifted](https://github.com/abcorrea/powerlifted)  
- Expected source directory: `pwl/`


### Clingo / Gringo

- Used for grounding.  
- Available through most Linux package managers.  
- Sources available at: [Clingo GitHub](https://github.com/potassco/clingo)

---

## Configuration
Experiment settings are defined in `config.yaml`. Below is a guide to the most important parameters:

```yaml
search_algorithm: g_astar        # Choices: ucs, dfs, astar, g_astar, gbfs
heuristic_relaxation: unary      # Choices: zeroary, null, unary, or relax-all variants.
lift_prob: 1.0                   # Probability for lifting actions (1.0 =  lift).
instance_ids: null               # Provide explicit IDs, or null to run all.
min_length: 1                    # Minimum plan length.
max_length: 15                   # Maximum plan length.
timeout_seconds: 900             # Timeout per instance (seconds).
order: increasing                # Instance ordering (increasing or random).
benchmark_path: /path/to/benchmarks   # Path to benchmark PDDL problems.
log_folder: /path/to/output/logs      # Output folder for per-instance YAML logs.
log_interval: 1000000            # Logging frequency (in expansions).
domain_class: null               # Override with a custom domain class (optional).
```

> Each parameter is explained directly in `config.yaml`.  
> For example, `search_algorithm` and `heuristic_relaxation` must be compatible; BFS/DFS ignore heuristics, while A* and Greedy require them.

---

## Usage

### Batch Solver
Run batch experiments over a set of benchmark instances:

```bash
python -u batch_solver.py config.yaml
```

- Automatically detects available CPUs and distributes work across them.  
- Memory usage is capped at 8GB per instance in `instance_solver.py`; ensure you have enough RAM when scaling up CPU usage.  
- Produces per-instance YAML logs in `log_folder`.  
- For HPC: we used `container/source/ecai-os-python.def` to build a **Singularity image** as the execution environment.

---

### Simplified Batch Solver
If you want a single-CPU version with simpler usage, run:

```bash
python3 main.py config.yaml
```

This is useful for debugging or running small batches without HPC infrastructure.

---

### Single Instance Solver
Solve a single instance identified by `<instance_id>`:

```bash
python -u instance_solver.py config.yaml <instance_id>
```

TODO: How form instance_id

---

### Log Processing
Convert generated YAML logs into structured summaries:

```bash
# Generate a combined CSV summary:
python -u log_reader.py              > summary.csv

# Create a plain-text table:
python -u log_to_table.py <logs_dir> > table.txt

# Generate a LaTeX table:
python -u log_table_to_latex.py <logs_dir> > table.tex
```

Other utilities:
- `log_merger.py` – merge multiple YAML logs
- `log_table_to_latex_maxh.py` – LaTeX tables optimized for publications

---

## Directory Structure

```
.
├── container/               # Container definitions (e.g., Singularity, Docker support files)
├── exp_log_processing/      # Utilities for processing experimental logs
├── exp_logs_anu/            # Experiment logs (ANU runs)
├── exp_logs_csv/            # Experiment logs exported to CSV
├── exp_logs_debug/          # Debugging logs
├── exptools/                # Experiment utilities for instance and data management
├── fd/                      # Fast Downward build or resources
├── fd2/                     # Alternate Fast Downward build
├── heuristic_tools/         # Heuristic implementations and auxiliary files
├── hitter/                  # Hitting set or related utilities
├── input/                   # Input benchmark datasets
├── model/                   # PDDL domain and task models
├── pwl/                     # Powerlifted build/resources
├── relaxation_generator/    # Heuristic relaxation generators
├── repairer/                # Ground repair implementations
├── search_partial_grounding/ # Partial grounding search framework
├── utils/                   # Supporting utility modules
├── batch_solver.py
├── commands.sh
├── config.yaml
├── custom_logger.py
├── Dockerfile
├── instance_solver.py
├── main.py
├── README.md
├── requirements.txt
```

---

## Limitations
- You can't enforece identical grounding by using identical variable names in the input action sequence. The search procedure will try grounding each variable independently by using objects of the same type.
- In the experimental logs included in exp_logs_anu, `bfs` is internally equivalent to **Uniform Cost Search (UCS)**. The log_processing scripts rename `bfs` to `ucs` for creating the latex table.
- Batch solver assumes HPC usage; ensure sufficient memory scaling across CPUs.    
---

## Reference

This repository is the official implementation of our paper:

> Nader Karimi Bavandpour, Pascal Lauer, Songtuan Lin, and Pascal Bercher.  
> *Repairing Planning Domains Based on Lifted Test Plans*.  
> In Proceedings of the 28th European Conference on Artificial Intelligence (ECAI 2025). IOS Press, 2025.

If you use this code in your research, please cite our paper:

```
@InProceedings{Bavandpour2025LiftedTestPlans,
  author    = {Nader Karimi Bavandpour and Pascal Lauer and Songtuan Lin and Pascal Bercher},
  booktitle = {Proceedings of the 28th European Conference on Artificial Intelligence (ECAI 2025)},
  title     = {Repairing Planning Domains Based on Lifted Test Plans},
  year      = {2025},
  publisher = {IOS Press},
  keywords  = {conference,DECRA},
  abstract  = {Knowledge engineering for AI planning remains a significant challenge, particularly in the creation and maintenance of accurate domain models. A recent approach to correcting flawed models involves using test plans: non-solution plans that are intended to be solutions. However, these plans must be grounded, which restricts the modeler's ability to specify repairs at various levels of abstraction, especially when only partial information is available. In this paper, we propose a novel approach that extends domain repair capabilities to handle lifted test plans, where action parameters may remain unspecified. We introduce a new lifted repair problem set, a search algorithm, different designs of proper search spaces, and a novel lifted heuristic for solving the lifted repair problem. Our implementation and experimental results shows that our approach can solve a wide range of problems efficiently and reach solutions that are close to optimal.}  
}
```

---

## License
*To be added later.*



----
# TODO
-- explain how define lifted plans as input
-- explain the expected folder structure
-- add licensing