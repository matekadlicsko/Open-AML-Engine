# Toy Examples Collection

This document contains a collection of the simplest possible AML examples. Each example is completely self-contained and demonstrates a single concept.

## Example 1: Single Implication

The absolute simplest AML model - learning "A implies B".

```python
import aml

def example_single_implication():
    """Learn: If A, then B"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B = 0, 1
    model.cmanager.setNewConstantIndex()  # A
    model.cmanager.setNewConstantIndex()  # B
    
    # Rule: A → B
    rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)
    
    # Train
    embedder.enforce([rule], [])
    
    print("✅ Learned: A → B")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_single_implication()
```

## Example 2: Simple Exclusion

Learning that two things cannot both be true.

```python
import aml

def example_simple_exclusion():
    """Learn: A and B cannot both be true"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B = 0, 1
    model.cmanager.setNewConstantIndex()  # A
    model.cmanager.setNewConstantIndex()  # B
    
    # Rule: NOT (A AND B)
    rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), False, 0, 1)
    
    # Train
    embedder.enforce([], [rule])
    
    print("✅ Learned: A and B are mutually exclusive")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_simple_exclusion()
```

## Example 3: AND Logic

Learning "A AND B implies C".

```python
import aml

def example_and_logic():
    """Learn: If A AND B, then C"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B, C = 0, 1, 2
    for i in range(3):
        model.cmanager.setNewConstantIndex()
    
    # Rule: (A AND B) → C
    rule = aml.Duple(aml.LCSegment([A, B]), aml.LCSegment([C]), True, 0, 1)
    
    # Train
    embedder.enforce([rule], [])
    
    print("✅ Learned: (A AND B) → C")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_and_logic()
```

## Example 4: OR Logic

Learning "A OR B implies C" using multiple rules.

```python
import aml

def example_or_logic():
    """Learn: If A OR B, then C"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B, C = 0, 1, 2
    for i in range(3):
        model.cmanager.setNewConstantIndex()
    
    # Rules: A → C and B → C (equivalent to (A OR B) → C)
    rules = [
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([C]), True, 0, 1),
        aml.Duple(aml.LCSegment([B]), aml.LCSegment([C]), True, 0, 1)
    ]
    
    # Train
    embedder.enforce(rules, [])
    
    print("✅ Learned: (A OR B) → C")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_or_logic()
```

## Example 5: Chain of Implications

Learning a chain: A → B → C.

```python
import aml

def example_chain():
    """Learn: A → B → C"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B, C = 0, 1, 2
    for i in range(3):
        model.cmanager.setNewConstantIndex()
    
    # Rules: A → B and B → C
    rules = [
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
        aml.Duple(aml.LCSegment([B]), aml.LCSegment([C]), True, 0, 1)
    ]
    
    # Train
    embedder.enforce(rules, [])
    
    print("✅ Learned: A → B → C")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_chain()
```

## Example 6: Simple Classification

A tiny binary classifier that learns to distinguish two classes.

```python
import aml

def example_simple_classifier():
    """Learn to classify: features → class"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    FEATURE1, FEATURE2, CLASS_A, CLASS_B = 0, 1, 2, 3
    for i in range(4):
        model.cmanager.setNewConstantIndex()
    
    # Training rules
    rules = [
        # If feature1, then class A
        aml.Duple(aml.LCSegment([FEATURE1]), aml.LCSegment([CLASS_A]), True, 0, 1),
        
        # If feature2, then class B  
        aml.Duple(aml.LCSegment([FEATURE2]), aml.LCSegment([CLASS_B]), True, 0, 1),
        
        # Classes are mutually exclusive
        aml.Duple(aml.LCSegment([CLASS_A]), aml.LCSegment([CLASS_B]), False, 0, 1)
    ]
    
    positive_rules = [r for r in rules if r.positive]
    negative_rules = [r for r in rules if not r.positive]
    
    # Train
    embedder.enforce(positive_rules, negative_rules)
    
    print("✅ Learned: Simple binary classifier")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_simple_classifier()
```

## Example 7: Tiny State Machine

Learning state transitions.

```python
import aml

def example_state_machine():
    """Learn: OFF → ON → OFF"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    OFF, ON, PRESS_BUTTON = 0, 1, 2
    for i in range(3):
        model.cmanager.setNewConstantIndex()
    
    # State transition rules
    rules = [
        # If OFF and press button, then ON
        aml.Duple(aml.LCSegment([OFF, PRESS_BUTTON]), aml.LCSegment([ON]), True, 0, 1),
        
        # If ON and press button, then OFF
        aml.Duple(aml.LCSegment([ON, PRESS_BUTTON]), aml.LCSegment([OFF]), True, 0, 1),
        
        # Cannot be both ON and OFF
        aml.Duple(aml.LCSegment([ON]), aml.LCSegment([OFF]), False, 0, 1)
    ]
    
    positive_rules = [r for r in rules if r.positive]
    negative_rules = [r for r in rules if not r.positive]
    
    # Train
    embedder.enforce(positive_rules, negative_rules)
    
    print("✅ Learned: Simple state machine")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_state_machine()
```

## Example 8: Micro Pattern Recognition

Recognizing a 2x2 pattern.

```python
import aml

def example_micro_pattern():
    """Learn to recognize a 2x2 cross pattern"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants for 2x2 grid positions
    # [0] [1]
    # [2] [3]
    POS0, POS1, POS2, POS3, CROSS_PATTERN = 0, 1, 2, 3, 4
    for i in range(5):
        model.cmanager.setNewConstantIndex()
    
    # Cross pattern: positions 1 and 2 are filled
    # ·█
    # █·
    cross_rule = aml.Duple(
        aml.LCSegment([POS1, POS2]),  # Positions 1 and 2 filled
        aml.LCSegment([CROSS_PATTERN]),  # Is a cross pattern
        True, 0, 1
    )
    
    # Train
    embedder.enforce([cross_rule], [])
    
    print("✅ Learned: 2x2 cross pattern recognition")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_micro_pattern()
```

## Example 9: Simple Constraint Satisfaction

Learning constraints for a tiny puzzle.

```python
import aml

def example_constraint_satisfaction():
    """Learn constraints: each position gets exactly one color"""
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants: 2 positions, 2 colors
    POS1_RED, POS1_BLUE, POS2_RED, POS2_BLUE = 0, 1, 2, 3
    for i in range(4):
        model.cmanager.setNewConstantIndex()
    
    # Constraints
    constraints = [
        # Position 1 cannot be both red and blue
        aml.Duple(aml.LCSegment([POS1_RED]), aml.LCSegment([POS1_BLUE]), False, 0, 1),
        
        # Position 2 cannot be both red and blue
        aml.Duple(aml.LCSegment([POS2_RED]), aml.LCSegment([POS2_BLUE]), False, 0, 1),
    ]
    
    # Train
    embedder.enforce([], constraints)
    
    print("✅ Learned: Color constraint satisfaction")
    print(f"Atoms created: {len(model.atomization)}")

if __name__ == "__main__":
    example_constraint_satisfaction()
```

## Example 10: Complete Minimal Example with Testing

A complete example that includes training and testing.

```python
import aml

def complete_minimal_example():
    """Complete example: train and test a simple rule"""
    
    print("=== Training ===")
    
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Constants
    A, B = 0, 1
    model.cmanager.setNewConstantIndex()  # A
    model.cmanager.setNewConstantIndex()  # B
    
    # Train: A → B
    training_rule = aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1)
    embedder.enforce([training_rule], [])
    
    print(f"✅ Trained: A → B")
    print(f"Atoms created: {len(model.atomization)}")
    
    print("\n=== Testing ===")
    
    # Test cases
    test_cases = [
        # Should work (what we taught)
        aml.Duple(aml.LCSegment([A]), aml.LCSegment([B]), True, 0, 1),
        
        # Should not work (reverse implication)
        aml.Duple(aml.LCSegment([B]), aml.LCSegment([A]), True, 0, 1),
    ]
    
    # Setup test space
    test_space = aml.termSpace()
    for duple in test_cases:
        duple.wL = test_space.add(duple.L)
        duple.wH = test_space.add(duple.R)
    
    constants = aml.CSegment([A, B])
    las = aml.calculateLowerAtomicSegment(model.atomization, constants, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    # Test
    result = embedder.test(test_cases)
    print(f"Test result: {result}")
    print(f"FPR: {embedder.vars.FPR:.3f}, FNR: {embedder.vars.FNR:.3f}")
    
    if embedder.vars.FPR < 0.5 and embedder.vars.FNR < 0.5:
        print("✅ Model learned successfully!")
    else:
        print("❌ Model needs more work")

if __name__ == "__main__":
    complete_minimal_example()
```

## Running All Examples

Here's a script to run all the toy examples:

```python
import aml

def run_all_toy_examples():
    """Run all toy examples in sequence"""
    
    examples = [
        ("Single Implication", example_single_implication),
        ("Simple Exclusion", example_simple_exclusion),
        ("AND Logic", example_and_logic),
        ("OR Logic", example_or_logic),
        ("Chain of Implications", example_chain),
        ("Simple Classification", example_simple_classifier),
        ("State Machine", example_state_machine),
        ("Micro Pattern Recognition", example_micro_pattern),
        ("Constraint Satisfaction", example_constraint_satisfaction),
        ("Complete Example", complete_minimal_example),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print('='*50)
        try:
            example_func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print(f"\n{'='*50}")
    print("All toy examples completed!")
    print('='*50)

if __name__ == "__main__":
    run_all_toy_examples()
```

## Key Takeaways

These toy examples demonstrate:

1. **Basic structure**: Model → Embedder → Constants → Rules → Training
2. **Two types of rules**: Positive (implications) and Negative (exclusions)
3. **Logical relationships**: AND, OR, chains, mutual exclusion
4. **Applications**: Classification, state machines, pattern recognition, constraints
5. **Testing**: How to evaluate if the model learned correctly

Each example is intentionally minimal to focus on one concept. Real applications combine these patterns into more complex systems.

## Next Steps

1. **Modify these examples**: Change the constants and rules
2. **Combine patterns**: Mix different logical relationships
3. **Add more complexity**: Use more constants and rules
4. **Try different embedders**: Compare sparse vs full crossing
5. **Build your own**: Create examples for your specific domain

These toy examples provide the building blocks for understanding AML. Once you're comfortable with these, you're ready to tackle the full examples in the `Examples/` folder!