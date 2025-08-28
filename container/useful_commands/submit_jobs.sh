#!/bin/bash

# A bash script to submit multiple jobs for multiple config files using Singularity

# List of config files
yaml_files=(
    "gbfs-unary-ff_exhaust_lp066.yaml"
    "gbfs-unary-ff_exhaust_lp1.yaml"
    "gbfs-unary_exhaust_lp033.yaml"
    "gbfs-unary_exhaust_lp066.yaml"
    "gbfs-unary_exhaust_lp1.yaml"
)


# Loop through each YAML file and submit a job
for yaml_file in "${yaml_files[@]}"; do
    sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=lift-n-repair-${yaml_file}
#SBATCH --ntasks=1
#SBATCH --partition=normal
#SBATCH --nodelist=cpusrv-1
#SBATCH --mem=165G
#SBATCH --cpus-per-task=20
#SBATCH --time=4:00:00
#SBATCH --output=job_%j_${yaml_file}.log

# Print job info
echo "Job started at: \$(date)"
echo "Running on node: \$(hostname)"
echo "Processing file: ${yaml_file}"

# Run your code inside singularity container
singularity exec --bind /home/projects /home/projects/u7899572/ijcai-os-python.sif bash -c \
    "cd /home/remote/u7899572/lifted-white-plan-domain-repair && /home/projects/u7899572/conda-envs/main/bin/python3 batch_solver.py configs_exhaustive/${yaml_file}"

echo "Job finished at: \$(date)"
EOF
done
