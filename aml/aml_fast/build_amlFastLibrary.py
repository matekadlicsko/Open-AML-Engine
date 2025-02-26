# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from cffi import FFI
import sys

ffibuilder = FFI()

with open("build_amlFastLibrary_externalFunctions.h") as f:
    cdef_text = f.read()

with open("amlFast_bitarrays.h") as f:
    cdef_text += "\n"
    cdef_text += f.read()

ffibuilder.cdef(cdef_text)

ffibuilder.set_source(
    "amlCompiledLibrary",
    """
    #include "build_amlFastLibrary_externalFunctions.h"
    #include "amlFast_bitarrays.h"
    """,
    sources=[
        "amlFast_bitarrays.c",
        "aml_fast.c",
        "aml_tools.c",
        "cbar_buffer.c",
        "bitarrays.c",
        "tracehelper.c",
        "cbar.c",
    ],
    extra_compile_args=[
        "-Wall",
        "-Wextra",
        "-Wshadow",
        "-fopenmp",
        "-msse2",
        "-march=core-avx2",
        "-O3",
        "-g0",
    ],
    extra_link_args=[
        "-fopenmp",
    ],
)

ffibuilder.compile(verbose=True)
