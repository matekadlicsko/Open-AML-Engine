# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import random
import math
import sys

import aml
from MNIST import mnistGenerator, datasetType

# Training iterations
iterations = 5000  # Maximum number of mini-batch iterations
num_batches_for_periodic_test = 10  # Report FPR and FPN on the test set
ranseed = 123456789

mnist_image_size = 28 * 28  # Number of pixels per image
mnist_numclasses = 10
gray_threshold = 256 / 10

saveAtomization = False  # Save the model everytime a full test is performed


class trainingParameters:
    def __init__(self):
        self.constants = set()
        # Balance: number of times that false positives are overvalued over false negatives
        self.balance = mnist_numclasses - 1
        self.initialPTrainingExamples = 500
        self.initialNTrainingExamples = 500
        self.maxPTrainingExamples: int  # defined based on dataset
        self.maxNTrainingExamples: int  # defined based on dataset
        self.sizeOfFullTest: int  # defined based on dataset
        self.valSize = 10000
        self.fullDatasetAtBatch = 500


def digitToConstants(d):
    ret = [-1] * mnist_image_size
    for j in range(mnist_image_size):
        if d[j] > gray_threshold:
            ret[j] = j
        else:
            ret[j] = j + mnist_image_size
    result = set(ret)
    return result


def generateSet(typeOfDataset, dTerm, cmanager):
    print("Generating set")
    setSize = DATA_SOURCE.getRange(typeOfDataset=typeOfDataset)
    ret = []
    for i in range(setSize):
        digit, label, _ = DATA_SOURCE.getNextDigit(typeOfDataset=typeOfDataset)
        term = aml.LCSegment(digitToConstants(digit))
        region = 1 + label
        pRel = aml.Duple(dTerm[label], term, True, 0, region)
        aux = []
        for d in range(0, mnist_numclasses):
            if d != label:
                region = 1 + d
                nRel = aml.Duple(dTerm[d], term, False, 0, region)
                aux.append(nRel)
        ret.append([pRel, aux])
    random.shuffle(ret)
    return ret


def selectFromSet(fromSet, navigatorIndex, pSize, nSize):
    print("Selecting set")
    neg = 0
    pos = 0
    nbatch = []
    pbatch = []
    while pos < pSize or neg < nSize:
        pr, nr = fromSet[navigatorIndex]
        navigatorIndex += 1
        if navigatorIndex == len(fromSet):
            navigatorIndex = 0
            random.shuffle(fromSet)
        if pos < pSize:
            pbatch.append(pr)
            pos += 1
        if neg < nSize:
            nbatch.extend(nr)
            neg += len(nr)

    return navigatorIndex, pbatch, nbatch


def selectClass(wH, las, classToClassConstant):
    minsize = math.inf
    selectDigit = None
    for d in range(0, mnist_numclasses):
        dc = classToClassConstant[d]
        if dc in las:
            dlas = las[dc]
            disc = dlas - wH.las
            discsize = len(disc)
            if discsize < minsize:
                selectDigit = d
                minsize = discsize

    return selectDigit


def batchTraining(embedder, model, DATA_SOURCE, params):
    # Add embedding constants to model
    for i in params.constants:
        c = model.cmanager.setNewConstantIndex()
        if i != c:
            raise ValueError
    # Add also constants for each label
    dTerm = [None] * mnist_numclasses
    classToClassConstant = []
    for i in range(0, mnist_numclasses):
        dIndex = model.cmanager.setNewConstantIndexWithName(f"D[{i}]")
        dTerm[i] = aml.LCSegment([dIndex])
        classToClassConstant.append(dIndex)

    # Define parameters for growing the batch size over time
    ipBatchSize = params.initialPTrainingExamples
    inBatchSize = params.initialNTrainingExamples * params.balance
    fpBatchSize = params.maxPTrainingExamples
    fnBatchSize = params.maxNTrainingExamples * params.balance

    # Sets of relations to be used for training and test
    trainingSet = generateSet(datasetType.training, dTerm, model.cmanager)
    testSet = generateSet(datasetType.test, dTerm, model.cmanager)
    tr_iterator = 0
    ts_iterator = 0

    classificationError = -1
    # Start training
    for batch in range(iterations):
        # Heuristics for computing minibatch size
        pBatchSize = min(
            ipBatchSize
            + batch * (fpBatchSize - ipBatchSize) / params.fullDatasetAtBatch,
            2 * fpBatchSize,
        )
        nBatchSize = min(
            inBatchSize
            + batch * (fnBatchSize - inBatchSize) / params.fullDatasetAtBatch,
            int(0.75 * fnBatchSize),
        )

        # Select minibatch
        tr_iterator, pbatch, nbatch = selectFromSet(
            trainingSet,
            tr_iterator,
            pBatchSize,
            nBatchSize,
        )

        # Enforce relation in the model
        embedder.enforce(pbatch, nbatch)

        # Test
        if (batch % num_batches_for_periodic_test == 0) and (batch != 0):
            # Select relations for test
            ts_iterator, ptest, ntest = selectFromSet(
                testSet,
                ts_iterator,
                params.sizeOfFullTest,
                params.sizeOfFullTest * params.balance,
            )
            testSetDuples = ptest.copy()
            testSetDuples.extend(ntest)

            # Precompute the lower atomic segment for all terms (instead of duple by duple)
            print("Calculate test space")
            las = aml.calculateLowerAtomicSegment(
                embedder.lastUnionModel,
                model.cmanager.embeddingConstants,
                True,
            )
            testSpace = aml.termSpace()
            for rel in testSetDuples:
                rel.wL = testSpace.add(rel.L)
                rel.wH = testSpace.add(rel.R)
            testSpace.calculateLowerAtomicSegments(embedder.lastUnionModel, las)

            # Compute and report statistics
            correct = 0
            incorrect = 0
            cm = [[0] * mnist_numclasses for d in range(0, mnist_numclasses)]
            for r in testSetDuples:
                if r.positive:
                    digit = r.region - 1
                    selectedDigit = selectClass(r.wH, las, classToClassConstant)
                    if digit == selectedDigit:
                        correct += 1
                    else:
                        incorrect += 1
                    cm[digit][selectedDigit] += 1
            classificationError = incorrect / (correct + incorrect)
            print(f"correct: {correct}, incorrect: {incorrect}")
            for d in range(0, mnist_numclasses):
                print(cm[d])

            if saveAtomization:
                aml.saveAtomizationOnFileUsingBitarrays(
                    [at for at in embedder.lastUnionModel if not at.isSizeOne()],
                    model.cmanager,
                    f"MNIST_{ranseed}_E{batch}",
                )

        cOrange = "\u001b[33m"
        cReset = "\u001b[0m"
        print(
            f"{cOrange}BATCH: {batch}{cReset}",
            f"batchSize({pBatchSize:.0f}, {nBatchSize:.0f})",
            f"Classification error: {classificationError}",
            f"UnionModel: {len(embedder.unionModel)}",
            f"({len([at for at in embedder.unionModel if not at.isSizeOne()])})",
        )


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(ranseed)
    sys.setrecursionlimit(100000000)

    params = trainingParameters()
    DATA_SOURCE = mnistGenerator(params.valSize)

    params.maxPTrainingExamples = DATA_SOURCE.getRange(typeOfDataset=datasetType.training)  # fmt:skip
    params.maxNTrainingExamples = params.maxPTrainingExamples
    params.sizeOfFullTest = DATA_SOURCE.getRange(typeOfDataset=datasetType.test)
    params.constants = set([c for c in range(0, 2 * mnist_image_size)])

    model = aml.Model()

    embedder = aml.sparse_crossing_embedder(model)
    # If a positive duple produced new atoms during crossing, the duple is stored and reused in the following batch
    embedder.params.storePositives = True
    # The amount of atoms in the dual is reduced while keeping trace invariance
    embedder.params.useReduceIndicators = True
    # If enforceTraceConstraints is False a fresh atom is added to each constant every cycle.
    embedder.params.enforceTraceConstraints = True
    # Faster crossing only valid for binary classification
    embedder.params.byQuotient = False
    # True if the set of embedding constants does not change during training
    embedder.params.staticConstants = True
    # negativeIndicatorThreshold requires a minimal fraction of atoms from
    #   negative Duples in the dual. The effect is to increase atom diversity.
    embedder.params.negativeIndicatorThreshold = 0.1

    batchTraining(embedder, model, DATA_SOURCE, params)
