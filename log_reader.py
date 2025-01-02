import yaml
import csv
import os
import glob

# Predefined columns based on the specification
COLUMNS = [
    'log file',
    'instance id',
    'domain class',
    'search algorithm',
    'plan length',
    'vanilla repair length',
    'vanilla repair',
    'goal reached',
    'num nodes generated',
    'sum h cost',
    'sum f cost',
    'sum h cost time',
    'sum grounding time',
    'search time',
    'search g cost',   
    'search repair set',
    'repair length comparison',  # New column for comparison
    'error message'
]

def format_float(value):
    """Format float values to 2 decimal places."""
    return round(float(value), 2) if isinstance(value, (float, int)) else value

def compare_repair_lengths(search_cost, vanilla_length):
    """Compare search repair length with vanilla repair length."""
    if search_cost is None or vanilla_length is None:
        return None
    try:
        search_cost = float(search_cost)
        vanilla_length = float(vanilla_length)
        if search_cost < vanilla_length:
            return 'shorter'
        elif search_cost > vanilla_length:
            return 'longer'
        return 'equal'
    except (TypeError, ValueError):
        return None

def process_yaml_file(file_path):
    """Process a single YAML file and extract relevant data in a single pass."""
    # Initialize all fields as None
    data = {column: None for column in COLUMNS}
    data['goal reached'] = False  # Default value for goal_reached is False
    
    try:
        with open(file_path, 'r') as f:
            for doc in yaml.safe_load_all(f):
                # Check for error level documents
                level = str(doc.get('level', '')).lower()
                if level == 'error':
                    data['error message'] = doc.get('data')
                    continue
                
                issuer = doc.get('issuer')
                event_type = doc.get('event_type')
                doc_data = doc.get('data', {})
                
                if issuer == 'instance_solver':
                    if event_type == 'metadata':
                        # Extract metadata
                        data.update({
                            'log file': doc_data.get('log_file'),
                            'instance id': doc_data.get('instance_id'),
                            'search algorithm': doc_data.get('search_algorithm'),
                            'plan length': doc_data.get('plan_length'),
                            'domain class': doc_data.get('domain_class')
                        })
                    elif event_type == 'ground_repair':
                        # Extract repair data
                        data.update({
                            'vanilla repair length': doc_data.get('repair_length'),
                            'vanilla repair': doc_data.get('repair')
                        })
                    elif event_type == 'timer_seconds':
                        # Extract search time
                        data['search time'] = format_float(doc_data)
                
                elif issuer == 'searcher' and event_type == 'final':
                    # Extract searcher final data
                    is_goal = doc_data.get('is_goal', False)
                    data['goal reached'] = is_goal
                    
                    if is_goal:
                        data.update({
                            'num nodes generated': doc_data.get('num_nodes_generated'),
                            'sum h cost': doc_data.get('sum_h_cost'),
                            'sum f cost': doc_data.get('sum_f_cost'),
                            'sum h cost time': format_float(doc_data.get('sum_h_cost_time')),
                            'sum grounding time': format_float(doc_data.get('sum_grounding_time'))
                        })
                        
                        # Extract current_node data if available
                        current_node = doc_data.get('current_node', {})
                        if current_node:
                            data.update({
                                'search g cost': format_float(current_node.get('g_cost')),
                                'search repair set': current_node.get('repair_set')
                            })
        
        # Add repair length comparison
        data['repair length comparison'] = compare_repair_lengths(
            data['search g cost'], 
            data['vanilla repair length']
        )
        
        return data
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return data  # Return data with default values if there's an error

def process_yaml_files(directory_path, output_csv):
    """Process all YAML files in the directory and save results to CSV."""
    yaml_files = glob.glob(os.path.join(directory_path, '*.yaml'))
    
    if not yaml_files:
        print(f"No YAML files found in {directory_path}")
        return
    
    # Write to CSV using predefined columns
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        
        for yaml_file in yaml_files:
            data = process_yaml_file(yaml_file)
            writer.writerow(data)


if __name__ == "__main__":
    log_folder = "01 bfs relax-prec-delete lp1"
    directory_path = f"/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/{log_folder}"
    output_csv = f"00 logs_{log_folder}.csv"
    process_yaml_files(directory_path, output_csv)
