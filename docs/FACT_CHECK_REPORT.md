# AML Documentation Fact-Check Report

This report identifies factual inaccuracies and issues in the AML documentation compared to the actual research paper "Algebraic Machine Learning: Learning as computing an algebraic decomposition of a task" (arXiv:2502.19944v1).

## Executive Summary

The documentation contains several significant errors and misconceptions about AML terminology and concepts. The most critical issues involve:
1. **Incorrect use of "duples" terminology** - The paper uses the symbol ≤ (less than or equal) and ≰ (not less than or equal), NOT "positive/negative duples"
2. **Misrepresentation of what duples express** - The paper describes inequalities in semilattices, not "if-then rules" and "exclusions"
3. **Missing theoretical foundation** - Documentation omits the semilattice structure that is fundamental to AML
4. **Terminology confusion** - The docs use informal terms that don't match the paper's mathematical precision

## Critical Issues

### 1. **MAJOR ERROR: "Positive" and "Negative" Duples Terminology**

**Documentation Claims:**
- Files: `02_core_concepts.md`, `04_duples_explained.md`, `09_quick_reference.md`
- States there are "Positive Duples (Inclusions)" and "Negative Duples (Exclusions)"
- Claims positive duples mean "If Left, then Right"
- Claims negative duples mean "Left and Right cannot both be true"

**Actual Paper:**
- The paper uses mathematical notation: `L ≤ R` (positive/inclusion axiom) and `L ≰ R` (negative/exclusion axiom)
- These represent **semilattice inequalities**, not simple if-then rules
- The paper never uses the informal terms "positive duple" or "negative duple" in the way the docs present them
- The correct interpretation is about **ordering in a semilattice structure**, not boolean logic

**Evidence from Paper:**
```
"positive and negative task duples" (referring to ≤ and ≰ relationships)
"digit_i ≤ image_k" (positive task duple)
"digit_{j≠i} ≰ image_k" (negative task duple)
```

### 2. **MAJOR ERROR: Oversimplification of What Duples Represent**

**Documentation Claims:**
- "Duples are statements about two terms"
- "Positive Duples: 'If-Then' Rules" 
- "Negative Duples: 'Cannot Both Be True'"

**Actual Paper:**
- Duples represent **ordering relationships in an atomized semilattice**
- `L ≤ R` means "L is below or equal to R in the semilattice ordering"
- This is NOT the same as material implication in logic
- The ⊙ operator is **idempotent summation** (join in semilattice), not AND

**Impact:** Users will fundamentally misunderstand how AML works.

### 3. **MISSING CRITICAL CONCEPT: Atomized Semilattices**

**Documentation Issues:**
- The term "semilattice" appears nowhere in the documentation
- "Atomization" is mentioned but not properly explained
- The fundamental algebraic structure underlying AML is completely omitted

**Actual Paper:**
- Entire Supplementary Section 1 is "Atomized Semilattices"
- The paper states: "Statistics and Optimization are foundational to modern Machine Learning. Here, we propose an alternative foundation based on Abstract Algebra"
- The freest atomized model is central to understanding how learning works

**Impact:** Users miss the theoretical foundation that distinguishes AML from other ML approaches.

### 4. **TERMINOLOGY ERROR: "Terms" vs "Segments"**

**Documentation Claims:**
- Uses "terms" to refer to sets of constants
- "Terms are sets of constants that represent concepts"

**Actual Paper:**
- Uses "segment" (specifically "LCSegment" = Lower Constant Segment)
- Terms have a specific mathematical meaning in the semilattice theory
- The paper uses "term" in phrases like "pinning terms" and "term space" with precise mathematical definitions

**Correction Needed:**
- Should use "segment" or "constant segment" instead of "term" when referring to sets of constants
- Or clearly define that "term" in the documentation refers to "lower constant segment"

### 5. **INCOMPLETE: Sparse Crossing vs Full Crossing**

**Documentation Claims:**
- `06_embedders.md`: "Sparse Crossing Embedder: Best for most real-world problems"
- "Full Crossing Embedder: Best for small problems, when you need exact solutions"

**Actual Paper:**
- Sparse Crossing is a sophisticated algorithm using **trace preservation** to select atoms
- The paper states: "atoms are selected based on an invariance condition: the preservation of a quantity we call the trace"
- Uses "pinning terms" to accelerate discovery of non-redundant atoms
- This is far more complex than "approximates the optimal solution"

**Missing Information:**
- Trace invariance
- Pinning terms
- The relationship between sparse crossing and the freest model
- Why sparse crossing works for generalization

### 6. **MISLEADING: "Atoms" Explanation**

**Documentation Claims:**
- `02_core_concepts.md`: "Atoms are the learned building blocks... They represent 'atomic' concepts that cannot be broken down further"

**Actual Paper:**
- Atoms are elements of an atomized semilattice with specific mathematical properties
- "Non-redundant atoms" are the true building blocks (atoms that cannot be expressed as unions of other atoms)
- Redundant atoms ARE unions of non-redundant atoms
- The distinction between redundant and non-redundant is crucial

**Impact:** Users won't understand the model structure.

### 7. **INCORRECT EXAMPLE: Traffic Light Model**

**File:** `04_duples_explained.md`

**Documentation Code:**
```python
# Rule: Red → Stop
aml.Duple(aml.LCSegment([RED_LIGHT]), aml.LCSegment([STOP]), True, 0, 1)

# Rule: Can't be red AND green
aml.Duple(aml.LCSegment([RED_LIGHT]), aml.LCSegment([GREEN_LIGHT]), False, 0, 1)
```

**Issues:**
- The comment "Red → Stop" is misleading - this is not material implication
- The comment "Can't be red AND green" misrepresents what the negative duple means
- In semilattice terms, this says RED_LIGHT ≰ GREEN_LIGHT, meaning RED_LIGHT is not below GREEN_LIGHT in the ordering

**Correct Interpretation:**
- First duple: RED_LIGHT ≤ STOP (in any model containing RED_LIGHT, STOP must also be present at or above it)
- Second duple: RED_LIGHT ≰ GREEN_LIGHT (RED_LIGHT cannot be ordered below GREEN_LIGHT)

### 8. **MISSING: The Embedding Strategy**

**Documentation Issues:**
- Doesn't explain what "embedding" means in AML context
- Examples show direct constant usage without explaining the embedding theory

**Actual Paper:**
- Entire section on "Semantic embeddings" 
- For MNIST: Uses 2×28×28 constants (black/white for each pixel)
- For grayscale: Uses ascending and descending chains of constants
- The embedding strategy is crucial for how problems are represented

**Impact:** Users won't know how to properly encode their problems.

### 9. **INCONSISTENT: Testing Methodology**

**File:** `07_testing.md`

**Documentation Shows:**
- Complex test space setup
- Lower atomic segments calculation
- But doesn't explain WHY these steps are needed

**Actual Paper:**
- Testing involves checking if duples are satisfied in the learned model
- Uses Equation 2: digit_i assigned when "atoms in the lower segment of constant digit_i are a subset of atoms in lower segment of test image"
- This mathematical foundation is missing from docs

### 10. **MISLEADING ANALOGY: "Learning to Drive"**

**File:** `02_core_concepts.md`

The analogy presents AML as learning simple rules like "red light means stop" but this oversimplifies the semilattice mathematics and could mislead users about what AML actually does.

## Minor Issues

### 11. Constants Registration
**Issue:** Documentation doesn't explain that constants need to be registered with `cmanager` BEFORE use, leading to potential runtime errors.

### 12. Missing Parameters
**File:** `06_embedders.md`
- Lists parameters but doesn't explain their mathematical basis
- Example: `useReduceIndicators` relates to trace preservation but this isn't explained

### 13. Error Metrics
**File:** `07_testing.md`
- FPR and FNR are mentioned but their specific meaning in the AML context isn't clear
- The paper uses these for measuring how well duples are satisfied

## Recommendations

### Immediate Corrections Needed:

1. **Replace "positive/negative duple" terminology** with proper mathematical notation (≤ and ≰)
2. **Add semilattice theory section** to explain the algebraic foundation
3. **Correct all "if-then" interpretations** to properly reflect semilattice ordering
4. **Add embedding theory section** explaining how to represent problems
5. **Explain atoms vs non-redundant atoms** properly
6. **Add trace preservation concept** to sparse crossing explanation
7. **Fix all code examples** to have mathematically correct comments

### Documentation That Needs Major Revision:

- `02_core_concepts.md` - Completely rewrite to include semilattice foundations
- `04_duples_explained.md` - Remove misleading if-then interpretations
- `06_embedders.md` - Add proper explanation of sparse crossing algorithm
- All example files - Correct comments to reflect semilattice semantics

### Missing Documentation:

- Atomized semilattice theory
- Embedding strategies for different problem types
- Trace preservation and pinning terms
- Relationship between freest model and learned models
- Non-redundant vs redundant atoms

## Conclusion

The documentation was clearly written by someone who understood the practical API but not the underlying mathematical theory from the paper. While the code examples may work correctly, the conceptual explanations are often wrong or misleading. This will cause users to:

1. Misunderstand the theoretical foundations of AML
2. Struggle to properly embed their problems
3. Miss the key advantages of AML over other ML approaches
4. Not understand why certain design decisions were made

**Priority:** HIGH - The current documentation could lead to incorrect usage and misunderstanding of when/how to apply AML.

---

*Report generated by comparing documentation files against arXiv paper 2502.19944v1*
*Date: 2025-09-30*