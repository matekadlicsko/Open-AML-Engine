# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import pickle
import os
import subprocess
import numpy as np
from pathlib import Path
from . import core as sc
from . import amlset
from . import config
from .aml_fast import aml_fast as af
from .aml_fast.amlFastBitarrays import bitarray

# -----------------------------------------------------------------------------
# Logging


def log(level, *msg, **kwargs):
    if level >= config.verbosityLevel:
        print(*msg, **kwargs)


def logDebug(*msg, **kwargs):
    log(config.Verbosity.Debug, *msg, **kwargs)


def logInfo(*msg, **kwargs):
    log(config.Verbosity.Info, *msg, **kwargs)


def logWarn(*msg, **kwargs):
    log(config.Verbosity.Warn, *msg, **kwargs)


def logError(*msg, **kwargs):
    log(config.Verbosity.Error, *msg, **kwargs)


def logCrit(*msg, **kwargs):
    log(config.Verbosity.Crit, *msg, **kwargs)


# -----------------------------------------------------------------------------
# Saving


def saveAtomizationOnFile(atomization, cmanager, filePathAndName):
    """
    Save 'atomization' and 'cmanager' to 'filePathAndName'.aml.
    It only works if amlset is an alias for set. If using bitarrays,
    use saveAtomizationOnFileUsingBitarrays instead.
    """
    print("Saving in file as", filePathAndName)
    try:
        git_call = subprocess.run(
            ["git", "log", "-1", '--pretty=format:"%H"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        git_hash = git_call.stdout
    except subprocess.CalledProcessError:
        git_hash = "UNKNOWN HASH"

    with open(filePathAndName + ".atemp", "wb") as output:
        # Pickle version using git hash
        pickle.dump(git_hash, output, pickle.HIGHEST_PROTOCOL)
        # Pickle constant manager
        cmanager.embeddingConstants = set(cmanager.embeddingConstants)
        pickle.dump(cmanager, output, pickle.HIGHEST_PROTOCOL)
        cmanager.embeddingConstants = amlset(cmanager.embeddingConstants)
        for at in atomization:
            pickle.dump(at, output, pickle.HIGHEST_PROTOCOL)

    os.rename(filePathAndName + ".atemp", filePathAndName + ".aml")


def loadAtomizationFromFile(filePathAndName):
    """
    Load 'cmanager' and 'atomization' from 'filePathAndName'.aml.
    It only works if amlset is an alias for set. If using bitarrays,
    use loadAtomizationFromFileUsingBitarrays instead.
    """
    print("Loading file", filePathAndName)
    try:
        with open(filePathAndName + ".aml", "rb") as inputfile:
            git_hash = pickle.load(inputfile)
            if isinstance(git_hash, str):
                cmanager = pickle.load(inputfile)
            else:
                cmanager = git_hash
            cmanager.embeddingConstants = amlset(cmanager.embeddingConstants)
            loadedAtomization = []
            while True:
                try:
                    at = pickle.load(inputfile)
                    at.unionUpdateEntrance = -1
                    loadedAtomization.append(at)

                except EOFError:
                    break
    except ModuleNotFoundError:
        COLOR_RED = "\033[1;31m"
        COLOR_RESET = "\033[0m"
        print(f"{COLOR_RED}File saved with version: {git_hash}{COLOR_RESET}")
    return cmanager, loadedAtomization


def saveAtomizationOnFileUsingBitarrays(atomization, cmanager, filePathAndName):  # fmt:skip
    """
    Save 'atomization' and 'cmanager' to 'filePathAndName'.aml.
    It only works if amlset is an alias for bitarray. If using bitarrays,
    use saveAtomizationOnFile instead.
    """
    try:
        git_call = subprocess.run(
            ["git", "log", "-1", '--pretty=format:"%H"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        git_hash = git_call.stdout
    except subprocess.CalledProcessError:
        git_hash = "UNKNOWN HASH"

    # Set up paths and extensions
    filename = Path(filePathAndName + ".aml")
    filename_temp = Path(filePathAndName + ".atemp")
    print("Saving in file as", filename)

    # Create buffer with ucs
    segments = [bitarray(at.ucs) for at in atomization]
    handles = [s._segment_handle[0] for s in segments]
    length_buffer = af.caml.segment_getAllSegmentsBufferLength(
        handles, len(atomization)
    )
    buffer = np.empty([length_buffer], dtype=np.byte)
    buffer_ptr = af.ffi.cast("char *", buffer.ctypes.data)
    af.caml.segment_getAllSegmentsBuffer(
        buffer_ptr,
        handles,
        len(atomization),
    )

    with open(filename_temp, "wb") as output:
        # Pickle version using git hash
        pickle.dump(git_hash, output, pickle.HIGHEST_PROTOCOL)
        # Pickle constant manager
        cmanager.embeddingConstants = set(cmanager.embeddingConstants)
        pickle.dump(cmanager, output, pickle.HIGHEST_PROTOCOL)
        cmanager.embeddingConstants = amlset(cmanager.embeddingConstants)
        pickle.dump(len(atomization), output, pickle.HIGHEST_PROTOCOL)
        gens = [at.gen for at in atomization]
        Gs = [at.G for at in atomization]
        pickle.dump(gens, output, pickle.HIGHEST_PROTOCOL)
        pickle.dump(Gs, output, pickle.HIGHEST_PROTOCOL)
        # Pickle ucs buffer
        pickle.dump(buffer, output, pickle.HIGHEST_PROTOCOL)

    filename_temp.rename(filename)


def loadAtomizationFromFileUsingBitarrays(filePathAndName):
    """
    Load 'cmanager' and 'atomization' from 'filePathAndName'.aml.
    It only works if amlset is an alias for bitarray. If using sets,
    use loadAtomizationFromFile instead.
    """
    try:
        filename = Path(filePathAndName + ".aml")
        print("Loading file", filename)
        # Read file
        with open(filename, "rb") as inputfile:
            git_hash = pickle.load(inputfile)
            if isinstance(git_hash, str):
                cmanager = pickle.load(inputfile)
            else:
                cmanager = git_hash
            cmanager.embeddingConstants = amlset(cmanager.embeddingConstants)
            atomization_len = pickle.load(inputfile)
            atomization = []
            gens = pickle.load(inputfile)
            Gs = pickle.load(inputfile)
            buffer = pickle.load(inputfile)

        # Read data into bitarrays
        segments = [bitarray() for _ in range(atomization_len)]
        handles = [b._segment_handle for b in segments]
        buffer_ptr = af.ffi.cast("char *", buffer.ctypes.data)
        af.caml.segment_buildFromBuffer(
            buffer_ptr,
            handles,
            bitarray.gsm,
        )

        # Assign bitarrays to atoms ucs
        for k in range(atomization_len):
            at = sc.Atom(0, 0, set(segments[k]))
            at.gen = gens[k]
            at.G = Gs[k]
            atomization.append(at)
    except ModuleNotFoundError:
        COLOR_RED = "\033[1;31m"
        COLOR_RESET = "\033[0m"
        print(f"{COLOR_RED}File saved with version: {git_hash}{COLOR_RESET}")

    return cmanager, atomization
