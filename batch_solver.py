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
import logging
import traceback
from custom_logger import StructuredLogger
import signal
import resource



DEBUG = True
# DEBUG = False


def get_allowed_cpus():
    """Get the list of allowed CPU cores for the current process"""
    try:
        process = psutil.Process()
        return list(process.cpu_affinity())
    except Exception as e:
        print(f"Error getting CPU affinity: {e}")
        return list(range(cpu_count()))


def is_memory_related_error(error, stderr=None):
    """
    Helper function to identify memory-related errors from both Python and OS level
    
    Args:
        error: The error object or error string to analyze
        stderr: Optional stderr output from subprocess execution
        
    Returns:
        bool: True if the error appears to be memory-related
    """
    def check_string_for_memory_error(s):
        memory_indicators = [
            'memoryerror',
            'errno 12',         # Cannot allocate memory
            'cannot allocate memory',
            'out of memory',
            'oom',             # Out Of Memory
            'killed',          # Often OOM killer
            'allocation failed',
            'virtual memory exhausted',
            # Signal related
            'sigabrt: 6',
            'signals.sigabrt: 6',
            'signal 6',        # SIGABRT
            'signal 9',        # SIGKILL
            'signal 11'        # SIGSEGV
        ]
        s = s.lower()
        return any(indicator in s for indicator in memory_indicators)

    # Check stderr first if provided
    if stderr:
        if check_string_for_memory_error(stderr):
            return True

    # Check stdout if available in subprocess error
    if hasattr(error, 'stdout') and error.stdout:
        if check_string_for_memory_error(error.stdout):
            return True

    # Direct check for MemoryError
    if isinstance(error, MemoryError):
        return True
            
    # Check for subprocess error signals
    if isinstance(error, subprocess.SubprocessError):
        if hasattr(error, 'returncode'):
            rc = abs(error.returncode) if error.returncode < 0 else error.returncode
            if rc in {signal.SIGABRT, signal.SIGBUS, signal.SIGKILL, signal.SIGSEGV}:
                return True
    
    # Finally check the error string itself
    return check_string_for_memory_error(str(error))

def worker(worker_id, task_queue, result_queue, params):
    """Worker process function that processes instances from the queue"""
    while True:
        try:
            instance = task_queue.get()
            if instance is None:  # Poison pill
                print(f"[{datetime.datetime.now()}] Worker {worker_id} terminated.", flush=True)
                break
                
            start_time = datetime.datetime.now()
            print(f"[{start_time}] Worker {worker_id} starting instance {instance.identifier}", flush=True)
            
            log_file = os.path.join(params['log_folder'], f"{instance.identifier}.yaml")
            
            if os.path.isfile(log_file):
                os.remove(log_file)
            
            logger = StructuredLogger(log_file)
            
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
                if DEBUG:
                    result = subprocess.run(cmd, check=True, timeout=params['timeout_seconds'])
                else:
                    result = subprocess.run(cmd, check=True, timeout=params['timeout_seconds'],
                                        capture_output=True, text=True)
                
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"[{end_time}] Worker {worker_id} completed {instance.identifier} in {duration:.2f} seconds", flush=True)
                logger.log(
                    issuer="batch_solver",
                    event_type="general",
                    level=logging.INFO,
                    message=f"Subprocess finished successfully. Duration: {duration:.2f} seconds"
                )
                
                result_queue.put((True, instance.identifier))
                
            except subprocess.TimeoutExpired as e:
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"[{end_time}] Worker {worker_id} TIMEOUT on {instance.identifier} after {duration:.2f} seconds", flush=True)
                logger.log(
                    issuer="batch_solver",
                    event_type="error",
                    level=logging.ERROR,
                    message=f"Subprocess timed out after {params['timeout_seconds']} seconds."
                )
                result_queue.put((True, instance.identifier))
                
            except Exception as e:
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                stack_trace = traceback.format_exc()
                
                process_info = {
                    'cmd': cmd,
                    'duration': f"{duration:.2f}",
                    'python_executable': sys.executable,
                }
                
                is_memory_error = is_memory_related_error(e, stderr=e.stderr if hasattr(e, 'stderr') else None)
                
                print(f"[{end_time}] Worker {worker_id} {'MEMORY ERROR' if is_memory_error else 'ERROR'} on {instance.identifier} after {duration:.2f} seconds:", flush=True)
                print(f"Error type: {type(e).__name__}", flush=True)
                print(f"Error message: {str(e)}", flush=True)
                print(f"Stack trace:\n{stack_trace}", flush=True)
                
                error_info = {
                    "error_type": "MemoryError" if is_memory_error else type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": stack_trace,
                    "instance_id": instance.identifier,
                    "process_info": process_info
                }
                
                if hasattr(e, 'stdout'):
                    error_info['stdout'] = e.stdout
                if hasattr(e, 'stderr'):
                    error_info['stderr'] = e.stderr
                
                logger.log(
                    issuer="batch_solver",
                    event_type="error",
                    level=logging.ERROR,
                    message=error_info
                )
                
                if is_memory_error:
                    result_queue.put((True, instance.identifier))
                else:
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
    
    # Setup checkpoint files
    checkpoint_file = os.path.join(log_folder, "00_checkpoint.json")
    checkpoint_errors = os.path.join(log_folder, "00_checkpoint_errors.json")
    
    # Create checkpoint files if they don't exist
    for file_path in [checkpoint_file, checkpoint_errors]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
            print(f"Created new checkpoint file: {file_path}", flush=True)
    
    # Load successful checkpoint
    with open(checkpoint_file, 'r') as f:
        completed_instances = set(json.load(f))
        print(f"Loaded {len(completed_instances)} completed instances from checkpoint", flush=True)
    
    # Load error checkpoint
    with open(checkpoint_errors, 'r') as f:
        error_instances = set(json.load(f))
        print(f"Loaded {len(error_instances)} error instances from checkpoint", flush=True)
    
    # Combine both sets for filtering
    all_completed = completed_instances.union(error_instances)
    
    # Filter remaining instances
    remaining_instances = [inst for inst in instances if inst.identifier not in all_completed]
    print(f"Remaining instances to process: {len(remaining_instances)}", flush=True)
    
    return remaining_instances, params, checkpoint_file, checkpoint_errors


def run_process(search_algorithm, benchmark_path, log_folder, log_interval,
                timeout_seconds, order, min_length, max_length, heuristic_relaxation,
                domain_class=None, instance_ids=[], lift_prob=0.0):
    
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
    
    # Prepare data and parameters (now includes both checkpoint files)
    remaining_instances, params, checkpoint_file, checkpoint_errors = prepare_data(
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
    
    # Collect results and update checkpoint files
    successful = 0
    total_processed = 0
    
    while total_processed < len(remaining_instances):
        success, instance_id = result_queue.get()
        total_processed += 1
        
        print(f"[{datetime.datetime.now()}] Processed {total_processed}/{len(remaining_instances)} instances. Current instance: {instance_id}", flush=True)
        
        if success:
            successful += 1
            print(f"[{datetime.datetime.now()}] Instance {instance_id} completed successfully. Total successful: {successful}/{total_processed}", flush=True)
            
            # Update success checkpoint file
            try:
                with open(checkpoint_file, 'r') as f:
                    completed = set(json.load(f))
                    print(f"Loaded existing checkpoint with {len(completed)} completed instances", flush=True)
            except (FileNotFoundError, json.JSONDecodeError):
                completed = set()
                print(f"No existing checkpoint found or invalid JSON. Creating new checkpoint file", flush=True)
            
            completed.add(instance_id)
            
            # Write and flush the updated checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump(list(completed), f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure the file is written to disk
            
            print(f"Updated checkpoint file with {len(completed)} completed instances", flush=True)
            
        else:
            # Update error checkpoint file
            try:
                with open(checkpoint_errors, 'r') as f:
                    error_completed = set(json.load(f))
                    print(f"Loaded existing error checkpoint with {len(error_completed)} error instances", flush=True)
            except (FileNotFoundError, json.JSONDecodeError):
                error_completed = set()
                print(f"No existing error checkpoint found or invalid JSON. Creating new error checkpoint file", flush=True)
            
            error_completed.add(instance_id)
            
            # Write and flush the updated error checkpoint
            with open(checkpoint_errors, 'w') as f:
                json.dump(list(error_completed), f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure the file is written to disk
            
            print(f"[{datetime.datetime.now()}] Instance {instance_id} completed with errors. Added to error checkpoint.", flush=True)
            print(f"Updated error checkpoint file with {len(error_completed)} error instances", flush=True)
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time}] Batch solver completed. Total duration: {duration:.2f} seconds", flush=True)
    print(f"Successfully completed instances: {successful}/{len(remaining_instances)}", flush=True)
    
    # Load final counts for comprehensive report
    try:
        with open(checkpoint_file, 'r') as f:
            final_completed = len(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        final_completed = 0
        
    try:
        with open(checkpoint_errors, 'r') as f:
            final_errors = len(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        final_errors = 0
        
    print(f"Final status:", flush=True)
    print(f"  Total successful completions: {final_completed}", flush=True)
    print(f"  Total error completions: {final_errors}", flush=True)
    print(f"  Total instances processed: {final_completed + final_errors}", flush=True)


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
        lift_prob=lift_prob
    )
