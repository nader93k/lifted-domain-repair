from instance_solver import solve_instance
from custom_logger import StructuredLogger
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import sys
import logging
import subprocess
import json
import yaml
import datetime
from concurrent.futures import ProcessPoolExecutor
import resource
from functools import partial
import psutil


def limit_resources(worker_id):
    """Set CPU affinity for each worker process"""
    try:
        # Parse SLURM CPU list (e.g., "4-18")
        cpu_range = os.environ.get('SLURM_CPU_BIND_LIST', '')
        print('debug' + cpu_range)
        if cpu_range and '-' in cpu_range:
            start, end = map(int, cpu_range.split('-'))
            num_cpus = end - start + 1
            # Map worker_id to the range [start, end]
            assigned_cpu = start + (worker_id % num_cpus)
            psutil.Process().cpu_affinity([assigned_cpu])
        
            # Set memory limit if specified
            if 'SLURM_MEM_PER_NODE' in os.environ:
                total_mem = int(os.environ['SLURM_MEM_PER_NODE']) * 1024 * 1024 * 1024
                mem_limit = total_mem // num_cpus
                resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
                
    except Exception as e:
        print(f"Warning: Failed to set resource limits for worker {worker_id}: {e}", flush=True)
            
    except Exception as e:
        print(f"Warning: Failed to set resource limits for worker {worker_id}: {e}", flush=True)


def solve_instance_wrapper(worker_id, instance, params):
    """Wrapper function to handle individual instance solving with timeout"""
    start_time = datetime.datetime.now()
    print(f"[{start_time}] Worker {worker_id} starting instance {instance.identifier}", flush=True)
    
    try:
        limit_resources(worker_id)
    except Exception as e:
        print(f"Warning: Could not set CPU affinity for worker {worker_id}: {e}", flush=True)
    
    log_file = os.path.join(
        params['log_folder'],
        f"{params['search_algorithm']}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.yaml"
    )
    
    if os.path.isfile(log_file):
        print(f"[{datetime.datetime.now()}] Worker {worker_id} skipping existing result for {instance.identifier}", flush=True)
        return None
        
    logger = StructuredLogger(log_file)
    interpreter_path = sys.executable
    cmd = [
        interpreter_path,
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
        
        logger.log(
            issuer="batch_solver",
            event_type="general",
            level=logging.INFO,
            message=f"Subprocess finished successfully. Duration: {duration:.2f} seconds"
        )
        print(f"[{end_time}] Worker {worker_id} completed {instance.identifier} in {duration:.2f} seconds", flush=True)
        return True
        
    except subprocess.TimeoutExpired:
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.log(
            issuer="batch_solver",
            event_type="error",
            level=logging.ERROR,
            message=f"Subprocess timed out after {params['timeout_seconds']} seconds."
        )
        print(f"[{end_time}] Worker {worker_id} TIMEOUT on {instance.identifier} after {duration:.2f} seconds", flush=True)
        
    except Exception as e:
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.log(
            issuer="batch_solver",
            event_type="error",
            level=logging.ERROR,
            message=f"Exception: instance id={instance.identifier}, err: {e}"
        )
        print(f"[{end_time}] Worker {worker_id} ERROR on {instance.identifier} after {duration:.2f} seconds: {e}", flush=True)
        
    return False


def process_instance(args):
    """Helper function to unpack arguments for solve_instance_wrapper"""
    worker_id, instance, params = args
    return solve_instance_wrapper(worker_id, instance, params)


def run_process(search_algorithm, benchmark_path, log_folder, log_interval,
                timeout_seconds, order, min_length, max_length, heuristic_relaxation,
                domain_class=None, instance_ids=[], lift_prob=0.0, run_mode='parallel'):
    
    start_time = datetime.datetime.now()
    print(f"[{start_time}] Batch solver started", flush=True)
    
    # Get number of workers from SLURM CPU binding or use all available CPUs
    cpu_list = os.environ.get('SLURM_CPU_BIND_LIST', '')
    if cpu_list:
        num_workers = sum(len(range(int(r.split('-')[0]), int(r.split('-')[1]) + 1)) 
                         if '-' in r else 1 
                         for r in cpu_list.split(','))
    else:
        num_workers = psutil.cpu_count()
    
    print(f"Running with {num_workers} worker processes", flush=True)
    
    # Create log folder if it doesn't exist
    os.makedirs(log_folder, exist_ok=True)
    
    instance_list = list_instances(benchmark_path, domain_class, instance_ids)
    instances = list(smart_instance_generator(
        instance_list,
        min_length=min_length,
        max_length=max_length,
        order=order
    ))
    
    print(f"Total instances to process: {len(instances)}", flush=True)
    
    params = {
        'search_algorithm': search_algorithm,
        'benchmark_path': benchmark_path,
        'log_folder': log_folder,
        'log_interval': log_interval,
        'timeout_seconds': timeout_seconds,
        'heuristic_relaxation': heuristic_relaxation,
        'lift_prob': lift_prob
    }
    
    checkpoint_file = os.path.join(log_folder, "checkpoint.json")
    completed_instances = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            completed_instances = set(json.load(f))
            print(f"Loaded {len(completed_instances)} completed instances from checkpoint", flush=True)
    
    # Filter out completed instances
    instances = [inst for inst in instances if inst.identifier not in completed_instances]
    print(f"Remaining instances to process: {len(instances)}", flush=True)
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Create a list of (worker_id, instance, params) tuples
        worker_assignments = [(i % num_workers, instance, params) 
                            for i, instance in enumerate(instances)]
        
        # Map using the helper function
        for i, result in enumerate(executor.map(process_instance, worker_assignments)):
            if result:  # If instance was processed successfully
                instance_id = instances[i].identifier
                completed_instances.add(instance_id)
                # Update checkpoint after each successful completion
                with open(checkpoint_file, 'w') as f:
                    json.dump(list(completed_instances), f)
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time}] Batch solver completed. Total duration: {duration:.2f} seconds", flush=True)
    print(f"Total instances completed: {len(completed_instances)}", flush=True)


def load_instance_ids(file_path):
    """Load instance IDs from a JSON file"""
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.", flush=True)
    return instance_ids


if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Starting batch solver", flush=True)
    
    config_file = 'config.yaml'
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
