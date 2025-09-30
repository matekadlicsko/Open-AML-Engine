# AML Documentation

Welcome to the Open-AML-Engine documentation! This folder contains simple, step-by-step tutorials to help you understand and use Algebraic Machine Learning.

## Getting Started

1. **[Installation Guide](01_installation.md)** - Set up the AML package
2. **[Core Concepts](02_core_concepts.md)** - Understand the fundamental ideas
3. **[Your First Model](03_first_model.md)** - Build a simple classification model
4. **[Understanding Duples](04_duples_explained.md)** - Learn about inclusions and exclusions
5. **[Simple Pattern Recognition](05_pattern_recognition.md)** - Recognize basic patterns
6. **[Working with Embedders](06_embedders.md)** - Choose and configure learning algorithms
7. **[Testing and Evaluation](07_testing.md)** - Evaluate your models

## What is Algebraic Machine Learning?

AML is a unique approach to machine learning that:
- Uses algebraic structures to represent knowledge
- Learns through logical constraints (inclusions and exclusions)
- Provides interpretable models
- Handles constraint satisfaction naturally

## Quick Example

```python
import aml

# Create a model that learns "if A and B, then C"
model = aml.Model()
embedder = aml.sparse_crossing_embedder(model)

# Define constants
A, B, C = 0, 1, 2
for i in [A, B, C]:
    model.cmanager.setNewConstantIndex()

# Create training data: "A and B implies C"
left = aml.LCSegment([A, B])  # A and B together
right = aml.LCSegment([C])    # should imply C
positive_duple = aml.Duple(left, right, True, 0, 1)

# Train the model
embedder.enforce([positive_duple], [])
```

Start with the [Installation Guide](01_installation.md) to begin your AML journey!