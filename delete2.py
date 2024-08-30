from collections import defaultdict

class DualKeyDict:
    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(list))

    def __getitem__(self, keys):
        key1, key2 = keys
        return self.data[key1][key2]

    def __setitem__(self, keys, value):
        key1, key2 = keys
        self.data[key1][key2] = value

    def append(self, keys, item):
        key1, key2 = keys
        self.data[key1][key2].append(item)

# Example usage
if __name__ == "__main__":
    d = DualKeyDict()
    
    # Appending items
    d.append(("a", 1), "apple")
    d.append(("a", 1), "apricot")
    d.append(("b", 2), "banana")
    
    # Accessing items
    print(d[("a", 1)])  # Output: ['apple', 'apricot']
    print(d[("b", 2)])  # Output: ['banana']
    print(d[("c", 3)])  # Output: [] (empty list for non-existent key)
    
    # Setting items
    d[("d", 4)] = ["date", "durian"]
    print(d[("d", 4)])  # Output: ['date', 'durian']