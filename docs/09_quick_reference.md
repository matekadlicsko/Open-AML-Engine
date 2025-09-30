# Quick Reference Guide

This is a cheat sheet for common AML operations. Keep this handy while coding!

## Basic Setup

```python
import aml

# Create model and embedder
model = aml.Model()
embedder = aml.sparse_crossing_embedder(model)

# Alternative: full crossing (for small problems)
embedder = aml.full_crossing_embedder(model)
```

## Constants

```python
# Method 1: Manual constants
A, B, C = 0, 1, 2
for i in [A, B, C]:
    model.cmanager.setNewConstantIndex()

# Method 2: Named constants
A = model.cmanager.setNewConstantIndexWithName("A")
B = model.cmanager.setNewConstantIndexWithName("B")

# Method 3: Range of constants
constants = set(range(0, 10))  # Constants 0-9
for i in constants:
    model.cmanager.setNewConstantIndex()
```

## Terms (Sets of Constants)

```python
# Single constant
term_A = aml.LCSegment([A])

# Multiple constants (AND)
term_AB = aml.LCSegment([A, B])

# From a set
my_constants = {A, B, C}
term_ABC = aml.LCSegment(my_constants)
```

## Duples (Rules)

```python
# Positive duple: "If A, then B"
rule1 = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)

# Negative duple: "A and B cannot both be true"
rule2 = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), False, 0, 1)

# Complex rule: "If A and B, then C and D"
rule3 = aml.Duple(aml.LCSegment([A, B]), aml.LCSegment([C, D]), True, 0, 1)
```

## Training

```python
# Separate positive and negative rules
positive_rules = [rule1, rule3]  # Implications
negative_rules = [rule2]         # Exclusions

# Train the model
embedder.enforce(positive_rules, negative_rules)

# Alternative: only positive rules
embedder.enforce(positive_rules, [])

# Alternative: only negative rules  
embedder.enforce([], negative_rules)
```

## Testing

```python
# Create test cases
test_cases = [
    aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    aml.Duple(aml.LCSegment([C]), aml.LCSegment([D]), False, 0, 1),
]

# Setup test space
test_space = aml.termSpace()
for duple in test_cases:
    duple.wL = test_space.add(duple.L)
    duple.wH = test_space.add(duple.R)

# Calculate lower atomic segments
all_constants = aml.CSegment([A, B, C, D])  # All constants used
las = aml.calculateLowerAtomicSegment(model.atomization, all_constants, True)
test_space.calculateLowerAtomicSegments(model.atomization, las)

# Run test
result = embedder.test(test_cases)
print(f"Result: {result}")
print(f"FPR: {embedder.vars.FPR}, FNR: {embedder.vars.FNR}")
```

## Common Patterns

### Implication: A → B
```python
rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)
```

### AND Logic: (A ∧ B) → C
```python
rule = aml.Duple(aml.LCSegment([A, B]), aml.LCSegment([C]), True, 0, 1)
```

### OR Logic: (A ∨ B) → C
```python
rules = [
    aml.Duple(aml.LCSegment([A]), aml.LCSegment([C]), True, 0, 1),
    aml.Duple(aml.LCSegment([B]), aml.LCSegment([C]), True, 0, 1)
]
```

### Mutual Exclusion: ¬(A ∧ B)
```python
rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), False, 0, 1)
```

### Chain: A → B → C
```python
rules = [
    aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    aml.Duple(aml.LCSegment([B]), aml.LCSegment([C]), True, 0, 1)
]
```

## Embedder Configuration

### Sparse Crossing Parameters
```python
embedder = aml.sparse_crossing_embedder(model)

# Common configurations
embedder.params.storePositives = True           # Remember successful rules
embedder.params.useReduceIndicators = True      # Reduce model complexity
embedder.params.enforceTraceConstraints = True  # Use trace constraints
embedder.params.byQuotient = False             # Alternative method (binary only)
embedder.params.staticConstants = True          # Constants don't change
embedder.params.negativeIndicatorThreshold = 0.1  # Diversity control
```

### Full Crossing Parameters
```python
embedder = aml.full_crossing_embedder(model)
embedder.params = aml.params_full(
    calculateRedundancy=True,   # Remove redundant atoms
    removeRepetitions=True,     # Remove repeated atoms
    sortDuples=True,           # Sort for efficiency
    binary=False               # Binary optimization
)
```

## Debugging and Monitoring

```python
# Check model size
print(f"Atoms in model: {len(model.atomization)}")
print(f"Union model size: {len(embedder.unionModel)}")

# Check training progress
print(f"Positive examples seen: {embedder.vars.pcount}")
print(f"Negative examples seen: {embedder.vars.ncount}")

# Set verbosity
aml.config.verbosityLevel = aml.config.Verbosity.Info  # Debug, Info, Warn, Error, Crit

# Print spectrums (detailed model analysis)
aml.printLSpectrum(model.atomization)  # Length spectrum
aml.printGSpectrum(model.atomization)  # Generation spectrum
```

## Data Conversion Helpers

### Convert Grid to Constants
```python
def grid_to_constants(grid, black_offset=0, white_offset=None):
    """Convert a binary grid to constants."""
    if white_offset is None:
        white_offset = len(grid)
    
    constants = set()
    for i, cell in enumerate(grid):
        if cell == 1:  # Black
            constants.add(black_offset + i)
        else:  # White
            constants.add(white_offset + i)
    return constants

# Usage
grid = [1, 0, 1, 0]  # Binary pattern
constants = grid_to_constants(grid)
term = aml.LCSegment(constants)
```

### Convert Features to Constants
```python
def features_to_constants(features, base_offset=0):
    """Convert feature vector to constants."""
    constants = set()
    for i, feature in enumerate(features):
        if feature:  # Feature is present
            constants.add(base_offset + i)
    return constants

# Usage
features = [True, False, True, False]  # Feature presence
constants = features_to_constants(features)
term = aml.LCSegment(constants)
```

## File Operations

```python
# Save model
aml.saveAtomizationOnFile(model.atomization, model.cmanager, "my_model")

# Load model
cmanager, atomization = aml.loadAtomizationFromFile("my_model")

# For bitarray version (more efficient)
aml.saveAtomizationOnFileUsingBitarrays(model.atomization, model.cmanager, "my_model")
cmanager, atomization = aml.loadAtomizationFromFileUsingBitarrays("my_model")
```

## Error Handling

```python
try:
    embedder.enforce(positive_rules, negative_rules)
except ValueError as e:
    print(f"Training error: {e}")
    # Handle inconsistent rules

try:
    result = embedder.test(test_cases)
except Exception as e:
    print(f"Testing error: {e}")
    # Handle testing issues
```

## Performance Tips

```python
# For large problems
embedder.params.simplify_threshold = 1.2  # Simplify more often
embedder.params.removeRepetitions = True  # Remove duplicates

# For memory efficiency
embedder.params.storePositives = False    # Don't store all positive rules

# For accuracy
embedder.params.useReduceIndicators = True  # Better generalization
embedder.params.negativeIndicatorThreshold = 0.2  # More diversity
```

## Common Mistakes to Avoid

```python
# ❌ Wrong: Forgetting to register constants
A, B = 0, 1
rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)

# ✅ Correct: Register constants first
A, B = 0, 1
model.cmanager.setNewConstantIndex()  # A
model.cmanager.setNewConstantIndex()  # B
rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)

# ❌ Wrong: Testing without test space setup
result = embedder.test(test_cases)  # Will fail

# ✅ Correct: Setup test space first
test_space = aml.termSpace()
for duple in test_cases:
    duple.wL = test_space.add(duple.L)
    duple.wH = test_space.add(duple.R)
# ... (rest of test setup)
result = embedder.test(test_cases)
```

## Template: Complete Minimal Example

```python
import aml

def template_example():
    # 1. Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # 2. Constants
    A, B = 0, 1
    for i in [A, B]:
        model.cmanager.setNewConstantIndex()
    
    # 3. Rules
    rules = [
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    ]
    
    # 4. Train
    embedder.enforce(rules, [])
    
    # 5. Test
    test_cases = [
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    ]
    
    test_space = aml.termSpace()
    for duple in test_cases:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    constants = aml.CSegment([A, B])
    las = aml.calculateLowerAtomicSegment(model.atomization, constants, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    result = embedder.test(test_cases)
    print(f"Result: {result}")

if __name__ == "__main__":
    template_example()
```

This quick reference covers the most common AML operations. Keep it handy while you're learning and building your own models!