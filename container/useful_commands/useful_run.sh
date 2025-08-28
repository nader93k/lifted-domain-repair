# Useful commands to connect to computing nodes, and get interactive shells to a Singularity image. 

# Connect to the computing nodes
srun -p normal --time=5:00:00 --cpus-per-task=1 --mem=8G --pty bash
srun -p normal -w cpusrv-1 --time=5:00:00 --cpus-per-task=1 --mem=8G --pty bash
# interactive singularity
singularity shell --bind /home/projects /home/projects/u7899572/ijcai-os-python.sif

# activate virtualenv and run the solver
source $HOME/.bashrc
conda activate main
python3 /home/remote/u7899572/lifted-white-plan-domain-repair/batch_solver.py

#### BUILD Singularity
# development
sudo singularity build --sandbox nader-ijcai singularity.def
sudo singularity shell --writable nader-ijcai

# Production
sudo singularity build --no-cleanup ijcai-os-python.sif ijcai-os-python.def
sudo singularity build --no-cleanup ijcai-nader.sif ijcai-nader.def
