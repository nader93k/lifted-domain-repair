import os
from matplotlib import contour
from matplotlib.ticker import NullFormatter
import yaml
import csv
from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field
from statistics import mean, median



ALL_COLUMNS = [
    'file_name', 'problem_name', 'plan_length', 'num_ground_repair', 'str_ground_repair',
    'run_time', 'error', 'results_exists',
    'result_depth', 'result_repair_set', 'result_g_cost', 'result_h_cost', 'result_f_cost',
    'num_neighbours'
]

# Add columns for all aggregates
for metric in ['iteration', 'depth', 'branching_factor', 'fringe_size', 'h_cost', 'g_cost', 'f_cost', 'num_neighbours']:
    for agg_type in ['min', 'max', 'median', 'avg', 'sum']:
        ALL_COLUMNS.append(f'{metric}_{agg_type}')


@dataclass
class SearcherIterationData:
    iterations: List[int] = field(default_factory=list)
    depths: List[float] = field(default_factory=list)
    branching_factors: List[float] = field(default_factory=list)
    fringe_sizes: List[float] = field(default_factory=list)
    h_costs: List[float] = field(default_factory=list)
    g_costs: List[float] = field(default_factory=list)
    f_costs: List[float] = field(default_factory=list)
    num_neighbours: List[int] = field(default_factory=list)

    def add_iteration(self, iteration: int, depth: float, branching_factor: float, 
                      fringe_size: float, h_cost: float, g_cost: float, f_cost: float,
                      num_neighbours: int):
        self.iterations.append(iteration)
        self.depths.append(depth)
        self.branching_factors.append(branching_factor)
        self.fringe_sizes.append(fringe_size)
        self.h_costs.append(h_cost)
        self.g_costs.append(g_cost)
        self.f_costs.append(f_cost)
        self.num_neighbours.append(num_neighbours)

    def calculate_aggregates(self):
        return {
            "iteration": self._aggregate(self.iterations),
            "depth": self._aggregate(self.depths),
            "branching_factor": self._aggregate(self.branching_factors),
            "fringe_size": self._aggregate(self.fringe_sizes),
            "h_cost": self._aggregate(self.h_costs),
            "g_cost": self._aggregate(self.g_costs),
            "f_cost": self._aggregate(self.f_costs),
            "num_neighbours": self._aggregate(self.num_neighbours)
        }

    @staticmethod
    def _aggregate(values: List[float]):
        if not values:
            return {"min": None, "max": None, "median": None, "avg": None, "sum": None}
        return {
            "min": min(values),
            "max": max(values),
            "median": median(values),
            "avg": mean(values),
            "sum": sum(values)
        }



@dataclass
class LogData:
    file_name: str
    problem_name: Optional[str] = None
    plan_length: Optional[int] = None
    num_ground_repair: Optional[int] = None
    str_ground_repair: Optional[str] = None
    run_time: Optional[float] = None
    results: Optional[Dict] = None
    error: Optional[str] = None
    searcher_data: SearcherIterationData = field(default_factory=SearcherIterationData)
    num_neighbours: Optional[int] = None



def extract_data(yaml_docs: List[dict], file_name: str) -> LogData:
    log_data = LogData(file_name=file_name)

    results = []
    errors = []
    for idx, doc in enumerate(yaml_docs):
        
        issuer = doc.get('issuer')
        event_type = doc.get('event_type')
        data = doc.get('data', {})

        # we don't need this doc type in the newer version of the code anymore. Just skip.
        if event_type == 'results':
            continue
        
        ## read the errors
        if 'error' in doc:
            err_str = str(doc['error'].get('data'))
            errors.append(err_str)
            continue
        
        ## read the result nodes
        if type(data) is dict and "is_goal" in data.keys():
            result = {
                'depth': data['current_node']['depth'],
                'repair_set': data['current_node']['repair_set'],
                'g_cost': data['current_node']['g_cost'],
                'h_cost': data['current_node']['h_cost'],
                'f_cost': data['current_node']['f_cost']
            }
            results.append(result)
        
        if issuer == 'instance_solver':
            ## read Meta-data
            if event_type == 'metadata':
                log_data.problem_name = data.get('instance_id')
                log_data.plan_length = data.get('plan_length')
                
            elif event_type == 'ground_repair':
                log_data.num_ground_repair = data.get('repair_length')
                log_data.str_ground_repair = data.get('repair')
                
            ## read time spent
            elif event_type == 'time_spent':
                log_data.run_time = data

        ## read general search node stats
        if issuer == 'Searcher' and event_type == 'general':
            current_node = data.get('current_node', {})
            num_neighbours = current_node.get('num_neighbours')
            log_data.searcher_data.add_iteration(
                iteration=data.get('iteration'),
                depth=current_node.get('depth'),
                branching_factor=current_node.get('num_neighbours'),
                fringe_size=data.get('fring_size'),
                h_cost=current_node.get('h_cost'),
                g_cost=current_node.get('g_cost'),
                f_cost=current_node.get('f_cost'),
                num_neighbours=num_neighbours
            )
            log_data.num_neighbours = num_neighbours
    
    log_data.error = "; ".join(errors)
    if results:
        x = 1
    log_data.results = results.pop() if results else None

    return log_data


def safe_load_yaml(yaml_content):
    class IgnoreTagLoader(yaml.SafeLoader):
        def ignore_unknown(self, node):
            return None

    IgnoreTagLoader.add_constructor(None, IgnoreTagLoader.ignore_unknown)
    return yaml.load(yaml_content, Loader=IgnoreTagLoader)


def get_processed_files(csv_file: str) -> Set[str]:
    processed_files = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                processed_files.add(row['file_name'])
    return processed_files


def analyze_log_file(file_path: str) -> LogData:
    # try:
    with open(file_path, 'r') as file:
        yaml_docs = []
        for doc in yaml.safe_load_all(file):
            yaml_docs.append(safe_load_yaml(yaml.dump(doc)))
    return extract_data(yaml_docs, os.path.basename(file_path))
    # except Exception as e:
    #     return LogData(file_name=os.path.basename(file_path), error=str(e))


def get_unprocessed_files(folder_path: str, csv_file: str) -> List[str]:
    all_yaml_files = [f for f in os.listdir(folder_path) if f.endswith('.yaml')]
    processed_files = get_processed_files(csv_file)
    return [f for f in all_yaml_files if f not in processed_files]


def analyze_logs(folder_path: str) -> List[LogData]:
    all_log_data = []
    csv_file = 'results.csv'
    
    unprocessed_files = get_unprocessed_files(folder_path, csv_file)
    total_files = len(unprocessed_files)
    
    print(f"Found {total_files} unprocessed files.")
    
    for i, filename in enumerate(unprocessed_files, 1):
        file_path = os.path.join(folder_path, filename)
        log_data = analyze_log_file(file_path)
        all_log_data.append(log_data)
        append_to_csv(log_data)
        print(f"Processed file {i} out of {total_files}: {filename}")
    
    return all_log_data

def get_empty_row():
    return {col: None for col in ALL_COLUMNS}

def append_to_csv(log_data: LogData):
    csv_file = 'results.csv'
    file_exists = os.path.isfile(csv_file)
    
    aggregates = log_data.searcher_data.calculate_aggregates()
    
    row = get_empty_row()
    row.update({
        'file_name': log_data.file_name,
        'problem_name': log_data.problem_name,
        'plan_length': log_data.plan_length,
        'num_ground_repair': log_data.num_ground_repair,
        'str_ground_repair': log_data.str_ground_repair,
        'run_time': log_data.run_time,
        'error': log_data.error,
        'results_exists': log_data.results is not None,
        'num_neighbours': log_data.num_neighbours  # Added num_neighbours
    })
    
    if log_data.results:
        for key, value in log_data.results.items():
            row[f'result_{key}'] = value
    
    for metric, values in aggregates.items():
        for agg_type, value in values.items():
            row[f'{metric}_{agg_type}'] = value

    with open(csv_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ALL_COLUMNS, quoting=csv.QUOTE_NONNUMERIC)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)

if __name__ == "__main__":
    folder_path = './exp_logs/13 BFS-lifted-prob06'

    # ## TODO: Remove these debug lines
    # if os.path.exists("results.csv"):
    #     os.remove("results.csv")
    # folder_path = './exp_logs_debug/'

    all_log_data = analyze_logs(folder_path)
    print(f"\nAnalysis complete. Processed {len(all_log_data)} new log files.")
