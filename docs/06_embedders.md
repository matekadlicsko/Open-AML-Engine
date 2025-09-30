# Working with Embedders

Embedders are the learning algorithms in AML. They take your duples (rules) and build models. Let's understand the different types and how to configure them.

## Types of Embedders

### 1. Sparse Crossing Embedder
**Best for**: Most real-world problems, large datasets, iterative learning

```python
import aml

model = aml.Model()
embedder = aml.sparse_crossing_embedder(model)
```

**Characteristics**:
- Scalable to large problems
- Approximates the optimal solution
- Good for iterative/online learning
- Handles noise well

### 2. Full Crossing Embedder
**Best for**: Small problems, when you need exact solutions

```python
embedder = aml.full_crossing_embedder(model)
```

**Characteristics**:
- Finds exact solutions
- Only works for small problems (< 30 variables)
- Computationally intensive
- Guarantees optimal results

## Sparse Crossing Parameters

The sparse crossing embedder has many parameters you can tune:

### Basic Parameters

```python
embedder = aml.sparse_crossing_embedder(model)

# Store successful positive duples for reuse
embedder.params.storePositives = True  # Default: True

# Reduce the number of atoms in the dual while keeping trace invariance
embedder.params.useReduceIndicators = True  # Default: False

# Use trace-based constraints (recommended)
embedder.params.enforceTraceConstraints = True  # Default: True
```

### Advanced Parameters

```python
# Alternative method for enforcing positive constraints (binary classification)
embedder.params.byQuotient = False  # Default: False

# Remove repeated atoms during learning
embedder.params.removeRepetitions = False  # Default: False

# Use trace-based reduction
embedder.params.reductionByTraces = True  # Default: True

# Constants don't change during training (optimization)
embedder.params.staticConstants = False  # Default: False

# Threshold for simplification (higher = more aggressive)
embedder.params.simplify_threshold = 1.5  # Default: 1.5

# Minimum fraction of negative indicator atoms
embedder.params.negativeIndicatorThreshold = 0.1  # Default: 0.1
```

## Full Crossing Parameters

```python
embedder = aml.full_crossing_embedder(model)
embedder.params = aml.params_full(
    calculateRedundancy=True,   # Remove redundant atoms
    removeRepetitions=True,     # Remove repeated atoms
    sortDuples=True,           # Sort for efficiency
    binary=False               # Optimize for binary problems
)
```

## Choosing the Right Embedder

### Use Sparse Crossing When:
- You have more than ~20 constants
- You're doing iterative/online learning
- You can tolerate approximate solutions
- You're working with noisy data
- You need scalability

### Use Full Crossing When:
- You have fewer than 20 constants
- You need exact solutions
- You're solving constraint satisfaction problems
- Computational time is not a concern
- You want the mathematically optimal result

## Configuration Examples

### Example 1: Binary Classification
```python
def setup_binary_classifier():
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Good settings for binary classification
    embedder.params.storePositives = True
    embedder.params.useReduceIndicators = True
    embedder.params.byQuotient = True  # Alternative positive enforcement
    embedder.params.staticConstants = True  # If features don't change
    
    return model, embedder
```

### Example 2: Multi-class Classification
```python
def setup_multiclass_classifier():
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Good settings for multi-class problems
    embedder.params.storePositives = True
    embedder.params.useReduceIndicators = True
    embedder.params.byQuotient = False  # Don't use for multi-class
    embedder.params.negativeIndicatorThreshold = 0.1  # Ensure diversity
    
    return model, embedder
```

### Example 3: Constraint Satisfaction
```python
def setup_constraint_solver():
    model = aml.Model()
    
    # Use full crossing for exact constraint satisfaction
    embedder = aml.full_crossing_embedder(model)
    embedder.params.calculateRedundancy = True
    embedder.params.removeRepetitions = True
    embedder.params.sortDuples = True
    
    return model, embedder
```

### Example 4: Large-Scale Learning
```python
def setup_large_scale():
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Optimized for large problems
    embedder.params.storePositives = False  # Save memory
    embedder.params.useReduceIndicators = True  # Reduce complexity
    embedder.params.reductionByTraces = True  # Aggressive reduction
    embedder.params.simplify_threshold = 1.2  # More frequent simplification
    
    return model, embedder
```

## Performance Tuning

### Memory Usage
```python
# Reduce memory usage
embedder.params.storePositives = False
embedder.params.removeRepetitions = True
```

### Speed Optimization
```python
# Faster training
embedder.params.simplify_threshold = 1.2  # Simplify more often
embedder.params.staticConstants = True    # If constants don't change
```

### Accuracy Improvement
```python
# Better accuracy
embedder.params.useReduceIndicators = True
embedder.params.negativeIndicatorThreshold = 0.2  # More diversity
```

## Monitoring Training

### Check Model Size
```python
print(f"Atoms in model: {len(model.atomization)}")
print(f"Union model size: {len(embedder.unionModel)}")
```

### Monitor Training Progress
```python
# After each training batch
print(f"FPR: {embedder.vars.FPR}, FNR: {embedder.vars.FNR}")
print(f"Positive examples seen: {embedder.vars.pcount}")
print(f"Negative examples seen: {embedder.vars.ncount}")
```

## Complete Example: Comparing Embedders

```python
import aml

def compare_embedders():
    # Problem: Learn A → B
    A, B = 0, 1
    
    def setup_model():
        model = aml.Model()
        for i in [A, B]:
            model.cmanager.setNewConstantIndex()
        return model
    
    # Rule: A implies B
    rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)
    
    # Test with sparse crossing
    print("=== Sparse Crossing ===")
    model1 = setup_model()
    embedder1 = aml.sparse_crossing_embedder(model1)
    embedder1.enforce([rule], [])
    print(f"Atoms created: {len(model1.atomization)}")
    
    # Test with full crossing
    print("=== Full Crossing ===")
    model2 = setup_model()
    embedder2 = aml.full_crossing_embedder(model2)
    embedder2.enforce([rule])
    print(f"Atoms created: {len(model2.atomization)}")

if __name__ == "__main__":
    compare_embedders()
```

## Best Practices

1. **Start with defaults**: The default parameters work well for most problems
2. **Tune incrementally**: Change one parameter at a time
3. **Monitor performance**: Watch model size and accuracy
4. **Use sparse for exploration**: Start with sparse crossing, switch to full if needed
5. **Consider your constraints**: Memory, time, and accuracy requirements

## Common Issues and Solutions

### Model Too Large
```python
embedder.params.simplify_threshold = 1.2  # Simplify more aggressively
embedder.params.useReduceIndicators = True
```

### Poor Accuracy
```python
embedder.params.negativeIndicatorThreshold = 0.2  # More diversity
embedder.params.storePositives = True  # Remember good examples
```

### Slow Training
```python
embedder.params.staticConstants = True  # If constants don't change
embedder.params.removeRepetitions = True
```

## Next Steps

Now that you understand embedders, let's learn about [Testing and Evaluation](07_testing.md) to measure how well your models perform!