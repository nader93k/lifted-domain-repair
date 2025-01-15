import json
import csv

def remove_matching_instances(json_file, csv_file):
    # Read the JSON file
    with open(json_file, 'r') as f:
        instances = json.load(f)
    
    # Read the CSV file and get the instance IDs
    csv_instances = set()
    with open(csv_file, 'r') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            csv_instances.add(row['instance id'])
    
    # Remove matching instances from the JSON list
    filtered_instances = [inst for inst in instances if inst not in csv_instances]
    
    # Write back to the JSON file
    # print(csv_instances)
    with open(json_file, 'w') as f:
        json.dump(filtered_instances, f, indent=2)
    
    print(f"Removed {len(instances) - len(filtered_instances)} matching instances.")
    
if __name__ == "__main__":
    base = '/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/'
    folder = 'dfs relax-all lp1/'
    json_name = '00_checkpoint.json'
    csv_name = 'dfs_1.csv'
    json_file = base + folder + json_name
    csv_file = base + folder + csv_name
    
    try:
        remove_matching_instances(json_file, csv_file)
    except Exception as e:
        print(f"An error occurred: {str(e)}")