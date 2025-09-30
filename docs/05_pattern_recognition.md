# Simple Pattern Recognition

Let's build a toy pattern recognition system that learns to identify simple shapes in a 3x3 grid. This example shows how AML can learn visual patterns.

## The Problem

We have a 3x3 grid where each cell can be either:
- **Black** (1) - represented by constants 0-8
- **White** (0) - represented by constants 9-17

We want to teach the model to recognize a "vertical line" pattern.

## Visual Representation

```
Grid positions:    Black constants:    White constants:
[0] [1] [2]        [0] [1] [2]         [9]  [10] [11]
[3] [4] [5]   →    [3] [4] [5]    OR   [12] [13] [14]
[6] [7] [8]        [6] [7] [8]         [15] [16] [17]
```

A vertical line in the middle column would be: positions 1, 4, 7 are black.

## Step 1: Set Up the Model

```python
import aml
import random

def create_pattern_model():
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    
    # Configure for better pattern learning
    embedder.params.storePositives = True
    embedder.params.useReduceIndicators = True
    
    return model, embedder

model, embedder = create_pattern_model()
```

## Step 2: Define Constants

```python
# Constants for a 3x3 grid
GRID_SIZE = 3
TOTAL_CELLS = GRID_SIZE * GRID_SIZE

# Constants 0-8: black cells
# Constants 9-17: white cells
BLACK_OFFSET = 0
WHITE_OFFSET = TOTAL_CELLS

# Register all constants with the model
for i in range(2 * TOTAL_CELLS):
    model.cmanager.setNewConstantIndex()

# Add a constant for the "vertical line" concept
VERTICAL_LINE = model.cmanager.setNewConstantIndexWithName("VERTICAL_LINE")

print(f"Defined {2 * TOTAL_CELLS + 1} constants")
```

## Step 3: Helper Functions

```python
def position_to_constants(grid):
    """Convert a 3x3 grid to a set of constants."""
    constants = set()
    for i in range(TOTAL_CELLS):
        if grid[i] == 1:  # Black cell
            constants.add(BLACK_OFFSET + i)
        else:  # White cell
            constants.add(WHITE_OFFSET + i)
    return constants

def create_vertical_line(column):
    """Create a vertical line in the specified column (0, 1, or 2)."""
    grid = [0] * TOTAL_CELLS  # Start with all white
    for row in range(GRID_SIZE):
        pos = row * GRID_SIZE + column
        grid[pos] = 1  # Make it black
    return grid

def print_grid(grid):
    """Print a visual representation of the grid."""
    for row in range(GRID_SIZE):
        line = ""
        for col in range(GRID_SIZE):
            pos = row * GRID_SIZE + col
            line += "█" if grid[pos] == 1 else "·"
        print(line)
    print()
```

## Step 4: Create Training Data

```python
def create_training_data():
    positive_duples = []
    negative_duples = []
    
    # Positive examples: vertical lines
    for column in range(GRID_SIZE):
        grid = create_vertical_line(column)
        constants = position_to_constants(grid)
        
        print(f"Positive example - column {column}:")
        print_grid(grid)
        
        # Rule: "If this pattern, then it's a vertical line"
        positive_duple = aml.Duple(
            aml.LCSegment([VERTICAL_LINE]),
            aml.LCSegment(constants),
            True, 0, 1
        )
        positive_duples.append(positive_duple)
    
    # Negative examples: random patterns that are NOT vertical lines
    for _ in range(5):
        # Create random grid
        grid = [random.randint(0, 1) for _ in range(TOTAL_CELLS)]
        
        # Make sure it's not accidentally a vertical line
        is_vertical = any(
            all(grid[row * GRID_SIZE + col] == 1 for row in range(GRID_SIZE))
            for col in range(GRID_SIZE)
        )
        
        if not is_vertical:
            constants = position_to_constants(grid)
            
            print("Negative example:")
            print_grid(grid)
            
            # Rule: "This pattern should NOT be a vertical line"
            negative_duple = aml.Duple(
                aml.LCSegment([VERTICAL_LINE]),
                aml.LCSegment(constants),
                False, 0, 1
            )
            negative_duples.append(negative_duple)
    
    return positive_duples, negative_duples

positive_duples, negative_duples = create_training_data()
```

## Step 5: Train the Model

```python
print("Training the model...")
embedder.enforce(positive_duples, negative_duples)
print(f"Training complete! Model has {len(model.atomization)} atoms")
```

## Step 6: Test the Model

```python
def test_pattern(grid, description):
    """Test if the model recognizes a pattern as a vertical line."""
    constants = position_to_constants(grid)
    
    # Create test duple
    test_duple = aml.Duple(
        aml.LCSegment([VERTICAL_LINE]),
        aml.LCSegment(constants),
        True, 0, 1
    )
    
    # Prepare for testing
    test_space = aml.termSpace()
    test_duple.wL = test_space.add(test_duple.L)
    test_duple.wH = test_space.add(test_duple.R)
    
    # Calculate lower atomic segments
    all_constants = aml.CSegment(list(range(2 * TOTAL_CELLS + 1)))
    las = aml.calculateLowerAtomicSegment(model.atomization, all_constants, True)
    test_space.calculateLowerAtomicSegments(model.atomization, las)
    
    # Test
    result = embedder.test([test_duple])
    
    print(f"{description}:")
    print_grid(grid)
    print(f"Test result: {result}")
    print()

# Test with various patterns
print("Testing the trained model:")

# Test 1: Vertical line (should be recognized)
test_pattern(create_vertical_line(1), "Middle vertical line")

# Test 2: Horizontal line (should NOT be recognized)
horizontal_line = [0, 0, 0, 1, 1, 1, 0, 0, 0]
test_pattern(horizontal_line, "Horizontal line")

# Test 3: Diagonal (should NOT be recognized)
diagonal = [1, 0, 0, 0, 1, 0, 0, 0, 1]
test_pattern(diagonal, "Diagonal line")

# Test 4: Random pattern (should NOT be recognized)
random_pattern = [1, 0, 1, 0, 1, 0, 1, 0, 1]
test_pattern(random_pattern, "Random pattern")
```

## Complete Example

Here's the full working code:

```python
import aml
import random

def simple_pattern_recognition():
    # Setup
    model = aml.Model()
    embedder = aml.sparse_crossing_embedder(model)
    embedder.params.storePositives = True
    
    # Constants
    GRID_SIZE = 3
    TOTAL_CELLS = 9
    
    # Register constants (0-8: black, 9-17: white)
    for i in range(18):
        model.cmanager.setNewConstantIndex()
    
    VERTICAL_LINE = model.cmanager.setNewConstantIndexWithName("VERTICAL_LINE")
    
    def position_to_constants(grid):
        constants = set()
        for i in range(TOTAL_CELLS):
            if grid[i] == 1:
                constants.add(i)  # Black
            else:
                constants.add(i + TOTAL_CELLS)  # White
        return constants
    
    def create_vertical_line(column):
        grid = [0] * TOTAL_CELLS
        for row in range(GRID_SIZE):
            pos = row * GRID_SIZE + column
            grid[pos] = 1
        return grid
    
    # Training data
    positive_duples = []
    negative_duples = []
    
    # Positive: all three vertical lines
    for col in range(GRID_SIZE):
        grid = create_vertical_line(col)
        constants = position_to_constants(grid)
        positive_duples.append(aml.Duple(
            aml.LCSegment([VERTICAL_LINE]),
            aml.LCSegment(constants),
            True, 0, 1
        ))
    
    # Negative: some non-vertical patterns
    non_vertical_patterns = [
        [1, 1, 1, 0, 0, 0, 0, 0, 0],  # Horizontal
        [1, 0, 0, 0, 1, 0, 0, 0, 1],  # Diagonal
        [1, 0, 1, 0, 1, 0, 1, 0, 1],  # Checkerboard
    ]
    
    for grid in non_vertical_patterns:
        constants = position_to_constants(grid)
        negative_duples.append(aml.Duple(
            aml.LCSegment([VERTICAL_LINE]),
            aml.LCSegment(constants),
            False, 0, 1
        ))
    
    # Train
    embedder.enforce(positive_duples, negative_duples)
    
    print(f"Pattern recognition model trained!")
    print(f"Atoms created: {len(model.atomization)}")
    
    return model, embedder

if __name__ == "__main__":
    model, embedder = simple_pattern_recognition()
```

## What the Model Learned

The model learned to:
1. **Recognize vertical lines**: Patterns where an entire column is black
2. **Reject other patterns**: Horizontal lines, diagonals, random patterns
3. **Generalize**: It can recognize vertical lines in any of the three columns

## Key Insights

1. **Positive duples** teach what the pattern IS
2. **Negative duples** teach what the pattern IS NOT
3. **The model creates atoms** that capture the essential features of vertical lines
4. **Testing shows** how well the model learned the concept

## Next Steps

This example showed basic pattern recognition. Next, let's learn about [Working with Embedders](06_embedders.md) to understand how to choose and configure the learning algorithms!