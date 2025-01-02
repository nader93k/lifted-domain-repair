import yaml
import csv
import os
import glob

# Predefined columns based on the specification
COLUMNS = [
    'log_file',
    'instance_id',
    'domain_class',
    'search_algorithm',
    'plan_length',
    'repair_length',
    'repair',
    'goal_reached',
    'num_nodes_generated',
    'sum_h_cost',
    'sum_f_cost',
    'sum_h_cost_time',
    'sum_grounding_time',
    'search_time',
    'goal_g_cost',   # New column
    'goal_repair_set',  # New column
    'error_message'
]

def process_yaml_file(file_path):
    """Process a single YAML file and extract relevant data in a single pass."""
    # Initialize all fields as None
    data = {column: None for column in COLUMNS}
    data['goal_reached'] = False  # Default value for goal_reached is False
    
    try:
        with open(file_path, 'r') as f:
            for doc in yaml.safe_load_all(f):
                # Check for error level documents
                level = str(doc.get('level', '')).lower()
                if level == 'error':
                    data['error_message'] = doc.get('data')
                    continue
                
                issuer = doc.get('issuer')
                event_type = doc.get('event_type')
                doc_data = doc.get('data', {})
                
                if issuer == 'instance_solver':
                    if event_type == 'metadata':
                        # Extract metadata
                        data.update({
                            'log_file': doc_data.get('log_file'),
                            'instance_id': doc_data.get('instance_id'),
                            'search_algorithm': doc_data.get('search_algorithm'),
                            'plan_length': doc_data.get('plan_length'),
                            'domain_class': doc_data.get('domain_class')
                        })
                    elif event_type == 'ground_repair':
                        # Extract repair data
                        data.update({
                            'repair_length': doc_data.get('repair_length'),
                            'repair': doc_data.get('repair')
                        })
                    elif event_type == 'timer_seconds':
                        # Extract search time
                        data['search_time'] = doc_data
                
                elif issuer == 'searcher' and event_type == 'final':
                    # Extract searcher final data
                    is_goal = doc_data.get('is_goal', False)
                    data['goal_reached'] = is_goal
                    
                    if is_goal:
                        data.update({
                            'num_nodes_generated': doc_data.get('num_nodes_generated'),
                            'sum_h_cost': doc_data.get('sum_h_cost'),
                            'sum_f_cost': doc_data.get('sum_f_cost'),
                            'sum_h_cost_time': doc_data.get('sum_h_cost_time'),
                            'sum_grounding_time': doc_data.get('sum_grounding_time')
                        })
                        
                        # Extract current_node data if available
                        current_node = doc_data.get('current_node', {})
                        if current_node:
                            data.update({
                                'goal_g_cost': current_node.get('g_cost'),
                                'goal_repair_set': current_node.get('repair_set')
                            })
        
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
    directory_path = "/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/00 bfs relax-prec-delete lp1"
    output_csv = "exp_logs.csv"
    process_yaml_files(directory_path, output_csv)