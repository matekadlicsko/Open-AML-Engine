# Installation Guide

This guide walks you through setting up the Open-AML-Engine on your system.

## Prerequisites

- Python 3.7 or higher
- A C compiler (gcc on Linux/Mac, Visual Studio on Windows)
- Git (to clone the repository)

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/Open-AML-Engine.git
cd Open-AML-Engine
```

## Step 2: Install Python Dependencies

```bash
pip install cffi numpy
```

Optional dependencies for examples:
```bash
pip install networkx matplotlib  # For graph examples
```

## Step 3: Compile C Extensions

The AML engine includes optimized C code for performance. Compile it:

```bash
cd aml/aml_fast
python build_amlFastLibrary.py
cd ../..
```

**Troubleshooting**: If you get "Illegal instruction (core dumped)" errors later, edit `build_amlFastLibrary.py` and remove these lines:
```python
"-msse2",
"-march=core-avx2",
```

## Step 4: Install the AML Package

From the root directory:

```bash
python -m pip install -e .
```

The `-e` flag installs in "editable" mode, so changes to the source code are immediately available.

## Step 5: Verify Installation

Test that everything works:

```python
import aml
print("AML installed successfully!")

# Create a simple model to test
model = aml.Model()
print(f"Model created with {len(model.atomization)} atoms")
```

## Optional: MNIST Dataset

If you want to run the MNIST example (`example04_MNIST.py`), download the MNIST dataset:

1. Create the directory: `mkdir -p Examples/mnist_datasets`
2. Download from [Yann LeCun's website](http://yann.lecun.com/exdb/mnist/) or [Hugging Face](https://huggingface.co/datasets/ylecun/mnist)
3. Place these files in `Examples/mnist_datasets/`:
   - `t10k-images-idx3-ubyte`
   - `t10k-labels-idx1-ubyte`
   - `train-images-idx3-ubyte`
   - `train-labels-idx1-ubyte`

## Next Steps

Now that AML is installed, continue to [Core Concepts](02_core_concepts.md) to understand the fundamental ideas behind Algebraic Machine Learning.