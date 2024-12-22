#!/bin/bash
#SBATCH --partition=normal        # Partition name
#SBATCH --nodelist=cpusrv-1      # Specific node request
#SBATCH --mem=20G                # Memory request
#SBATCH --cpus-per-task=8        # CPUs per task
#SBATCH --time=08:00:00          # Time limit
#SBATCH --output=job_%j.log      # Standard output and error log

export SINGULARITY_NOCOLOR=1


# build sandbox from .def
singularity build --fakeroot --sandbox ijcai-nader/ ijcai-nader.def

# # build sandbox from SIF
# singularity build --sandbox ijcai-os-python/ ijcai-os-python.sif
