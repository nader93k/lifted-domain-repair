#!/bin/bash

# Get all directories and files except fd2 and pwl
BIND_PATHS=$(find . -mindepth 1 -maxdepth 1 \
    ! -name 'fd2' \
    ! -name 'pwl' \
    ! -name '.*' \
    -printf '-B ./%P:/repair-project/%P ')

# Run the container with all bindings
singularity run $BIND_PATHS container.sif