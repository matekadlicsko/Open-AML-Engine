# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import sys
import os
import random

import aml

# --------------------------------------------------------------------
# Configuration

# Available size in embedding: 4, 5, 6, 9
gridDimension = 6
# Target number of different, valid, complete boards
fullBoard_target = 200
# Maximum number of iterations when using sparse crossing
maxAttempts = 1000

# True: Obtain the freest model via the full crossing algorithm
#   It can be used for gridDimension 4
#   It becomes intractable for larger board sizes
# False: Use the sparse crossing algorithm.
computeFullCrossing = False

# Save full crossing
saveAtomization = False

# Report
# Print duples during initialization
displayDuplesAtInitialization = False

# Random seed for reproducibility
randseed = 123456789

aml.config.verbosityLevel = aml.config.Verbosity.Warn

# --------------------------------------------------------------------


def ixwn(digit, row, col, gridDimension):
    """
    Transform coordinates to index
    """

    return digit + row * gridDimension + col * gridDimension**2


def printDuples(exampleSet, counterexampleSet, reversedNameDictionary):
    for prel in exampleSet:
        print(
            f"{aml.interpretTerm(prel.L, reversedNameDictionary)}"
            f"<"
            f"{aml.interpretTerm(prel.R, reversedNameDictionary)}"
        )
    for nrel in counterexampleSet:
        print(
            f"{aml.interpretTerm(nrel.L, reversedNameDictionary)}"
            f"!<"
            f"{aml.interpretTerm(nrel.R, reversedNameDictionary)}"
        )


def printGrid(atomization, cmanager, embedding, gridDimension):
    """
    Compute board from an atomization and print to stdout.
    """

    N = [{n} for n in embedding["NConstants"]]
    G = set(embedding["GConstants"])
    boardStr = ""
    for x in range(0, gridDimension):
        row = ""
        for y in range(0, gridDimension):
            nval = "?"
            hasN = False
            for n in range(0, gridDimension):
                if aml.lowerOrEqual(aml.LCSegment(N[ixwn(n, x, y, gridDimension)]), aml.LCSegment(G), atomization):  # fmt:skip
                    if hasN:
                        nval = "!"
                    else:
                        hasN = True
                        nval = str(n)
            row += nval
        boardStr += row + f"{os.linesep}"
    if gridDimension == 4:
        ret = f"+--+--+{os.linesep}"
        ret += f"|{boardStr[0:2]}|{boardStr[2:4]}|{boardStr[4]}"
        ret += f"|{boardStr[5:7]}|{boardStr[7:9]}|{boardStr[9]}"
        ret += f"+--+--+{os.linesep}"
        ret += f"|{boardStr[10:12]}|{boardStr[12:14]}|{boardStr[14]}"
        ret += f"|{boardStr[15:17]}|{boardStr[17:19]}|{boardStr[19]}"
        ret += f"+--+--+"
    elif gridDimension == 5:
        b = boardStr
        ret = f"-----------{os.linesep}"
        ret += f"|{b[ 0]} {b[ 1]}|{b[ 2]} {b[ 3]} {b[ 4]}|{b[ 5]}"
        ret += f"|   ·-·   |{os.linesep}"
        ret += f"|{b[ 6]} {b[ 7]}|{b[ 8]}|{b[ 9]} {b[10]}|{b[11]}"
        ret += f"| ·-· ·-·-|{os.linesep}"
        ret += f"|{b[12]}|{b[13]} {b[14]} {b[15]}|{b[16]}|{b[17]}"
        ret += f"|-·-· ·-· |{os.linesep}"
        ret += f"|{b[18]} {b[19]}|{b[20]}|{b[21]} {b[22]}|{b[23]}"
        ret += f"|   ·-·   |{os.linesep}"
        ret += f"|{b[24]} {b[25]} {b[26]}|{b[27]} {b[28]}|{b[29]}"
        ret += f"-----------{os.linesep}"
    elif gridDimension == 6:
        ret = f"+---+---+{os.linesep}"
        ret += f"|{boardStr[0:3]}|{boardStr[3:6]}|{boardStr[6]}"
        ret += f"|{boardStr[7:10]}|{boardStr[10:13]}|{boardStr[13]}"
        ret += f"+---+---+{os.linesep}"
        ret += f"|{boardStr[14:17]}|{boardStr[17:20]}|{boardStr[20]}"
        ret += f"|{boardStr[21:24]}|{boardStr[24:27]}|{boardStr[27]}"
        ret += f"+---+---+{os.linesep}"
        ret += f"|{boardStr[28:31]}|{boardStr[31:34]}|{boardStr[34]}"
        ret += f"|{boardStr[35:38]}|{boardStr[38:41]}|{boardStr[41]}"
        ret += f"+---+---+{os.linesep}"
    elif gridDimension == 9:
        ret = f"+---+---+---+{os.linesep}"
        ret += f"|{boardStr[0:3]}|{boardStr[3:6]}|{boardStr[6:9]}|{boardStr[9]}"
        ret += f"|{boardStr[10:13]}|{boardStr[13:16]}|{boardStr[16:19]}|{boardStr[19]}"
        ret += f"|{boardStr[20:23]}|{boardStr[23:26]}|{boardStr[26:29]}|{boardStr[29]}"
        ret += f"+---+---+---+{os.linesep}"
        ret += f"|{boardStr[30:33]}|{boardStr[33:36]}|{boardStr[36:39]}|{boardStr[39]}"
        ret += f"|{boardStr[40:43]}|{boardStr[43:46]}|{boardStr[46:49]}|{boardStr[49]}"
        ret += f"|{boardStr[50:53]}|{boardStr[53:56]}|{boardStr[56:59]}|{boardStr[59]}"
        ret += f"+---+---+---+{os.linesep}"
        ret += f"|{boardStr[60:63]}|{boardStr[63:66]}|{boardStr[66:69]}|{boardStr[69]}"
        ret += f"|{boardStr[70:73]}|{boardStr[73:76]}|{boardStr[76:79]}|{boardStr[79]}"
        ret += f"|{boardStr[80:83]}|{boardStr[83:86]}|{boardStr[86:89]}|{boardStr[89]}"
        ret += f"+---+---+---+{os.linesep}"
    print(ret)


def checkFullBoard(atomization, cmanager, embedding, gridDimension):
    """
    Checks if the model (given by atomization) describe a complete
    sudoku board and returns a unique identifier for the state of the board.

    Return:
    isFullBoard (bool) : True if the atomization models a full board.
    boardKey    (str)  : Uniquely describe the board.
    """

    N = [{n} for n in embedding["NConstants"]]
    G = set(embedding["GConstants"])
    isFullBoard = True
    boardKey = ""
    for x in range(0, gridDimension):
        for y in range(0, gridDimension):
            isValid = False
            hasN = False
            for n in range(0, gridDimension):
                if aml.lowerOrEqual(
                    aml.LCSegment(N[ixwn(n, x, y, gridDimension)]),
                    aml.LCSegment(G),
                    atomization,
                ):
                    boardKey += f"({x},{y}){n}|"
                    if hasN:
                        isValid = False
                    else:
                        hasN = True
                        isValid = True
            if not isValid:
                isFullBoard = False
    return isFullBoard, boardKey


def describeCurrentBoard(model, embedding, gridDimension):
    """
    Obtain the content of the board in the given model.

    Return:
    Npresent     (List[constants]) : for the given model, constants for numbers that are
                                     present in the board.
    Wpresent     (List[constants]) : for the given model, constants for the absence of numbers
                                     that are present in the board.
    undetermined (List[constants]) : for the given model, cells that are not filled up.

    """

    N = [{n} for n in embedding["NConstants"]]
    W = [{w} for w in embedding["WConstants"]]
    G = set(embedding["GConstants"])
    Npresent = set()
    Wpresent = set()
    undetermined = []
    for x in range(0, gridDimension):
        for y in range(0, gridDimension):
            cellFilled = False
            for n in range(0, gridDimension):
                # Digit n at (x,y) is in the lower segment of G (present in the board).
                if aml.lowerOrEqual(aml.LCSegment(N[ixwn(n, x, y, gridDimension)]), aml.LCSegment(G), model.atomization):  # fmt:skip
                    Npresent |= N[ixwn(n, x, y, gridDimension)]
                    cellFilled = True
                # Non-digit n at (x,y)  is in the lower segment of G  (present in the board).
                if aml.lowerOrEqual(aml.LCSegment(W[ixwn(n, x, y, gridDimension)]), aml.LCSegment(G), model.atomization):  # fmt:skip
                    Wpresent |= W[ixwn(n, x, y, gridDimension)]
            if not cellFilled:
                # Empty cells
                undetermined.append([x, y])

    return Npresent, Wpresent, undetermined


def describeBoardAndExtensions(model, embedding, gridDimension):
    """
    Uses the model to obtain the current board configuration and
    returns a list of duples that makes more likely for the next
    batch to produce an extension of it.

    """

    N = [{n} for n in embedding["NConstants"]]
    W = [{w} for w in embedding["WConstants"]]
    NCMP = embedding["CMPConstants"]
    G = set(embedding["GConstants"])
    ret = []
    Npresent, Wpresent, undetermined = describeCurrentBoard(
        model, embedding, gridDimension
    )
    if len(Npresent) + len(Wpresent) > 0:
        # Construct the term for the current board configuration
        term = embedding["GConstants"] | Npresent | Wpresent

        # A well-formed board should not have any digit (N) and
        #   its complementary no-digit (W) in the same cell
        for c in Npresent:
            r = aml.Duple(aml.LCSegment({NCMP[c]}), aml.LCSegment(term), False, 0, 0)
            ret.append(r)

        # Consider extensions of the current board configuration to try to fill
        #   empty cells
        for x, y in undetermined:
            for n in range(0, gridDimension):
                # This duple may or may not be consistent with
                # the embedding.
                r = aml.Duple(
                    aml.LCSegment(W[ixwn(n, x, y, gridDimension)]),
                    aml.LCSegment(term | N[ixwn(n, x, y, gridDimension)]),
                    False,
                    0,
                    0,
                )
                # Hypotheses are enforced only if consistent
                r.hypothesis = True
                ret.append(r)

    return ret


if __name__ == "__main__":
    random.seed(randseed)
    sys.setrecursionlimit(100000000)

    model = aml.Model()

    # --------------------------------------------------------------------
    # load the embedding theory, build constants and duples
    embedding = aml.amldl.load_embedding("embedding_Sudoku.py", gridDimension)
    CX = embedding["contextConstants"]

    constantsNames = embedding["constantsNames"]
    for name in constantsNames:
        # Add constants to the model's constant manager
        c = model.cmanager.setNewConstantIndexWithName(name)

        # Build the freest model: one atom for every constant
        at = aml.Atom(model.epoch, model.generation, [c])
        model.atomization.append(at)

    # Build duples
    p = embedding["positiveDuples"]
    n = embedding["negativeDuples"]

    # - build positive duples
    pduples = []
    for L, R, region, _ in p:
        rlt = aml.Duple(aml.LCSegment(L), aml.LCSegment(R), True, 0, region)
        pduples.append(rlt)

    # - build negative duples
    nduples = []
    for L, R, region, hyp in n:
        rlt = aml.Duple(aml.LCSegment(L), aml.LCSegment(R), False, 0, region)
        rlt.hypothesis = hyp
        nduples.append(rlt)

    if displayDuplesAtInitialization:
        reversedNameDictionary = model.cmanager.getReversedNameDictionary()
        printDuples(pduples, nduples, reversedNameDictionary)

    # --------------------------------------------------------------------

    if computeFullCrossing:
        # Use full crossing

        embedder = aml.full_crossing_embedder(model)
        # sort the duples for faster computation
        embedder.params.sortDuples = True
        embedder.params.calculateRedudacy = True
        embedder.params.removeRepetitions = True

        embedder.enforce(pduples)

        if saveAtomization:
            aml.saveAtomizationOnFileUsingBitarrays(
                model.atomization,
                model.cmanager,
                f"model_sudoku_{gridDimension}",
            )
    else:
        # Use sparse crossing

        embedder = aml.sparse_crossing_embedder(model)

        reversedNameDictionary = model.cmanager.getReversedNameDictionary()
        printDuples(
            embedder.exampleSet,
            embedder.counterexampleSet,
            reversedNameDictionary,
        )
        embedder.params.storePositives = False
        embedder.params.byQuotient = False
        embedder.params.useReduceIndicators = True
        # embedder.params.simplify_threshold = 1.1
        # embedder.params.ignore_single_const_ucs = False
        # Fractioning of the union model may not be needed
        embedder.params.negativeIndicatorThreshold = -1

        initial = aml.atomizationCopy(model.atomization)

        boardDict = {}
        fullBoard_count = 0
        rString = ""
        isNewBoard = False
        attempt = 0
        while fullBoard_count < fullBoard_target and attempt < maxAttempts:
            attempt += 1

            # Compute full or sparse crossing
            nduplesExt = nduples.copy()
            if isNewBoard and not isFullBoard:
                # Select a subset of atoms
                model.atomization, _, inconsistent = (
                    aml.selectAtomsFromNegativeDuplesAndExplicit(
                        model.atomization,
                        nduples,
                        [],
                        True,
                        aml.CSegment(CX),
                    )
                )

                # Keep the incomplete board of previous attempt and consider
                # potential extensions.
                nex = describeBoardAndExtensions(model, embedding, gridDimension)
                nduplesExt.extend(nex)
            else:
                #  restart the model atomization to freest model
                embedder.setAtomization(aml.atomizationCopy(initial))

            embedder.enforce(pduples, nduplesExt)

            # Select a subset of atoms from those that discrimiate the negative duples.
            # Prioritize the use of context constants so they are not discarded.
            selection, _, inconsistent = aml.selectAtomsFromNegativeDuplesAndExplicit(
                model.atomization,
                nduples,
                [],
                True,
                aml.CSegment(CX),
            )

            if inconsistent:
                print("Error: Inconsistent embedding")
                print("The embedding has some logical contradiction.")
                sys.exit(1)

            printGrid(selection, model.cmanager, embedding, gridDimension)
            isFullBoard, boardKey = checkFullBoard(selection, model.cmanager, embedding, gridDimension)  # fmt:skip

            isNewBoard = False
            if boardKey not in boardDict:
                boardDict[boardKey] = 0
                isNewBoard = True
            boardDict[boardKey] += 1

            # Quick results
            if isFullBoard:
                if isNewBoard:
                    fullBoard_count += 1
                    print("New Full Board Found")
                else:
                    print("Repeated Board")

            if isNewBoard:
                if isFullBoard:
                    rString += "B"  # New full board
                else:
                    rString += "_"  # New incomplete board
            else:
                rString += "."  # Repeated board configuration
            print(rString)
            print(f"Complete boards found: {fullBoard_count}")
            print("Union model size:", len(embedder.unionModel))
            print(f"Attempt {attempt}")
            print()
