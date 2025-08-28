# Useful commands to manage the jobs on a server.

# submit a job
sbatch job.slurm

# submit a job after another finishes
sbatch --dependency=afterany:66831 job.slurm

# status of my jobs
squeue -u $USER

# details
scontrol show job JOBID

# history (R: Running, PD: Pending, CG: Completing, CD: Completed, F: Failed)
sacct

# cancel
scancel JOBID

# check my usage
top -u u7899572

# interactive node
srun -p normal -w cpusrv-1 --cpus-per-task=4 --mem=20G -t 1:00:00 --pty bash

# available resources
sinfo -n cpusrv-1 -o "%n %C %e/%m"
scontrol show node cpusrv-1

# while sbatch is broken
srun --job-name=lift-n-repair --ntasks=1 --cpus-per-task=15 --cpu-bind=cores --export=ALL --partition=normal --mem=120G --time=15:00:00 singularity exec --bind /home/projects /home/projects/u7899572/ijcai-os-python.sif bash -c 'cd /home/remote/u7899572/lifted-white-plan-domain-repair && /home/projects/u7899572/conda-envs/main/bin/python3 batch_solver.py' > output.log 2>&1

# count num yamls generated
ls -l "/home/remote/u7899572/lifted-white-plan-domain-repair/exp_logs_anu/00 all"/*.yaml | wc -l


