# Testing and Evaluation

Once you've trained an AML model, you need to test how well it learned. This guide shows you different ways to evaluate your models.

## Basic Testing Workflow

### Step 1: Create Test Data
```python
import aml

# Create test duples (same format as training)
test_duples = [
    aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
    aml.Duple(aml.LCSegment([C]), aml.LCSegment([D]), False, 0, 1),
    # ... more test cases
]
```

### Step 2: Prepare Test Space
```python
# Create a term space for efficient testing
test_space = aml.termSpace()

# Add all terms to the space
for duple in test_duples:
    duple.wL = test_space.add(duple.L)
    duple.wH = test_space.add(duple.R)

# Calculate lower atomic segments
constants_in_test = aml.CSegment([A, B, C, D])  # All constants used
las = aml.calculateLowerAtomicSegment(model.atomization, constants_in_test, True)
test_space.calculateLowerAtomicSegments(model.atomization, las)
```

### Step 3: Run Tests
```python
# Test the model
result = embedder.test(test_duples)
print(f"Test result: {result}")
```

## Understanding Test Results

The test returns a string with two key metrics:

- **FPR (False Positive Rate)**: How often the model incorrectly says "yes"
- **FNR (False Negative Rate)**: How often the model incorrectly says "no"

```python
# Access individual metrics
print(f"False Positive Rate: {embedder.vars.FPR}")
print(f"False Negative Rate: {embedder.vars.FNR}")
```

**Lower values are better** for both metrics.

## Simple Testing Example

Let's test a model that learned "A implies B":

```python
def test_simple_implication():
    # Setup and train model
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    A, B = 0, 1
    for i in [A, B]:
        model.cmanager.setNewConstantIndex()
    
    # Train: A → B
    training_rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)
    embedder.enforce([training_rule], [])
    
    # Test cases
    test_cases = [
        # Should be correct (low FNR)
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
        
        # Should be rejected (low FPR)
        aml.Duple(aml.LCSegment([B]), aml.LCSegment([A]), True, 0, 1),
    ]
    
    # Prepare and run test
    test_space = aml.termSpace()
    for duple in test_cases:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    constants = aml.CSegment([A, B])
    las = aml.calculateLowerAtomicSegment(model.atomization, constants, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    result = embedder.test(test_cases)
    print(f"Test result: {result}")
    
    return embedder.vars.FPR, embedder.vars.FNR

fpr, fnr = test_simple_implication()
print(f"FPR: {fpr:.3f}, FNR: {fnr:.3f}")
```

## Testing Different Aspects

### Test 1: Positive Rules (Implications)
```python
def test_positive_rules(model, embedder):
    """Test if the model correctly learned positive implications."""
    positive_tests = [
        # Test cases where the implication should hold
        aml.Duple(aml.LCSegment([CONDITION]), aml.LCSegment([RESULT]), True, 0, 1),
    ]
    
    # Setup and test
    test_space = aml.termSpace()
    for duple in positive_tests:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    # ... (rest of testing setup)
    result = embedder.test(positive_tests)
    return result
```

### Test 2: Negative Rules (Exclusions)
```python
def test_negative_rules(model, embedder):
    """Test if the model correctly learned exclusions."""
    negative_tests = [
        # Test cases where things should be mutually exclusive
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), False, 0, 1),
    ]
    
    # ... (testing setup)
    result = embedder.test(negative_tests)
    return result
```

### Test 3: Generalization
```python
def test_generalization(model, embedder):
    """Test if the model generalizes to unseen combinations."""
    generalization_tests = [
        # Test with combinations not seen during training
        aml.Duple(aml.LCSegment([A, C]), aml.LCSegment([B]), True, 0, 1),
    ]
    
    # ... (testing setup)
    result = embedder.test(generalization_tests)
    return result
```

## Complete Testing Example

Here's a comprehensive testing example for a traffic light model:

```python
import aml

def comprehensive_traffic_light_test():
    # Setup model
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    RED, GREEN, YELLOW, STOP, GO = 0, 1, 2, 3, 4
    for i in range(5):
        model.cmanager.setNewConstantIndex()
    
    # Training rules
    training_rules = [
        # Positive rules
        aml.Duple(aml.LCSegment([RED]), aml.LCSegment([STOP]), True, 0, 1),
        aml.Duple(aml.LCSegment([GREEN]), aml.LCSegment([GO]), True, 0, 1),
        
        # Negative rules
        aml.Duple(aml.LCSegment([RED]), aml.LCSegment([GREEN]), False, 0, 1),
        aml.Duple(aml.LCSegment([STOP]), aml.LCSegment([GO]), False, 0, 1),
    ]
    
    positive_rules = [r for r in training_rules if r.positive]
    negative_rules = [r for r in training_rules if not r.positive]
    embedder.enforce(positive_rules, negative_rules)
    
    # Test cases
    test_cases = [
        # Should work (learned rules)
        aml.Duple(aml.LCSegment([RED]), aml.LCSegment([STOP]), True, 0, 1),
        aml.Duple(aml.LCSegment([GREEN]), aml.LCSegment([GO]), True, 0, 1),
        
        # Should be rejected (contradictions)
        aml.Duple(aml.LCSegment([RED]), aml.LCSegment([GO]), True, 0, 1),
        aml.Duple(aml.LCSegment([GREEN]), aml.LCSegment([STOP]), True, 0, 1),
        
        # Exclusions should hold
        aml.Duple(aml.LCSegment([RED]), aml.LCSegment([GREEN]), False, 0, 1),
        aml.Duple(aml.LCSegment([STOP]), aml.LCSegment([GO]), False, 0, 1),
    ]
    
    # Setup test space
    test_space = aml.termSpace()
    for duple in test_cases:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    constants = aml.CSegment(list(range(5)))
    las = aml.calculateLowerAtomicSegment(model.atomization, constants, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    # Run comprehensive test
    result = embedder.test(test_cases)
    
    print("=== Traffic Light Model Test ===")
    print(f"Overall result: {result}")
    print(f"FPR: {embedder.vars.FPR:.3f}")
    print(f"FNR: {embedder.vars.FNR:.3f}")
    print(f"Model atoms: {len(model.atomization)}")
    
    return embedder.vars.FPR, embedder.vars.FNR

if __name__ == "__main__":
    fpr, fnr = comprehensive_traffic_light_test()
```

## Interpreting Results

### Good Results
- **FPR ≈ 0.0**: Model doesn't make false positive errors
- **FNR ≈ 0.0**: Model doesn't make false negative errors
- **Both low**: Model learned the rules correctly

### Problematic Results
- **High FPR**: Model is too permissive (says "yes" too often)
- **High FNR**: Model is too restrictive (says "no" too often)
- **Both high**: Model is confused

### Example Interpretations
```python
if fpr < 0.1 and fnr < 0.1:
    print("✅ Excellent: Model learned very well")
elif fpr < 0.2 and fnr < 0.2:
    print("✅ Good: Model learned reasonably well")
elif fpr > 0.5 or fnr > 0.5:
    print("❌ Poor: Model needs more training or different parameters")
else:
    print("⚠️  Fair: Model learned partially")
```

## Advanced Testing Techniques

### Cross-Validation
```python
def cross_validate(all_duples, k_folds=5):
    """Simple k-fold cross-validation for AML models."""
    import random
    random.shuffle(all_duples)
    
    fold_size = len(all_duples) // k_folds
    results = []
    
    for i in range(k_folds):
        # Split data
        start = i * fold_size
        end = start + fold_size
        test_fold = all_duples[start:end]
        train_folds = all_duples[:start] + all_duples[end:]
        
        # Train and test
        model = aml.Model()
        embedder = aml.sparse_crossing_embedder(model)
        
        # ... (setup constants, train, test)
        # results.append((fpr, fnr))
    
    return results
```

### Testing with Noise
```python
def test_with_noise(model, embedder, clean_test_cases, noise_level=0.1):
    """Test model robustness by adding noise to test cases."""
    import random
    
    noisy_tests = []
    for duple in clean_test_cases:
        # Add random constants with some probability
        if random.random() < noise_level:
            # Add noise to the test case
            pass  # Implementation depends on your problem
    
    # Test with noisy data
    result = embedder.test(noisy_tests)
    return result
```

## Best Practices

1. **Test incrementally**: Test after each major change
2. **Use diverse test cases**: Include edge cases and corner cases
3. **Test both positive and negative examples**: Make sure both work
4. **Monitor during training**: Check performance periodically
5. **Compare baselines**: Test against simple baseline models
6. **Test generalization**: Use examples not seen during training

## Common Testing Mistakes

1. **Testing on training data**: Always use separate test data
2. **Forgetting test space setup**: The preparation steps are crucial
3. **Ignoring one metric**: Both FPR and FNR matter
4. **Not testing edge cases**: Include boundary conditions
5. **Overfitting to test results**: Don't tune too much based on test performance

## Next Steps

Congratulations! You now understand the basics of AML. Here are some next steps:

1. **Try the full examples**: Run the examples in the `Examples/` folder
2. **Experiment with parameters**: Try different embedder configurations
3. **Build your own problem**: Apply AML to a domain you're interested in
4. **Read the research paper**: Understand the theoretical foundations
5. **Join the community**: Contribute to the project or ask questions

Happy learning with Algebraic Machine Learning!