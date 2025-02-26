# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import sys
import random

import aml


# Training iterations
iterations = 5000  # Maximum number of mini-batch iterations
GRID_SIDE = 4  # length of image side
ranseed = 16

noise_percentage = 50  # 50% is max allowed noise value
noise = int(100 / min(noise_percentage, 50) - 2)

# True: Obtain the freest model via the full crossing algorithm
#   It can be used for gridDimension 4
#   It becomes intractable for larger board sizes
# False: Use the sparse crossing algorithm.
computeFullCrossing = False

# Save model every time the full test is run
saveAtomization = False

# Problem:
# 0: no vertical bar
# 1: complete vertical bar
# 2: odd number of vertical bars
# 3: even number of vertical bars
problem = 0


class trainingParameters:
    def __init__(self):
        self.constants = set()
        self.initialPTrainingExamples = 2000  # inital batch size positive relations
        self.initialNTrainingExamples = 2000  # inital batch size negative relations
        self.sizeOfQuickTest = 200  # test every 10 iterations
        self.sizeOfFullTest = 1000  # test every iteration


def createBackgroundForEvenOdd(size, columns):
    image = []
    for y in range(size):
        line = []
        for x in range(size):
            if x in columns:
                line.append(1)
            else:
                if random.randint(0, 1 + noise) == 0:
                    line.append(1)
                else:
                    line.append(0)
        image.append(line)

    for c in range(size):
        if c not in columns:
            allOne = True
            for y in range(size):
                if image[y][c] == 0:
                    allOne = False
                    break
            if allOne:
                return createBackgroundForEvenOdd(size, columns)
    return image


def evenExample(size, typeOfDataset=1):
    ret = []
    while True:
        columns = []
        count = 0
        averageNumberOflines = 1 + (random.randint(0, 10000) % (size - 1))
        for c in range(size):
            if random.randint(0, 1000) % size < averageNumberOflines:
                columns.append(c)
                count += 1
        if count % 2 == 0:
            break

    image = createBackgroundForEvenOdd(size, columns)

    for x in range(size):
        for y in range(size):
            i = y * size + x
            if image[y][x] == 1:
                ret.append(i)
            else:
                ret.append(size * size + i)

    return set(ret)


def oddExample(size, typeOfDataset=1):
    ret = []
    while True:
        columns = []
        count = 0
        averageNumberOflines = 1 + (random.randint(0, 10000) % (size - 1))
        for c in range(size):
            if random.randint(0, 1000) % size < averageNumberOflines:
                columns.append(c)
                count += 1
        if count % 2 == 1:
            break

    image = createBackgroundForEvenOdd(size, columns)

    for x in range(size):
        for y in range(size):
            i = y * size + x
            if image[y][x] == 1:
                ret.append(i)
            else:
                ret.append(size * size + i)

    return set(ret)


def verticalBarExample(size, typeOfDataset=1):
    ret = []
    retW = []
    column = random.randint(0, size - 1)

    for i in range(size * size):
        if i % size == column:
            ret.append(i)
        else:
            if random.randint(0, 1 + noise) == 0:
                ret.append(i)
            else:
                retW.append(size * size + i)

    ret.extend(retW)
    return set(ret)


def nonVerticalBarExample(size, typeOfDataset=1):
    ret = []
    retW = []
    for i in range(size * size):
        if random.randint(0, 1 + noise) == 0:
            ret.append(i)
        else:
            retW.append(size * size + i)

    for column in range(0, size):
        hasLine = True
        for i in range(size * size):
            if i % size == column:
                if not i in ret:
                    hasLine = False
                    break
        if hasLine:
            return nonVerticalBarExample(size, typeOfDataset)

    ret.extend(retW)
    return set(ret)


def generateExampleSet(
    cmanager,
    grid_side,
    L,
    exampleGeneratorFunction,
    counterxampleGeneratorFunction,
    size,
    generation,
    region,
    typeOfDataset=0,
):
    testset = []
    numtests = size
    for k in range(numtests):
        exampleTerm = aml.LCSegment(exampleGeneratorFunction(grid_side, typeOfDataset))
        pRel = aml.Duple(L, exampleTerm, True, generation, region)
        testset.append(pRel)

        counterExampleTerm = aml.LCSegment(
            counterxampleGeneratorFunction(grid_side, typeOfDataset)
        )
        nRel = aml.Duple(L, counterExampleTerm, False, generation, region)
        testset.append(nRel)
    return testset


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def batchTraining(
    embedder,
    model,
    exampleGeneratorFunction,
    counterxampleGeneratorFunction,
    grid_side,
    params,
):
    # Add embedding constants to model
    for i in params.constants:
        c = model.cmanager.setNewConstantIndex()
        if i != c:
            raise ValueError
    # Add also a constant for the positive class
    vIndex = model.cmanager.setNewConstantIndexWithName("v")
    vTerm = aml.LCSegment([vIndex])

    # Define parameters for the batch size
    pBatchSize = params.initialPTrainingExamples
    nBatchSize = params.initialNTrainingExamples

    region = 1
    testResult = "none"
    testResultOnUnionModel = "none"
    strReportError = ""
    # Start training
    for i in range(iterations):
        # Select minibatches
        print("Generating training set")
        nbatch = []
        for e in range(int(nBatchSize)):
            counterExampleTerm = aml.LCSegment(counterxampleGeneratorFunction(grid_side))  # fmt:skip
            nRel = aml.Duple(vTerm, counterExampleTerm, False, model.generation, region)
            nbatch.append(nRel)

        pbatch = []
        for e in range(int(pBatchSize)):
            exampleTerm = aml.LCSegment(exampleGeneratorFunction(grid_side))
            pRel = aml.Duple(vTerm, exampleTerm, True, model.generation, region)
            pbatch.append(pRel)

        # Enforce relations in the model
        embedder.enforce(pbatch, nbatch)

        # Testing
        fullTest = (i % 10 == 0) and (i != 0)
        if fullTest:
            sizeOfTest = params.sizeOfFullTest
        else:
            sizeOfTest = params.sizeOfQuickTest

        print("Generating test set")
        testSet = generateExampleSet(
            model.cmanager,
            grid_side,
            vTerm,
            exampleGeneratorFunction,
            counterxampleGeneratorFunction,
            sizeOfTest,
            model.generation,
            region,
        )

        print("Testing")
        testConsts = aml.CSegment()
        testSpace = aml.termSpace()
        for rel in testSet:
            rel.wL = testSpace.add(rel.L)
            rel.wH = testSpace.add(rel.R)
            testConsts |= rel.L
            testConsts |= rel.R

        las = aml.calculateLowerAtomicSegment(model.atomization, testConsts, True)
        testSpace.calculateLowerAtomicSegments(model.atomization, las)
        # master accuracy can stay permanently high
        testResult = embedder.test(testSet)

        # Test using the whole test set
        if fullTest:
            # union model accuracy must increase with training
            print("Test on reseve")
            las = aml.calculateLowerAtomicSegment(embedder.lastUnionModel, testConsts, True) 
            testSpace.calculateLowerAtomicSegments(embedder.lastUnionModel, las)
            if False:
                # this meassures the error rate at the optimal misses cutoff
                # error rate values for an optimal cutoff larger than 1 are only orientative 
                # and do not represtn a valid metric
                (
                    strTestResultOnUnionModel,
                    testResultOnUnionModel,
                    misses,
                ) = aml.evaluateUsingUnionModelAtOptimalCutoff(testSet, -1, region)
            else:
                mises = 1
                (
                    strTestResultOnUnionModel,
                    testResultOnUnionModel,
                ) = aml.evaluateUsingUnionModel(testSet, region, mises)


            print("unionModel error:", strTestResultOnUnionModel)
            strReportError = strTestResultOnUnionModel

            if saveAtomization:
                aml.saveAtomizationOnFile(
                    embedder.model.atomization,
                    embedder.cmanager,
                    f"vertical_bars_{i}",
                )
        cOrange = "\u001b[33m"
        cReset = "\u001b[0m"
        print(
            f"{cOrange}BATCH#: {i}{cReset}",
            f"seen({embedder.vars.pcount}, {embedder.vars.ncount})",
            f"batchSize({pBatchSize}, {nBatchSize})",
            f"unionModel {strReportError}",
            f"unionModel size {len(embedder.unionModel)}",
        )


# ------------------------------------------------------------------------------


def calculateFreestModel(
    model, exampleGeneratorFunction, counterxampleGeneratorFunction, grid_side, params
):
    if grid_side > 4:
        input(
            "Full crosssing is a very intensive computation. It is recommended to try with smaller grid sizes. Continue?"
        )

    params_full = aml.params_full(
        calculateRedundancy=True,
        removeRepetitions=True,
        sortDuples=False,
        binary=True,
    )

    embedder = aml.full_crossing_embedder(model)
    embedder.params = params_full

    # Add embedding constants to model and manually build freest model
    model.atomization = []
    for i in params.constants:
        c = model.cmanager.setNewConstantIndex()
        if i != c:
            raise ValueError
        at = aml.Atom(model.epoch, model.generation, [c])
        model.atomization.append(at)
    # Add also a constant for the positive class
    vIndex = model.cmanager.setNewConstantIndexWithName("v")
    vTerm = aml.LCSegment([vIndex])
    at = aml.Atom(model.epoch, model.generation, [vIndex])
    model.atomization.append(at)

    region = 1
    # Start training
    for i in range(iterations):
        # Build duples from an image and the positive class constant "v"
        exampleTerm = aml.LCSegment(exampleGeneratorFunction(grid_side))
        pRel = aml.Duple(vTerm, exampleTerm, True, model.generation, region)

        # Enforce relations in the model
        embedder.enforce([pRel])

        print("example:", i)


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(ranseed)
    sys.setrecursionlimit(100000000)

    model = aml.Model()
    params = trainingParameters()

    if problem == 0:
        # create model for lack of a complete vertical bar
        exampleGeneratorFunction = nonVerticalBarExample
        counterxampleGeneratorFunction = verticalBarExample
        params.constants = set([c for c in range(0, 2 * GRID_SIDE * GRID_SIDE)])
    elif problem == 1:
        # create model for presence of a complete vertical bar
        exampleGeneratorFunction = verticalBarExample
        counterxampleGeneratorFunction = nonVerticalBarExample
        params.constants = set([c for c in range(0, 2 * GRID_SIDE * GRID_SIDE)])
    elif problem == 2:
        # create model for an odd number of complete vertical bars
        exampleGeneratorFunction = oddExample
        counterxampleGeneratorFunction = evenExample
        params.constants = set([c for c in range(0, 2 * GRID_SIDE * GRID_SIDE)])
    elif problem == 3:
        # create model for an even number of complete ertical bars
        exampleGeneratorFunction = evenExample
        counterxampleGeneratorFunction = oddExample
        params.constants = set([c for c in range(0, 2 * GRID_SIDE * GRID_SIDE)])
    else:
        raise IndexError("Wrong problem index")

    if computeFullCrossing:
        # FULL CROSSSING
        calculateFreestModel(
            model,
            exampleGeneratorFunction,
            counterxampleGeneratorFunction,
            GRID_SIDE,
            params,
        )
    else:
        # SPARSE CROSSING
        embedder = aml.sparse_crossing_embedder(model)

        # Reduce the number of atoms in the dual (True) or use all the atoms in the dual (False)
        embedder.params.useReduceIndicators = False
        # Alternative method to enforce positive traces in binary classifiers
        embedder.params.byQuotient = False

        batchTraining(
            embedder,
            model,
            exampleGeneratorFunction,
            counterxampleGeneratorFunction,
            GRID_SIDE,
            params,
        )
