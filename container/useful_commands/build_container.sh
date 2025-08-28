# Building Singularity or Docker files

# Singularity: build sandbox from .def
singularity build --fakeroot --sandbox ijcai-os-python/ ijcai-os-python.sif

# Docker: Build and run
docker build -t model-repair .
docker run --rm -it   -v "$PWD":/app2 model-repair bash