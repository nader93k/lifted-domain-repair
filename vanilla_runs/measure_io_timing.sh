#!/bin/bash

# Run command:
# vanilla_runs/measure_io_timing.sh vanilla_runs/run_pascal_vanilla.py

# Check if the Python script name is provided
if [ $# -eq 0 ]; then
    echo "Please provide the name of your Python script as an argument."
    echo "Usage: $0 <python_script.py>"
    exit 1
fi

PYTHON_SCRIPT=$1
PYTHON_INTERPRETER="/home/nader/miniconda3/envs/planning/bin/python"

# Check if the specified Python interpreter exists
if [ ! -f "$PYTHON_INTERPRETER" ]; then
    echo "Error: The specified Python interpreter does not exist."
    echo "Path: $PYTHON_INTERPRETER"
    exit 1
fi

# Start time
start_time=$(date +%s.%N)

# Run strace with timing and filtering for I/O related system calls
strace -T -e trace=read,write,open,close -o io_trace.txt $PYTHON_INTERPRETER "$PYTHON_SCRIPT" "${@:2}"

# End time
end_time=$(date +%s.%N)

# Calculate total execution time
total_time=$(echo "$end_time - $start_time" | bc)

# Process the strace output to calculate total I/O time
echo "Calculating I/O timings..."
io_time=$(awk '
    {
        time = $NF;
        gsub("<|>", "", time);
        total += time;
    }
    END {
        printf "%.6f", total;
    }
' io_trace.txt)

# Print results
printf "Total execution time: %.6f seconds\n" $total_time
printf "Total I/O time: %.6f seconds\n" $io_time
printf "Non-I/O time: %.6f seconds\n" $(echo "$total_time - $io_time" | bc)

# Optional: Count the number of I/O operations
echo "Counting I/O operations..."
echo "Read operations: $(grep -c "read(" io_trace.txt)"
echo "Write operations: $(grep -c "write(" io_trace.txt)"
echo "Open operations: $(grep -c "open(" io_trace.txt)"
echo "Close operations: $(grep -c "close(" io_trace.txt)"

# Clean up
rm io_trace.txt