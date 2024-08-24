#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <transformation> <file to transform>"
    exit 1
fi

if [ ! -f "$2" ]; then
    echo "Error: $2 is not a valid file."
    exit 1
fi

SCRIPT_DIR=$(dirname "$0")
"$SCRIPT_DIR/datalog_transformer/cmake-build-debug/datalog_transformer" "$1" < "$2"