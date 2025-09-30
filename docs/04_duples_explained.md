# Understanding Duples

Duples are the heart of AML - they're how you teach the model logical relationships. Let's explore them with simple, concrete examples.

## What Are Duples?

A duple is a statement about two terms (sets of constants). There are two types:

1. **Positive Duples (Inclusions)**: "If Left, then Right" 
2. **Negative Duples (Exclusions)**: "Left and Right cannot both be true"

## Positive Duples: "If-Then" Rules

### Example 1: Simple Implication

```python
import aml

# Constants
RAIN = 0
WET_GROUND = 1

# Rule: "If it rains, then the ground gets wet"
rain_makes_wet = aml.Duple(
    aml.LCSegment([RAIN]),        # If rain
    aml.LCSegment([WET_GROUND]),  # Then wet ground
    True,  # Positive duple
    0, 1
)
```

### Example 2: Multiple Conditions

```python
# Constants
RAIN = 0
UMBRELLA = 1
STAY_DRY = 2

# Rule: "If it rains AND I have an umbrella, then I stay dry"
umbrella_keeps_dry = aml.Duple(
    aml.LCSegment([RAIN, UMBRELLA]),  # Rain AND umbrella
    aml.LCSegment([STAY_DRY]),        # Then stay dry
    True, 0, 1
)
```

### Example 3: Multiple Outcomes

```python
# Constants
STUDY = 0
GOOD_GRADE = 1
HAPPY = 2

# Rule: "If I study, then I get good grades AND feel happy"
study_benefits = aml.Duple(
    aml.LCSegment([STUDY]),              # If study
    aml.LCSegment([GOOD_GRADE, HAPPY]),  # Then good grade AND happy
    True, 0, 1
)
```

## Negative Duples: "Cannot Both Be True"

### Example 1: Contradictions

```python
# Constants
SUNNY = 0
RAINING = 1

# Rule: "Cannot be both sunny and raining"
weather_contradiction = aml.Duple(
    aml.LCSegment([SUNNY]),    # Sunny
    aml.LCSegment([RAINING]),  # Cannot coexist with raining
    False,  # Negative duple
    0, 1
)
```

### Example 2: Mutual Exclusion

```python
# Constants
LIGHT_ON = 0
LIGHT_OFF = 1

# Rule: "Light cannot be both on and off"
light_states = aml.Duple(
    aml.LCSegment([LIGHT_ON]),   # Light on
    aml.LCSegment([LIGHT_OFF]),  # Cannot be with light off
    False, 0, 1
)
```

### Example 3: Complex Exclusions

```python
# Constants
SLEEPING = 0
DRIVING = 1
SAFE = 2

# Rule: "If sleeping, then NOT (driving and safe)"
# This prevents the dangerous combination
sleep_driving_unsafe = aml.Duple(
    aml.LCSegment([SLEEPING]),        # If sleeping
    aml.LCSegment([DRIVING, SAFE]),   # Then NOT (driving AND safe)
    False, 0, 1
)
```

## Complete Working Example

Let's build a model that learns about traffic lights:

```python
import aml

def traffic_light_example():
    # Set up model
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Define constants
    RED_LIGHT = 0
    GREEN_LIGHT = 1
    YELLOW_LIGHT = 2
    STOP = 3
    GO = 4
    
    # Register constants
    for i in range(5):
        model.cmanager.setNewConstantIndex()
    
    # Define rules
    rules = [
        # Positive rules (implications)
        aml.Duple(
            aml.LCSegment([RED_LIGHT]), 
            aml.LCSegment([STOP]), 
            True, 0, 1
        ),  # Red → Stop
        
        aml.Duple(
            aml.LCSegment([GREEN_LIGHT]), 
            aml.LCSegment([GO]), 
            True, 0, 1
        ),  # Green → Go
        
        # Negative rules (exclusions)
        aml.Duple(
            aml.LCSegment([RED_LIGHT]), 
            aml.LCSegment([GREEN_LIGHT]), 
            False, 0, 1
        ),  # Can't be red AND green
        
        aml.Duple(
            aml.LCSegment([STOP]), 
            aml.LCSegment([GO]), 
            False, 0, 1
        ),  # Can't stop AND go
    ]
    
    # Train the model
    positive_rules = [r for r in rules if r.positive]
    negative_rules = [r for r in rules if not r.positive]
    
    embedder.enforce(positive_rules, negative_rules)
    
    print("Traffic light model trained!")
    print(f"Learned {len(model.atomization)} atoms")
    
    return model, embedder

if __name__ == "__main__":
    model, embedder = traffic_light_example()
```

## Common Patterns

### Pattern 1: Cause and Effect
```python
# If cause, then effect
cause_effect = aml.Duple(
    aml.LCSegment([CAUSE]), 
    aml.LCSegment([EFFECT]), 
    True, 0, 1
)
```

### Pattern 2: Prerequisites
```python
# Need A and B to achieve C
prerequisites = aml.Duple(
    aml.LCSegment([A, B]), 
    aml.LCSegment([C]), 
    True, 0, 1
)
```

### Pattern 3: Mutual Exclusion
```python
# A and B cannot both be true
mutual_exclusion = aml.Duple(
    aml.LCSegment([A]), 
    aml.LCSegment([B]), 
    False, 0, 1
)
```

### Pattern 4: Preventing Bad States
```python
# If dangerous condition, then NOT safe state
safety_rule = aml.Duple(
    aml.LCSegment([DANGEROUS_CONDITION]), 
    aml.LCSegment([SAFE_STATE]), 
    False, 0, 1
)
```

## Tips for Creating Good Duples

1. **Start simple**: Begin with basic if-then rules
2. **Be explicit**: Don't assume the model knows common sense
3. **Use negatives wisely**: Negative duples prevent unwanted combinations
4. **Think logically**: Each duple should represent a clear logical relationship
5. **Test incrementally**: Add rules one at a time to see their effects

## Duple Parameters Explained

```python
aml.Duple(left_term, right_term, positive, generation, region)
```

- **left_term**: The condition (if part)
- **right_term**: The consequence (then part) 
- **positive**: True for implications, False for exclusions
- **generation**: Used for tracking learning iterations (usually 0)
- **region**: Groups related duples together (usually 1)

## Next Steps

Now that you understand duples, let's apply them to [Simple Pattern Recognition](05_pattern_recognition.md) to see how they work in practice!