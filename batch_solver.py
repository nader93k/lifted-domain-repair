from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import sys
import subprocess
import json
import yaml
import datetime
from multiprocessing import Process, Queue, cpu_count
import psutil


def get_allowed_cpus():
    """Get the list of allowed CPU cores for the current process"""
    try:
        process = psutil.Process()
        return list(process.cpu_affinity())
    except Exception as e:
        print(f"Error getting CPU affinity: {e}")
        return list(range(cpu_count()))

def worker(worker_id, task_queue, result_queue, params):
    """Worker process function that processes instances from the queue"""
    print(f"Worker {worker_id} started", flush=True)
    
    while True:
        try:
            # Get next task from queue
            instance = task_queue.get()
            if instance is None:  # Poison pill
                break
                
            start_time = datetime.datetime.now()
            print(f"[{start_time}] Worker {worker_id} starting instance {instance.identifier}", flush=True)
            
            log_file = os.path.join(params['log_folder'], f"{instance.identifier}.yaml")
            
            if os.path.isfile(log_file):
                os.remove(log_file)
            
            # Prepare command
            cmd = [
                sys.executable,
                "instance_solver.py",
                params['search_algorithm'],
                str(params['benchmark_path']),
                log_file,
                str(params['log_interval']),
                instance.identifier,
                str(params['lift_prob'])
            ]
            
            if params['heuristic_relaxation']:
                cmd.append(params['heuristic_relaxation'])
            
            try:
                print(f"[{datetime.datetime.now()}] Worker {worker_id} executing subprocess for {instance.identifier}", flush=True)
                result = subprocess.run(cmd, check=True, timeout=params['timeout_seconds'])
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"[{end_time}] Worker {worker_id} completed {instance.identifier} in {duration:.2f} seconds", flush=True)
                
                result_queue.put((True, instance.identifier))
                
            except subprocess.TimeoutExpired:
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"[{end_time}] Worker {worker_id} TIMEOUT on {instance.identifier} after {duration:.2f} seconds", flush=True)
                result_queue.put((False, instance.identifier))
                
            except Exception as e:
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"[{end_time}] Worker {worker_id} ERROR on {instance.identifier} after {duration:.2f} seconds: {e}", flush=True)
                result_queue.put((False, instance.identifier))
                
        except Exception as e:
            print(f"Error in worker {worker_id}: {e}", flush=True)
            continue

def prepare_data(benchmark_path, domain_class, instance_ids, min_length, max_length, 
               order, log_folder, search_algorithm, log_interval, timeout_seconds, 
               heuristic_relaxation, lift_prob):
    """Prepare data and parameters for processing"""
    
    # Create log folder
    os.makedirs(log_folder, exist_ok=True)
    
    # Get instances
    instance_list = list_instances(benchmark_path, domain_class, instance_ids)
    instances = list(smart_instance_generator(
        instance_list,
        min_length=min_length,
        max_length=max_length,
        order=order
    ))
    
    print(f"Total instances to process: {len(instances)}", flush=True)
    
    # Prepare parameters
    params = {
        'search_algorithm': search_algorithm,
        'benchmark_path': benchmark_path,
        'log_folder': log_folder,
        'log_interval': log_interval,
        'timeout_seconds': timeout_seconds,
        'heuristic_relaxation': heuristic_relaxation,
        'lift_prob': lift_prob
    }
    
    # Setup checkpoint file
    checkpoint_file = os.path.join(log_folder, "00_checkpoint.json")
    
    # Load checkpoint if exists
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            completed_instances = set(json.load(f))
            print(f"Loaded {len(completed_instances)} completed instances from checkpoint", flush=True)
    else:
        completed_instances = set()
    
    # Filter remaining instances
    remaining_instances = [inst for inst in instances if inst.identifier not in completed_instances]
    print(f"Remaining instances to process: {len(remaining_instances)}", flush=True)
    
    return remaining_instances, params, checkpoint_file

def run_process(search_algorithm, benchmark_path, log_folder, log_interval,
                timeout_seconds, order, min_length, max_length, heuristic_relaxation,
                domain_class=None, instance_ids=[], lift_prob=0.0, run_mode='parallel'):
    
    start_time = datetime.datetime.now()
    print(f"[{start_time}] Batch solver started", flush=True)
    
    # Get allowed CPUs
    allowed_cpus = get_allowed_cpus()
    num_cpus = len(allowed_cpus)
    
    if num_cpus == 0:
        print("Could not determine allowed CPUs. Using system CPU count.")
        num_cpus = cpu_count()
        allowed_cpus = list(range(num_cpus))
    
    print(f"Running with {num_cpus} worker processes on CPUs: {allowed_cpus}", flush=True)
    
    # Prepare data and parameters
    remaining_instances, params, checkpoint_file = prepare_data(
        benchmark_path, domain_class, instance_ids, min_length, max_length,
        order, log_folder, search_algorithm, log_interval, timeout_seconds,
        heuristic_relaxation, lift_prob
    )
    
    # Initialize queues
    task_queue = Queue()
    result_queue = Queue()
    
    # Add tasks to queue
    for instance in remaining_instances:
        task_queue.put(instance)
    
    # Add poison pills
    for _ in range(num_cpus):
        task_queue.put(None)
    
    # Start worker processes
    processes = []
    for cpu_id in allowed_cpus:
        p = Process(target=worker, args=(cpu_id, task_queue, result_queue, params))
        processes.append(p)
        p.start()
    
    # Collect results and update checkpoint file
    successful = 0
    total_processed = 0
    
    while total_processed < len(remaining_instances):
        success, instance_id = result_queue.get()
        total_processed += 1
        
        if success:
            successful += 1
            # Update checkpoint file
            try:
                with open(checkpoint_file, 'r') as f:
                    completed = set(json.load(f))
            except (FileNotFoundError, json.JSONDecodeError):
                completed = set()
            
            completed.add(instance_id)
            
            with open(checkpoint_file, 'w') as f:
                json.dump(list(completed), f)
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time}] Batch solver completed. Total duration: {duration:.2f} seconds", flush=True)
    print(f"Successfully completed instances: {successful}/{len(remaining_instances)}", flush=True)

# Load instance IDs function remains the same
def load_instance_ids(file_path):
    """Load instance IDs from a JSON file"""
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.", flush=True)
    return instance_ids

# Main function remains unchanged as requested
if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Starting batch solver", flush=True)
    
    config_file = '00 config.yaml'
    with open(config_file, 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    benchmark_path = Path(config['benchmark_path'])
    search_algorithm = config['search_algorithm']
    log_folder = Path(config['log_folder'])
    log_interval = config['log_interval']
    timeout_seconds = config['timeout_seconds']
    order = config['order']
    min_length = config['min_length']
    max_length = config['max_length']
    domain_class = config['domain_class'] 
    heuristic_relaxation = config['heuristic_relaxation']
    lift_prob = config['lift_prob']
    run_mode = config.get('run_mode')

    # run on fixed instance_ids
    instance_ids = config['instance_ids']
    if instance_ids == 'load_instance_ids':
        instance_ids = load_instance_ids('instance_ids_nonzero_h.json')
    elif instance_ids == 'instance_ids_small_exp_set':
        instance_ids = load_instance_ids('instance_ids_small_exp_set.json')

    print(f"Loaded configuration from: {config_file}", flush=True)
    print("Configuration:", flush=True)
    for key, value in config.items():
        print(f"  {key}: {value}", flush=True)
    
    run_process(
        search_algorithm=search_algorithm,
        benchmark_path=benchmark_path,
        log_folder=log_folder,
        log_interval=log_interval,
        timeout_seconds=timeout_seconds,
        order=order,
        min_length=min_length,
        max_length=max_length,
        domain_class=domain_class,
        instance_ids=instance_ids,
        heuristic_relaxation=heuristic_relaxation,
        lift_prob=lift_prob,
        run_mode=run_mode
    )
