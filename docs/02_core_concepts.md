# Core Concepts

Before diving into code, let's understand the fundamental concepts that make AML unique.

## The Big Picture

Traditional machine learning learns patterns from data. AML learns **logical relationships** expressed as algebraic constraints. Think of it as teaching the computer rules like:
- "If it's raining AND I have an umbrella, then I stay dry"
- "If a number is even, then it's NOT odd"

## Key Components

### 1. Constants
Constants are the basic building blocks - think of them as features or variables.

```python
# In a weather prediction problem:
RAINING = 0
UMBRELLA = 1  
STAYING_DRY = 2
```

### 2. Terms
Terms are sets of constants that represent concepts or states.

```python
import aml

# "It's raining and I have an umbrella"
rainy_with_umbrella = aml.LCSegment([RAINING, UMBRELLA])

# "I stay dry"
staying_dry = aml.LCSegment([STAYING_DRY])
```

### 3. Duples
Duples express relationships between terms. There are two types:

**Inclusions (Positive Duples)**: "If Left, then Right"
```python
# "If raining + umbrella, then staying dry"
rule = aml.Duple(rainy_with_umbrella, staying_dry, True, 0, 1)
#                                                   ↑
#                                               positive=True
```

**Exclusions (Negative Duples)**: "Left and Right cannot both be true"
```python
# "Cannot be both raining and sunny"
sunny = aml.LCSegment([SUNNY])
rainy = aml.LCSegment([RAINING])
contradiction = aml.Duple(rainy, sunny, False, 0, 1)
#                                       ↑
#                                   positive=False
```

### 4. Atoms
Atoms are the learned building blocks that the model creates. They represent "atomic" concepts that cannot be broken down further. You don't create these directly - the learning algorithm builds them.

### 5. Models
Models contain collections of atoms that represent the learned knowledge.

```python
model = aml.Model()
# The model starts empty and learns by processing duples
```

### 6. Embedders
Embedders are the learning algorithms that process duples and build models.

```python
embedder = aml.sparse_crossing_embedder(model)
# This will learn from the duples you provide
```

## A Simple Mental Model

Think of AML like teaching a child rules:

1. **You show examples** (duples): "When it rains AND you have an umbrella, you stay dry"
2. **The child learns patterns** (atoms): The child figures out that "umbrella + rain" is a useful concept
3. **The child builds knowledge** (model): A collection of learned concepts and their relationships
4. **You test understanding**: Give new situations and see if the child applies the rules correctly

## Real-World Analogy: Learning to Drive

Imagine teaching someone to drive using AML:

```python
# Constants (features of driving situations)
RED_LIGHT = 0
GREEN_LIGHT = 1
PEDESTRIAN_CROSSING = 2
STOP_ACTION = 3
GO_ACTION = 4

# Rules (duples)
# "If red light, then stop"
red_means_stop = aml.Duple(
    aml.LCSegment([RED_LIGHT]), 
    aml.LCSegment([STOP_ACTION]), 
    True, 0, 1
)

# "Cannot go when pedestrian is crossing"
no_go_with_pedestrian = aml.Duple(
    aml.LCSegment([PEDESTRIAN_CROSSING]), 
    aml.LCSegment([GO_ACTION]), 
    False, 0, 1
)
```

The model learns these rules and can apply them to new driving situations.

## Why This Matters

AML is powerful because:
- **Interpretable**: You can understand why the model makes decisions
- **Logical**: It respects the constraints you define
- **Flexible**: Can handle complex logical relationships
- **Constraint-aware**: Perfect for problems with hard rules

## Next Steps

Now that you understand the concepts, let's build your [First Model](03_first_model.md) with a simple example!