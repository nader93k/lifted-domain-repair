import heapq

# Create an empty list
heap = []

# Push items onto the heap
heapq.heappush(heap, (5, "task 1"))
heapq.heappush(heap, (2, "task 2"))
heapq.heappush(heap, (4, "task 3"))
heapq.heappush(heap, (1, "task 4"))
heapq.heappush(heap, (3, "task 5"))

print("Heap after pushing items:")
print(heap)

# Pop and print items from the heap
print("\nPopping items from the heap:")
while heap:
    priority, task = heapq.heappop(heap)
    print(f"Priority: {priority}, Task: {task}")

# Create a list and transform it into a heap
numbers = [5, 2, 4, 1, 3]
heapq.heapify(numbers)

print("\nList after heapify:")
print(numbers)

# Get the smallest item without popping it
smallest = numbers[0]
print(f"\nSmallest item: {smallest}")