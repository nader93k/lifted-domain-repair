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
from mpi4py.futures import MPIPoolExecutor
from mpi4py import MPI
from functools import partial
import concurrent.futures

def solve_instance_wrapper(instance, params):
    """
    Wrapper function to handle individual instance solving with timeout
    """
    log_file = os.path.join(
        params['log_folder'],
        f"{params['search_algorithm']}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.yaml"
    )
    
    if os.path.isfile(log_file):
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
        result = subprocess.run(cmd, check=True, timeout=params['timeout_seconds'])
        logger.log(
            issuer="batch_solver",
            event_type="general",
            level=logging.INFO,
            message="Subprocess finished with no exception."
        )
        return True
    except subprocess.TimeoutExpired:
        logger.log(
            issuer="batch_solver",
            event_type="error",
            level=logging.ERROR,
            message=f"Subprocess timed out after {params['timeout_seconds']} seconds."
        )
    except Exception as e:
        logger.log(
            issuer="batch_solver",
            event_type="error",
            level=logging.ERROR,
            message=f"Exception: instance id={instance.identifier}, err: {e}"
        )
    return False

def run_process(search_algorithm, benchmark_path, log_folder, log_interval,
                timeout_seconds, order, min_length, max_length, heuristic_relaxation,
                domain_class=None, instance_ids=[], lift_prob=0.0, run_mode='mpi'):
    
    if run_mode == 'mpi':
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        
        if rank == 0:  # Master process
            instance_list = list_instances(benchmark_path, domain_class, instance_ids)
            instances = list(smart_instance_generator(
                instance_list,
                min_length=min_length,
                max_length=max_length,
                order=order
            ))
            
            # Package parameters for workers
            params = {
                'search_algorithm': search_algorithm,
                'benchmark_path': benchmark_path,
                'log_folder': log_folder,
                'log_interval': log_interval,
                'timeout_seconds': timeout_seconds,
                'heuristic_relaxation': heuristic_relaxation,
                'lift_prob': lift_prob
            }
            
            # Use MPIPoolExecutor to distribute work
            with MPIPoolExecutor() as executor:
                solve_with_params = partial(solve_instance_wrapper, params=params)
                results = list(executor.map(solve_with_params, instances))
                
            # Log detailed completion information
            total_instances = len(instances)
            successful = 0
            failed = 0
            skipped = 0
            failed_instances = []
            
            for instance, result in zip(instances, results):
                if result is True:
                    successful += 1
                elif result is None:
                    skipped += 1
                else:
                    failed += 1
                    failed_instances.append({
                        'id': instance.identifier,
                        'domain': instance.domain_class,
                        'name': instance.instance_name,
                        'length': instance.plan_length
                    })
            
            print("\n=== Execution Summary ===")
            print(f"Total instances: {total_instances}")
            print(f"Successfully processed: {successful}")
            print(f"Failed: {failed}")
            print(f"Skipped (already existed): {skipped}")
            print(f"Success rate: {(successful/total_instances)*100:.2f}%")
            
            if failed_instances:
                print("\n=== Failed Instances ===")
                for inst in failed_instances:
                    print(f"- ID: {inst['id']}")
                    print(f"  Domain: {inst['domain']}")
                    print(f"  Name: {inst['name']}")
                    print(f"  Plan Length: {inst['length']}")
                
                # Also save failed instances to a file for later reference
                failed_log_path = os.path.join(log_folder, 'failed_instances.yaml')
                with open(failed_log_path, 'w') as f:
                    yaml.dump({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'failed_instances': failed_instances,
                        'summary': {
                            'total': total_instances,
                            'successful': successful,
                            'failed': failed,
                            'skipped': skipped
                        }
                    }, f)
                print(f"\nFailed instances have been logged to: {failed_log_path}")
            
    elif run_mode == 'subprocess':
        # Original single-process implementation
        instance_list = list_instances(benchmark_path, domain_class, instance_ids)
        params = {
            'search_algorithm': search_algorithm,
            'benchmark_path': benchmark_path,
            'log_folder': log_folder,
            'log_interval': log_interval,
            'timeout_seconds': timeout_seconds,
            'heuristic_relaxation': heuristic_relaxation,
            'lift_prob': lift_prob
        }
        
        for instance in smart_instance_generator(instance_list, min_length=min_length,
                                              max_length=max_length, order=order):
            solve_instance_wrapper(instance, params)
            
    elif run_mode == 'pycall':
        # Original pycall implementation
        instance_list = list_instances(benchmark_path, domain_class, instance_ids)
        for instance in smart_instance_generator(instance_list, min_length=min_length,
                                              max_length=max_length, order=order):
            log_file = os.path.join(
                log_folder,
                f"{search_algorithm}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.yaml"
            )
            if os.path.isfile(log_file):
                continue
            print(f"> Starting by function call for file_name={log_file}")
            solve_instance(search_algorithm, str(benchmark_path), log_file,
                         str(log_interval), instance.identifier, str(lift_prob))
    else:
        raise NotImplementedError

def load_instance_ids(file_path):
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.")
    return instance_ids

if __name__ == "__main__":
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
    run_mode = config.get('run_mode', 'mpi')  # Default to MPI mode

    # run on fixed instance_ids
    instance_ids = config['instance_ids']
    if instance_ids == 'load_instance_ids':
        instance_ids = load_instance_ids('instance_ids_nonzero_h.json')
    elif instance_ids == 'instance_ids_small_exp_set':
        instance_ids = load_instance_ids('instance_ids_small_exp_set.json')

    print(f"Loaded configuration from: {config_file}")
    
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
