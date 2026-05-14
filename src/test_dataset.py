<<<<<<< HEAD
from datasets import load_dataset

# Load dataset from HuggingFace
dataset = load_dataset("d0r1h/ILC")

# Show dataset structure
print(dataset)

# Show column names
print("\nColumns:")
print(dataset["train"].column_names)

# Show first example
print("\nFirst Sample:\n")
print(dataset["train"][0])
=======
from datasets import load_dataset

# Load dataset from HuggingFace
dataset = load_dataset("d0r1h/ILC")

# Show dataset structure
print(dataset)

# Show column names
print("\nColumns:")
print(dataset["train"].column_names)

# Show first example
print("\nFirst Sample:\n")
print(dataset["train"][0])
>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
