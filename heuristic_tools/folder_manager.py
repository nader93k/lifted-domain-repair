import contextlib
import os
import shutil
from pathlib import Path
import sys



@contextlib.contextmanager
def temporary_base_folder(new_base_folder):
    # Import the module containing the global variables
    import heuristic_tools.heuristic as h_module
    
    # Store the original paths
    original_paths = {
        'BASE_FOLDER': h_module.BASE_FOLDER,
        'INPUT_MODEL_DOMAIN': h_module.INPUT_MODEL_DOMAIN,
        'INPUT_MODEL_PROBLEM': h_module.INPUT_MODEL_PROBLEM,
        'OUTPUT_MODEL_DOMAIN': h_module.OUTPUT_MODEL_DOMAIN,
        'OUTPUT_MODEL_PROBLEM': h_module.OUTPUT_MODEL_PROBLEM,
        'OLD_OUTPUT_MODEL_DOMAIN': h_module.OLD_OUTPUT_MODEL_DOMAIN,
        'OLD_OUTPUT_MODEL_PROBLEM': h_module.OLD_OUTPUT_MODEL_PROBLEM,
        'DATALOG_THEORY': h_module.DATALOG_THEORY,
        'DATALOG_MODEL': h_module.DATALOG_MODEL,
        'GROUNDED_OUTPUT_SAS': h_module.GROUNDED_OUTPUT_SAS
    }
    
    # Create the new folder if it doesn't exist
    os.makedirs(new_base_folder, exist_ok=True)
    
    try:
        # Update all paths with new base folder
        h_module.BASE_FOLDER = new_base_folder
        h_module.INPUT_MODEL_DOMAIN = f"{new_base_folder}/domain-in.pddl"
        h_module.INPUT_MODEL_PROBLEM = f"{new_base_folder}/problem-in.pddl"
        h_module.OUTPUT_MODEL_DOMAIN = f"{new_base_folder}/domain-out.pddl"
        h_module.OUTPUT_MODEL_PROBLEM = f"{new_base_folder}/problem-out.pddl"
        h_module.OLD_OUTPUT_MODEL_DOMAIN = f"{new_base_folder}/old-domain-out.pddl"
        h_module.OLD_OUTPUT_MODEL_PROBLEM = f"{new_base_folder}/old-problem-out.pddl"
        h_module.DATALOG_THEORY = f"{new_base_folder}/datalog.theory"
        h_module.DATALOG_MODEL = f"{new_base_folder}/datalog.model"
        h_module.GROUNDED_OUTPUT_SAS = f"{new_base_folder}/out.sas"
        
        yield
    
    finally:
        # Restore original paths
        h_module.BASE_FOLDER = original_paths['BASE_FOLDER']
        h_module.INPUT_MODEL_DOMAIN = original_paths['INPUT_MODEL_DOMAIN']
        h_module.INPUT_MODEL_PROBLEM = original_paths['INPUT_MODEL_PROBLEM']
        h_module.OUTPUT_MODEL_DOMAIN = original_paths['OUTPUT_MODEL_DOMAIN']
        h_module.OUTPUT_MODEL_PROBLEM = original_paths['OUTPUT_MODEL_PROBLEM']
        h_module.OLD_OUTPUT_MODEL_DOMAIN = original_paths['OLD_OUTPUT_MODEL_DOMAIN']
        h_module.OLD_OUTPUT_MODEL_PROBLEM = original_paths['OLD_OUTPUT_MODEL_PROBLEM']
        h_module.DATALOG_THEORY = original_paths['DATALOG_THEORY']
        h_module.DATALOG_MODEL = original_paths['DATALOG_MODEL']
        h_module.GROUNDED_OUTPUT_SAS = original_paths['GROUNDED_OUTPUT_SAS']
        
        # Clean up generated files
        files_to_remove = [
            'domain-in.pddl',
            'problem-in.pddl',
            'domain-out.pddl',
            'problem-out.pddl',
            'old-domain-out.pddl',
            'old-problem-out.pddl',
            'datalog.theory',
            'datalog.model',
            'out.sas'
        ]
        
        #TODO uncomment this for production
        # for file in files_to_remove:
        #     file_path = Path(new_base_folder) / file
        #     try:
        #         if file_path.exists():
        #             file_path.unlink()
        #     except Exception as e:
        #         print(f"Warning: Failed to remove {file_path}: {e}")
        


@contextlib.contextmanager
def temporary_base_folder_old_h(new_base_folder):
    # Import the module containing the global variables
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import heuristic_tools.old_heuristic as h_module
    
    # Store the original paths
    original_paths = {
        'BASE_FOLDER': h_module.BASE_FOLDER,
        'INPUT_MODEL_DOMAIN': h_module.INPUT_MODEL_DOMAIN,
        'INPUT_MODEL_PROBLEM': h_module.INPUT_MODEL_PROBLEM,
        'OUTPUT_MODEL_DOMAIN': h_module.OUTPUT_MODEL_DOMAIN,
        'OUTPUT_MODEL_PROBLEM': h_module.OUTPUT_MODEL_PROBLEM,
        'OLD_OUTPUT_MODEL_DOMAIN': h_module.OLD_OUTPUT_MODEL_DOMAIN,
        'OLD_OUTPUT_MODEL_PROBLEM': h_module.OLD_OUTPUT_MODEL_PROBLEM,
        'DATALOG_THEORY': h_module.DATALOG_THEORY,
        'DATALOG_MODEL': h_module.DATALOG_MODEL,
        'GROUNDED_OUTPUT_SAS': h_module.GROUNDED_OUTPUT_SAS
    }
    
    # Create the new folder if it doesn't exist
    os.makedirs(new_base_folder, exist_ok=True)
    
    try:
        # Update all paths with new base folder
        h_module.BASE_FOLDER = new_base_folder
        h_module.INPUT_MODEL_DOMAIN = f"{new_base_folder}/domain-in.pddl"
        h_module.INPUT_MODEL_PROBLEM = f"{new_base_folder}/problem-in.pddl"
        h_module.OUTPUT_MODEL_DOMAIN = f"{new_base_folder}/domain-out.pddl"
        h_module.OUTPUT_MODEL_PROBLEM = f"{new_base_folder}/problem-out.pddl"
        h_module.OLD_OUTPUT_MODEL_DOMAIN = f"{new_base_folder}/old-domain-out.pddl"
        h_module.OLD_OUTPUT_MODEL_PROBLEM = f"{new_base_folder}/old-problem-out.pddl"
        h_module.DATALOG_THEORY = f"{new_base_folder}/datalog.theory"
        h_module.DATALOG_MODEL = f"{new_base_folder}/datalog.model"
        h_module.GROUNDED_OUTPUT_SAS = f"{new_base_folder}/out.sas"
        
        yield
    
    finally:
        # Restore original paths
        h_module.BASE_FOLDER = original_paths['BASE_FOLDER']
        h_module.INPUT_MODEL_DOMAIN = original_paths['INPUT_MODEL_DOMAIN']
        h_module.INPUT_MODEL_PROBLEM = original_paths['INPUT_MODEL_PROBLEM']
        h_module.OUTPUT_MODEL_DOMAIN = original_paths['OUTPUT_MODEL_DOMAIN']
        h_module.OUTPUT_MODEL_PROBLEM = original_paths['OUTPUT_MODEL_PROBLEM']
        h_module.OLD_OUTPUT_MODEL_DOMAIN = original_paths['OLD_OUTPUT_MODEL_DOMAIN']
        h_module.OLD_OUTPUT_MODEL_PROBLEM = original_paths['OLD_OUTPUT_MODEL_PROBLEM']
        h_module.DATALOG_THEORY = original_paths['DATALOG_THEORY']
        h_module.DATALOG_MODEL = original_paths['DATALOG_MODEL']
        h_module.GROUNDED_OUTPUT_SAS = original_paths['GROUNDED_OUTPUT_SAS']
        
        # Clean up generated files
        files_to_remove = [
            'domain-in.pddl',
            'problem-in.pddl',
            'domain-out.pddl',
            'problem-out.pddl',
            'old-domain-out.pddl',
            'old-problem-out.pddl',
            'datalog.theory',
            'datalog.model',
            'out.sas'
        ]

        #TODO uncomment this for production 
        # for file in files_to_remove:
        #     file_path = Path(new_base_folder) / file
        #     try:
        #         if file_path.exists():
        #             file_path.unlink()
        #     except Exception as e:
        #         print(f"Warning: Failed to remove {file_path}: {e}")





@contextlib.contextmanager
def temporary_base_folder_ground(base_path):
    """Context manager that provides a temporary directory for the grounding process.
    """
    # Import here to avoid circular imports
    from relaxation_generator.shortcuts import TMP_DIR
    
    # Store original TMP_DIR
    original_tmp_dir = TMP_DIR
    
    try:
        # Convert to Path and ensure absolute
        base_path = Path(base_path).resolve()
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Update the global TMP_DIR
        globals()['TMP_DIR'] = str(base_path)
        
        yield
        
    finally:
        # Restore original TMP_DIR
        globals()['TMP_DIR'] = original_tmp_dir
        
        #TODO uncomment for production
        # Clean up temporary directory if it exists
        # if 'base_path' in locals() and base_path.exists():
        #     shutil.rmtree(base_path)
