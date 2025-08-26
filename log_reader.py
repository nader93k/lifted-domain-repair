import yaml
import csv
import os
import glob

# Reordered columns list with new error group field and grounding method
COLUMNS = [
    'log file',
    'instance id',
    'domain class',
    'search algorithm',
    'plan length',
    'vanilla repair length',
    'vanilla repair',
    'goal reached',
    'iteration',
    'num nodes generated',
    'h_max',
    'sum h cost',
    'sum f cost',
    'sum h cost time',
    'sum grounding time',
    'search time',
    'search g cost',
    'search repair set',
    'repair length comparison',
    'repair string comparison',
    'error message',
    'error group',
    'lift_prob',
    'grounding method'
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

def compare_repair_strings(search_repair, vanilla_repair):
    """Compare search repair set with vanilla repair."""
    if search_repair in (None, '') or vanilla_repair in (None, ''):
        return None
    return str(search_repair).strip() == str(vanilla_repair).strip()

def categorize_error(error_message):
    """Categorize error messages into groups."""
    if error_message is None:
        return None
        
    error_message = str(error_message).lower()
    
    if 'memoryerror' in error_message:
        return 'memory'
    elif 'timed out' in error_message:
        return 'time'
    return error_message

def process_yaml_file(file_path, lift_prob=None, grounding_method=None):
    """Process a single YAML file and extract relevant data in a single pass."""
    # Initialize all fields as None
    data = {column: None for column in COLUMNS}
    data['goal reached'] = False  # Default value for goal_reached is False
    data['lift_prob'] = lift_prob  # Set lift_prob from parameter
    data['grounding method'] = grounding_method  # Set grounding_method from parameter
    
    try:
        with open(file_path, 'r') as f:
            for doc in yaml.safe_load_all(f):
                # Check for error level documents
                level = str(doc.get('level', '')).lower()
                if level == 'error':
                    error_msg = doc.get('data')
                    data['error message'] = error_msg
                    data['error group'] = categorize_error(error_msg)
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
                    
                    # Add h_max and iteration
                    data['h_max'] = doc_data.get('h_max')
                    data['iteration'] = doc_data.get('iteration')
                    
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
        
        data['repair length comparison'] = compare_repair_lengths(
            data['search g cost'], 
            data['vanilla repair length']
        )
        data['repair string comparison'] = compare_repair_strings(
            data['search repair set'],
            data['vanilla repair']
        )
        
        return data
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return data  # Return data with default values if there's an error

def process_yaml_files(directory_path, output_csv, lift_prob=None, excluded_domains=None, grounding_method=None):
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
            data = process_yaml_file(yaml_file, lift_prob, grounding_method)  # Pass grounding_method to process_yaml_file
            
            # Skip if domain class is in exclusion list
            if excluded_domains and data['domain class'] in excluded_domains:
                continue
                
            writer.writerow(data)
