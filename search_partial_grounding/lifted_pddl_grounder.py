import subprocess
from pathlib import Path
from fd.pddl.tasks import Task
import os



def setup_ramdisk():
    ramdisk_path = Path("/dev/shm/pddl_grounder")
    # TODO add cleanup for ramdisk
    #TODO remove this
    ramdisk_path = Path("/home/remote/u7899572/lifted-white-plan-domain-repair/search_partial_grounding")

    ramdisk_path.mkdir(exist_ok=True)
    return ramdisk_path



def ground_pddl(domain, task, action_name, instance_id):
    base_folder = setup_ramdisk()
    
    domain_path = base_folder / f"domain_{instance_id}.pddl"
    with open(domain_path, "w") as f:
        content = domain.to_pddl(action_name)
        f.write(content)

    task_path = base_folder / f"task_{instance_id}.pddl"
    with open(task_path, "w") as f:
        content = task.to_pddl()
        f.write(content)

    python_path = "/home/projects/u7899572/conda-envs/grounder/bin/python3"
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    grounder_path = os.path.join(parent_dir, "search_partial_grounding", "grounder_service.py")
    
    try:
        result = subprocess.run(
            [
                python_path, grounder_path,
                "--domain_path", str(domain_path),
                "--task_path", str(task_path)
            ],
            capture_output=True,
            text=True,
            check=True
        )
            
        return result
    
    except subprocess.CalledProcessError as e:
        print(f"Grounding failed with error: {e.stderr}")
        raise
    except Exception as e:
        print(f"Failed to run grounder: {str(e)}")
        raise
    # finally:




    #     #TODO uncomment
    #     pass
    #     # domain_path.unlink(missing_ok=True)
    #     # task_path.unlink(missing_ok=True)
