import traceback

def print_call_stack():
    for line in traceback.format_stack():
        print(line.strip())

# Example usage
def function_c():
    print_call_stack()

def function_b():
    function_c()

def function_a():
    function_b()

function_a()