import signal
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import sys
import subprocess
import yaml
import datetime
from multiprocessing import Process
import logging
import traceback
from custom_logger import StructuredLogger



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


def worker(instance, config_file, params):    
    start_time = datetime.datetime.now()
    print(f"[{start_time}] Starting to solve instance = {instance.identifier}", flush=True)

    log_file = os.path.join(params['log_folder'], f"{instance.identifier}.yaml")

    if os.path.isfile(log_file):
        os.remove(log_file)
    
    logger = StructuredLogger(log_file)
    
    cmd = [
        sys.executable,
        "instance_solver.py",
        str(config_file),
        instance.identifier,
    ]
    
    try:
        result = subprocess.run(cmd, check=True, timeout=params['timeout_seconds'],
                                capture_output=True, text=True)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"Instance ID = {instance.identifier} completed in {duration:.2f} seconds", flush=True)
        logger.log(
            issuer="batch_solver",
            event_type="general",
            level=logging.INFO,
            message=f"Subprocess finished successfully. Duration: {duration:.2f} seconds"
        )
        
    except subprocess.TimeoutExpired as e:
        # Log error reason
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"Instance ID = {instance.identifier} TIMEOUT on {instance.identifier} after {duration:.2f} seconds", flush=True)
        logger.log(
            issuer="batch_solver",
            event_type="error",
            level=logging.ERROR,
            message=f"Subprocess timed out after {params['timeout_seconds']} seconds."
        )
        
    except Exception as e:
        # Log error reason
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
            

def prepare_data(benchmark_path, domain_class, instance_ids, min_length, max_length, 
               order, log_folder, timeout_seconds):
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

    excluded_domains = [
        'pipesworld-notankage',
        'woodworking-opt08-strips',
        'woodworking-sat08-strips',
        'woodworking-sat11-strips',
        'woodworking-opt11-strips',
        'tidybot-opt11-strips',
        'data-network-opt18-strips',
        'snake-opt18-strips',
        'logistics00',
        'ged-opt14-strips'
    ]

    instances = [inst for inst in instances if inst.domain_class not in excluded_domains]
    
    print(f"Total instances to process: {len(instances)}", flush=True)
    
    # Prepare parameters
    params = {
        'log_folder': log_folder,
        'timeout_seconds': timeout_seconds
    }
    
    return instances, params


def run_process(config_file, benchmark_path, log_folder, timeout_seconds,
                order, min_length, max_length, domain_class=None, instance_ids=[]):
    start_time = datetime.datetime.now()
    print(f"[{start_time}] Batch solver started", flush=True)
    
    # Prepare data and parameters (now includes both checkpoint files)
    instances, params = prepare_data(
        benchmark_path, domain_class, instance_ids, min_length, max_length,
        order, log_folder, timeout_seconds
    )
    
    # Add tasks to queue
    for instance in instances:
        p = Process(target=worker, args=(instance, config_file, params))
        p.start()
        p.join()

        
    print(f"Finished processing all instances.", flush=True)


if __name__ == "__main__":
    config_file = sys.argv[1]
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    benchmark_path = Path(config['benchmark_path'])
    log_folder = Path(config['log_folder'])
    timeout_seconds = config['timeout_seconds']
    order = config['order']
    min_length = config['min_length']
    max_length = config['max_length']
    domain_class = config['domain_class'] 

    print(f"Loaded configuration from: {config_file}", flush=True)
    print("Configuration:", flush=True)
    for key, value in config.items():
        print(f"  {key}: {value}", flush=True)
    
    run_process(
        config_file=config_file,
        benchmark_path=benchmark_path,
        log_folder=log_folder,
        timeout_seconds=timeout_seconds,
        order=order,
        min_length=min_length,
        max_length=max_length,
        domain_class=domain_class
    )
