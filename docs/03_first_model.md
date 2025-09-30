# Your First Model

Let's build the simplest possible AML model: learning that "A implies B".

## The Problem

We want to teach the model a simple rule: "Whenever A is true, B must also be true."

This is like learning:
- "If it's raining, then the ground is wet"
- "If I press the light switch, then the light turns on"
- "If I eat, then I'm no longer hungry"

## Step 1: Set Up the Model

```python
import aml

# Create an empty model
model = aml.Model()

# Create an embedder (learning algorithm)
embedder = aml.sparse_crossing_embedder(model)

print("Model created!")
```

## Step 2: Define Constants

Constants represent the basic concepts in our problem.

```python
# Define our constants
A = 0  # First concept
B = 1  # Second concept

# Tell the model about these constants
for constant in [A, B]:
    model.cmanager.setNewConstantIndex()

print(f"Defined constants: A={A}, B={B}")
```

## Step 3: Create Training Data

We express "A implies B" as a positive duple (inclusion).

```python
# Create terms (sets of constants)
term_A = aml.LCSegment([A])      # Just A
term_B = aml.LCSegment([B])      # Just B

# Create the rule: "A implies B"
rule = aml.Duple(
    term_A,     # Left side: A
    term_B,     # Right side: B  
    True,       # Positive duple (inclusion)
    0,          # Generation (for tracking)
    1           # Region (for grouping)
)

print("Created rule: A → B")
```

## Step 4: Train the Model

```python
# Train with our rule
positive_duples = [rule]
negative_duples = []  # No negative examples for now

embedder.enforce(positive_duples, negative_duples)

print("Training complete!")
print(f"Model now has {len(model.atomization)} atoms")
```

## Step 5: Test the Model

Let's see if the model learned our rule.

```python
# Create test data
test_duples = [
    # Test the rule we taught: A → B
    aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    
    # Test something we didn't teach: B → A (should not be true)
    aml.Duple(aml.LCSegment([B]), aml.LCSegment([A]), True, 0, 1)
]

# Prepare test space (needed for evaluation)
test_space = aml.termSpace()
for duple in test_duples:
    duple.wL = test_space.add(duple.L)
    duple.wH = test_space.add(duple.R)

# Calculate lower atomic segments
constants_in_test = aml.CSegment([A, B])
las = aml.calculateLowerAtomicSegment(model.atomization, constants_in_test, True)
test_space.calculateLowerAtomicSegments(model.atomization, las)

# Test the model
result = embedder.test(test_duples)
print(f"Test result: {result}")
```

## Complete Example

Here's the full code in one place:

```python
import aml

def simple_implication_example():
    # Step 1: Set up
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Step 2: Define constants
    A, B = 0, 1
    for constant in [A, B]:
        model.cmanager.setNewConstantIndex()
    
    # Step 3: Create training data
    rule = aml.Duple(
        aml.LCSegment([A]),  # A
        aml.LCSegment([B]),  # implies B
        True, 0, 1
    )
    
    # Step 4: Train
    embedder.enforce([rule], [])
    
    # Step 5: Test
    test_duples = [
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
        aml.Duple(aml.LCSegment([B]), aml.LCSegment([A]), True, 0, 1)
    ]
    
    # Prepare test space
    test_space = aml.termSpace()
    for duple in test_duples:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    constants_in_test = aml.CSegment([A, B])
    las = aml.calculateLowerAtomicSegment(model.atomization, constants_in_test, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    result = embedder.test(test_duples)
    print(f"Model learned: A → B")
    print(f"Test result: {result}")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    simple_implication_example()
```

## What Happened?

1. **The model learned**: It created atoms that represent the relationship "A → B"
2. **Testing showed**: The first test (A → B) should have low error, the second (B → A) should have higher error
3. **Atoms were created**: The model built internal representations to capture the rule

## Understanding the Output

- **FPR (False Positive Rate)**: How often the model incorrectly says something is true
- **FNR (False Negative Rate)**: How often the model incorrectly says something is false
- **Lower values are better** for both metrics

## Next Steps

This was a very simple example. Next, let's explore [Understanding Duples](04_duples_explained.md) to learn about more complex relationships!