# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

USE_BITARRAYS = True

if USE_BITARRAYS:
    from .aml_fast.amlFastBitarrays import bitarray
    amlset = bitarray
else:
    amlset = set

from .core import *
from .embedders import *
from .io import *
from .tools import *
from . import amldl
