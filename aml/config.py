# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

use_tracehelper = True

# ------------------------------------------------------------------------------
class Verbosity:
    """Levels for logging functions"""

    Debug = 10
    Info = 20
    Warn = 30
    Error = 40
    Crit = 50


# Default verbosity level for logging functions
verbosityLevel = Verbosity.Info

# ------------------------------------------------------------------------------
class compiledFunc:
    """Configure what functions are run in its precompiled C version"""

    calculateLowerAtomicSegments = True
    considerPositiveDuples = True
    crossAll = True
    freeTraceAll = True
    reduceIndicators = True
    selectAllUsefulIndicators = True
    simplifyFromConstants = True
    storeTracesOfConstants = True
    traceAll = True
    updateUnionModelWithSetOfPduples = True
