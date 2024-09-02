from fd.pddl.conditions import Atom, Conjunction

def create_conjunction_from_atom(atom):
    if not isinstance(atom, Atom):
        raise TypeError("Input must be an instance of fd.pddl.conditions.Atom")
    
    # Create a Conjunction containing the given Atom
    conjunction = Conjunction([atom])
    
    return conjunction

# Example usage
if __name__ == "__main__":
    # Create an example Atom
    example_atom = Atom("on", ["block1", "table"])
    
    # Create a Conjunction from the Atom
    result_conjunction = create_conjunction_from_atom(example_atom)
    
    print(f"Input Atom: {example_atom}")
    print(f"Resulting Conjunction: {result_conjunction}")
