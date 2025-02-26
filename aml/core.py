# Copyright (C) 2025 Algebraic AI - All Rights Reserved
# Go to github.com/algebraic-ai for full license details.

import random
import traceback

from .aml_fast.aml_fast import runCompiled
from . import amlset
from . import config
from .io import logDebug, logInfo, logWarn, logError


class UCSegment(amlset):
    """
    Representation of an upper constant segment:
    UCSegment < {c1, c2, ...}
    """

    pass


class LCSegment(amlset):
    """
    Representation of a lower constant segment:
    {c1, c2, ...} < LCSegment
    """

    pass


class CSegment(amlset):
    """
    Representation of a set of constants
    """

    pass


class Atom:
    """
    Individual atom from an atomization model.

    Vars:
    ucs (UCSegment) : representation of the upper constant segment of the atom
    gen (int)       : iteration at which the atom was created
    G   (int)       : amount of crossings needed to produce the atom
    ID  (int)       : unique identifier
    """

    IDS = 0

    def __init__(self, epoch, generation, ucsparam):
        """
        Note that the 'ucsparam' is copied when creating an atom.
        """

        self.ucs = UCSegment(ucsparam)
        self.epoch = epoch
        self.gen = generation
        self.redundancyChecked = False
        self.G = 0
        self.trace = None
        self.unionUpdateEntrance = -1
        Atom.IDS += 1
        self.ID = Atom.IDS

    def __eq__(self, other):
        return self.ucs == other.ucs

    def __repr__(self):
        return f"ucs: {self.ucs}\n" f"trace: {self.trace}\n"

    def __str__(self):
        return f"Atom({', '.join(str(x) for x in self.ucs)})"

    def copy(self):
        ret = Atom(self.epoch, self.gen, self.ucs)
        ret.G = self.G
        return ret

    def atomUnion(self, at, epoch):
        ret = Atom(epoch, max(self.gen, at.gen), [])
        ret.ucs = self.ucs | at.ucs
        ret.G = max(self.G + 1, at.G)

        return ret

    def toPinningTerm(self, C):
        pTerm = C - self.ucs
        if len(pTerm) == 0:
            raise ValueError("zero atom")
        return pTerm

    def isSizeOne(self):
        if isinstance(self.ucs, set):
            return len(self.ucs) == 1
        else:
            return self.ucs.len_upto2() == 1

    def __hash__(self):
        if isinstance(self.ucs, set):
            return hash(frozenset(self.ucs))
        else:
            return hash(self.ucs)


class Duple:
    """
    It represents a logic sentence of the embedding: `Left < Right`.
    It takes two terms for the left and right side of the inclusion operator.

    Vars:
    L,R (LCSegment)   : left and right terms of the Duple
    positive (bool)   : True  for positive duples (inclusion)
                        false for negative duples (exclusion)
    generation (int)  : to store generation at which it was created
    region (int)      : can be used to group duples
    hypothesis (bool) : when True the Duple is only used during training
                        if it does not create an inconsistency
    """

    def __init__(self, L, R, positive, generation, region, hypothesis=False):
        self.L = L
        self.R = R
        self.positive = positive
        self.generation = generation
        self.region = region
        self.hypothesis = hypothesis
        self.wL = None
        self.wH = None
        self.lastUnionUpdate = -1

    def __repr__(self):
        return f"{self.L} :: {self.R} - {self.positive}, {self.generation}, {self.region}, {self.hypothesis}"

    def copy(self):
        return Duple(self.L, self.R, self.positive, self.generation, self.region, self.hypothesis)  # fmt:skip


class ConstantManager:
    """
    Hold information about the model's constants.
    Establish mapping between indices and embedding constants

    Vars:
    definedWithName (Dict[str:int]) : map from names to internal indices
                                      used by the engine {name -> index}
    embeddingConstants (amlset)     : set with indices created/used
    """

    def __init__(self):
        self.lastDefConstantOrChain = -1
        self.definedWithName = {}
        self.reversedNameDict = {}
        self.embeddingConstants = CSegment()

    def __eq__(self, other):
        a = self.lastDefConstantOrChain == other.lastDefConstantOrChain
        b = self.definedWithName == other.definedWithName
        c = self.embeddingConstants == other.embeddingConstants
        return a and b and c

    def copy(self):
        ret = ConstantManager()
        ret.lastDefConstantOrChain = self.lastDefConstantOrChain
        ret.definedWithName = self.definedWithName.copy()
        ret.reversedNameDict = self.reversedNameDict.copy()
        ret.embeddingConstants = self.embeddingConstants.copy()
        return ret

    def setNewConstantIndex(self):
        """
        Create a new constant.
        Return the index of the new constant.
        """

        self.lastDefConstantOrChain += 1
        self.embeddingConstants.add(self.lastDefConstantOrChain)
        return self.lastDefConstantOrChain

    def setNewConstantIndexWithName(self, name):
        """
        Create a new constant and store its name in 'definedWithName".
        Return the index of the new constant.
        """

        c = self.setNewConstantIndex()
        self.definedWithName[name] = c
        self.reversedNameDict[c] = name
        return c

    def getReversedNameDictionary(self):
        """
        Return a map from constants' indices to constants' names.
        """

        return self.reversedNameDict

    def updateConstantsTo(self, atomization, unionModel, storedPositives):
        """
        Remove unused constants from the ConstantManager.
        Removes constants not present in 'atomization',
        'unionModel', or in 'storedPositives'.
        """

        logInfo("Removing unused constants in ConstantManager")
        standing = CSegment()

        for at in atomization:
            standing |= CSegment(at.ucs)

        for at in unionModel:
            standing |= CSegment(at.ucs)

        for r in storedPositives:
            standing |= r.L
            standing |= r.R

        toDelete = self.embeddingConstants - standing

        logInfo(f"- Standing: {len(standing)}")
        logInfo(f"- Deleting: {len(toDelete)}")
        if bool(toDelete):
            self.embeddingConstants &= standing


# -----------------------------------------------------------------------------


def atomizationCopy(atomSet):
    """Deep copy of an atomization"""
    ret = []
    for at in atomSet:
        ret.append(at.copy())
    return ret


def interpretTerm(term, reversedNameDictionary):
    ret = []
    for indx in term:
        if indx in reversedNameDictionary:
            ret.append(reversedNameDictionary[indx])
        else:
            ret.append(f"{indx}!")
    return ret


def lowerOrEqual(left, right, atomization):
    """
    Return True if the term 'left' is contained in the term 'right'.
    If the lower atomic segment of a term A is a subset
    of the lower atomic segment of another term B, then the term A
    is contained in B.
    If A has some atom that B lacks, then A is not contained in B.
    """

    for at in atomization:
        if not at.ucs.isdisjoint(left):
            if at.ucs.isdisjoint(right):
                return False
    return True


def separateDiscriminant(leftTerm, rightTerm, atomization, delay=True):
    discriminant = []
    nonDiscriminant = []
    lasRightTerm = []
    # to avoid computing unnecesary isDisjoint operations
    lasH_delayed = []

    for at in atomization:
        if not at.ucs.isdisjoint(leftTerm):
            if at.ucs.isdisjoint(rightTerm):
                discriminant.append(at)
            else:
                nonDiscriminant.append(at)
                lasRightTerm.append(at)
        else:
            nonDiscriminant.append(at)
            if (not delay) or bool(discriminant):
                if not at.ucs.isdisjoint(rightTerm):
                    lasRightTerm.append(at)
            else:
                lasH_delayed.append(at)

    if bool(discriminant) and bool(lasH_delayed):
        for at in lasH_delayed:
            if not at.ucs.isdisjoint(rightTerm):
                lasRightTerm.append(at)

    return discriminant, nonDiscriminant, lasRightTerm


def atomsNotIn(atomization, term):
    """
    Return the atoms in 'atomization' that do not form part of
    the lower atomic segment of 'term'.
    """

    ret = []
    for at in atomization:
        if at.ucs.isdisjoint(term):
            ret.append(at)
    return ret


def atomsIn(atomization, term):
    """
    Return the atoms in 'atomization' that form part of
    the lower atomic segment of 'term'.
    """

    ret = []
    for at in atomization:
        if not at.ucs.isdisjoint(term):
            ret.append(at)
    return ret


def calculateAtomSetProduct(setL, setH, epoch):
    """
    Product operation for full crossing
    """

    ret = []
    for atL in setL:
        for atH in setH:
            nAt = atL.atomUnion(atH, epoch)
            ret.append(nAt)

    return ret


def cross_simpler(
    discriminant, nonDiscriminant, lasRightTerm, atomization, epoch, binary
):
    """
    Performs full crossing of a Duple (leftTerm, rightTerm) over atomization.
    Takes as input the result from separateDiscriminant
        (discriminant, nonDiscriminant, lasRightTerm)
            = separateDiscriminant(leftTerm, rightTerm, atomization)

    Vars:
    binary (bool) : optimization when leftTerm only has one constant and is
                    common for all duples
    """

    if not bool(discriminant):
        return atomization

    ret = nonDiscriminant.copy()

    if binary:
        filteredAtoms = [at for at in lasRightTerm if at.isSizeOne()]
        ret.extend(calculateAtomSetProduct(discriminant, filteredAtoms, epoch))
    else:
        ret.extend(calculateAtomSetProduct(discriminant, lasRightTerm, epoch))

    return ret


def cross(discriminant, nonDiscriminant, lasRightTerm, atomization, constants, epoch, binary):  # fmt:skip
    """
    Performs full crossing of a Duple (leftTerm, rightTerm) over atomization.
    It removes repeted and redundant atoms during training.
    Takes as input the result from separateDiscriminant
        (discriminant, nonDiscriminant, lasRightTerm)
            = separateDiscriminant(leftTerm, rightTerm, atomization)

    Vars:
    binary (bool) : optimization when leftTerm only has one constant and is
                    common for all duples
    """

    if not bool(discriminant):
        return atomization

    ret = nonDiscriminant.copy()

    if binary:
        auxH = [at for at in lasRightTerm if at.isSizeOne()]
    else:
        auxH = lasRightTerm

    removed_repeated = 0
    removed_redundant = 0
    logInfo("Calculating full crossing")
    for idx, atL in enumerate(discriminant):
        for atH in auxH:
            nAt = atL.atomUnion(atH, epoch)
            ret.append(nAt)

        if len(ret) >= 1000000:
            ret_size = len(ret)
            ret = removeRepeatedAtoms(ret)
            removed_repeated += ret_size - len(ret)
            ret_size = len(ret)
            ret = removeRedundantAtoms(ret, constants, False)
            removed_redundant += ret_size - len(ret)
            logInfo(f"{idx} / {len(discriminant)} ", end="", flush=True)

    ret_size = len(ret)
    ret = removeRepeatedAtoms(ret)
    removed_repeated += ret_size - len(ret)
    ret_size = len(ret)
    ret = removeRedundantAtoms(ret, constants, True)  # mark as checked
    removed_redundant += ret_size - len(ret)
    logInfo(
        f"From {len(ret) + removed_repeated + removed_redundant}"
        f" to {len(ret) + removed_redundant} (repetition)"
    )
    logInfo(f"From {len(ret) + removed_redundant} to {len(ret)} (redundancy)")

    return ret


def crossWithTraces(tr, disc, noDisc, lasH, atomSet, model):
    if not bool(disc):
        return atomSet

    ret = noDisc.copy()
    ret.extend(tr.calculateAtomSetProduct(disc, lasH, model.epoch))
    return ret


def removeRepeatedAtoms(atomization):
    """
    Remove repeated atoms with the same upper constant segment.
    From a pair o repeated atoms, it preserves the one with the most recent generation.
    """

    hashDict = {}
    ret = []
    for at in atomization:
        key = at.__hash__()
        if key in hashDict:
            found = False
            for at2 in hashDict[key]:
                if at.ucs == at2.ucs:  # hashes can collide
                    at2.epoch = min(at2.epoch, at.epoch)
                    at2.gen = max(at2.gen, at.gen)
                    found = True
                    break
            if not found:
                hashDict[key].add(at)
                ret.append(at)
        else:
            hashDict[key] = set([at])
            ret.append(at)

    logInfo(f"From {len(atomization)} to {len(ret)}")
    return ret


def _removeRedundantAtoms_innermost(las, constants, atFromId, atms, thisAset):
    ret = []
    for at in thisAset:
        survives = True

        if not at.redundancyChecked:
            aux = atms.copy()
            compUcs = constants - at.ucs
            for c in compUcs:
                if c in las:
                    aux -= las[c]
                    if not bool(aux):
                        break

            if bool(aux):
                ucs = CSegment(at.ucs)
                for atId in aux:
                    ucs -= atFromId[str(atId)].ucs
                    if not bool(ucs):
                        survives = False
                        break

        if survives:
            ret.append(at)

    return ret


def _removeRedundantAtoms_inner(thisAset, prevAset, las, constants, atFromId, atms, markAsChecked):  # fmt:skip
    if len(prevAset) == 0:
        ret = thisAset.copy()
    else:
        ret = _removeRedundantAtoms_innermost(las, constants, atFromId, atms, thisAset)

    for at in ret:
        if markAsChecked:
            at.redundancyChecked = True
        atms.add(at.ID)
        atFromId[str(at.ID)] = at
        for c in at.ucs:
            if not c in las:
                las[c] = amlset([])
            las[c].add(at.ID)
    return ret


def removeRedundantAtoms(atomization, constants, markAsChecked):
    """
    Return a new atomization containing the non redundant atoms in 'atomization'.
    An atom is redundant with respecto to an atomization if
    it can be formed as the union of other atoms in the atomization.
    """

    if len(atomization) == 0:
        return []

    atomization.sort(key=lambda at: len(at.ucs))
    currentLength = len(atomization[0].ucs)

    las = {}
    atFromId = {}
    atms = amlset([])

    ret = []
    thisAset = []
    prevAset = []
    for at in atomization:
        length = len(at.ucs)
        if length > currentLength:
            currentLength = length
            ret.extend(
                _removeRedundantAtoms_inner(
                    thisAset, prevAset, las, constants, atFromId, atms, markAsChecked
                )
            )
            prevAset.extend(thisAset)
            thisAset = [at]
        else:
            thisAset.append(at)

    ret.extend(
        _removeRedundantAtoms_inner(thisAset, prevAset, las, constants, atFromId, atms, markAsChecked)  # fmt:skip
    )

    logInfo(f"From {len(atomization)} to {len(ret)}")
    return ret


def separateCurrentGeneration(atoms, currentGen):
    thisGen = []
    prevGen = []
    for at in atoms:
        if at.gen == currentGen:
            thisGen.append(at)
        else:
            prevGen.append(at)
    return thisGen, prevGen


def removeRedundantAtomsSegregatingCurrentGeneration(atoms, constants, gen):
    thisGen, prevGen = separateCurrentGeneration(atoms, gen)
    ret = removeRedundantAtoms(prevGen, constants, True)
    ret.extend(removeRedundantAtoms(thisGen, constants, True))
    return ret


def calculateLowerAtomicSegment(atoms, constantSet, asPositionTrueAsObjectFalse):
    las = {}
    for x, at in enumerate(atoms):
        for indx in at.ucs & constantSet:
            if indx not in las:
                if asPositionTrueAsObjectFalse:
                    las[indx] = amlset()
                else:
                    las[indx] = set()
            if asPositionTrueAsObjectFalse:
                las[indx].add(x)
            else:
                las[indx].add(at)
    return las


def printGSpectrum(atomSet, resFile=None):
    atList = []
    for at in atomSet:
        atList.append([at.G, at])
    atList.sort(key=lambda x: x[0])

    totaAtoms = len(atomSet)
    atms = 0
    G = 0
    print("G spectrum:")
    while atms < totaAtoms:
        atAtG = []
        for i, x in enumerate(atList):
            if x[0] == G:
                atAtG.append(x[1])
            else:
                atList = atList[i:]
                break

        if len(atAtG) > 0:
            aux = ["  G", G, "atoms", len(atAtG)]
            print(*aux)
            if resFile is not None:
                resFile.write("<GSPEC>" + str(aux) + "\n")
        atms += len(atAtG)
        G += 1


def printLSpectrum(atomSet, resFile=None):
    atList = []
    for at in atomSet:
        atList.append([len(at.ucs), at])
    atList.sort(key=lambda x: x[0])

    totaAtoms = len(atomSet)
    atms = 0
    L = 1
    print("L spectrum:")
    while atms < totaAtoms:
        atAtL = []
        for i, x in enumerate(atList):
            if x[0] == L:
                atAtL.append(x[1])
            else:
                atList = atList[i:]
                break
        if len(atAtL) > 0:
            aux = ["  L", L, "atoms", len(atAtL)]
            print(*aux)
            if resFile is not None:
                resFile.write("<LSPEC>" + str(aux) + "\n")
        atms += len(atAtL)
        L += 1


def printGENSpectrum(atomSet, resFile=None):
    atList = []
    for at in atomSet:
        atList.append([at.gen, at])
    atList.sort(key=lambda x: x[0])

    totaAtoms = len(atomSet)
    atms = 0
    GEN = 0
    print("GEN spectrum:")
    while atms < totaAtoms:
        atAtGEN = []
        for i, x in enumerate(atList):
            if x[0] == GEN:
                atAtGEN.append(x[1])
            else:
                atList = atList[i:]
                break

        if len(atAtGEN) > 0:
            aux = ["  GEN", GEN, "atoms", len(atAtGEN)]
            print("  GEN " + str(GEN) + " atoms " + str(len(atAtGEN)) + "   ", end="")
            if resFile is not None:
                resFile.write("<LSPEC>" + str(aux) + "\n")
        atms += len(atAtGEN)
        GEN += 1
    print()


def printCSpectrum(atomSet, cmanager, resFile=None):
    print("C Spectrum")
    reversedNameDictionary = cmanager.getReversedNameDictionary()
    las = calculateLowerAtomicSegment(atomSet, cmanager.embeddingConstants, True)
    for c in cmanager.embeddingConstants:
        if c in las:
            lenc = len(las[c])
        else:
            lenc = 0
        if c in reversedNameDictionary:
            print("  C", reversedNameDictionary[c], "atoms", lenc)
        else:
            print("  C", c, "atoms", lenc)


# -----------------------------------------------------------------------------


def calculateTraces(tr, atoms, wterms, j):
    for idx, wt in wterms:
        wt.trace = tr.getTraceOfTerm(wt.cset, atoms)
    return [wterms, j]


class _WrappedTerm:
    def __init__(self, cset):
        self.cset = cset
        self.trace = None
        self.freeTrace = None
        self.cpointer = 0  # c extensions helper field


class _SetFinder:
    def __init__(self, ref):
        self.A = None
        self.B = None
        self.c = None
        self.refwt = ref

    def find(self, term):
        if self.c is not None:
            if self.c in term:
                return self.A.find(term)
            else:
                return self.B.find(term)
        elif self.refwt is None:
            self.refwt = _WrappedTerm(term)
            return self.refwt, False
        else:
            dif = self.refwt.cset - term
            if dif:
                ldif = list(dif)
                self.c = ldif[0]
                self.A = _SetFinder(self.refwt)
                self.B = _SetFinder(_WrappedTerm(term))
                self.refwt = None
                return self.B.refwt, False

            dif = term - self.refwt.cset
            if dif:
                ldif = list(dif)
                self.c = ldif[0]
                self.A = _SetFinder(_WrappedTerm(term))
                self.B = _SetFinder(self.refwt)
                self.refwt = None
                return self.A.refwt, False
            else:
                return self.refwt, True

    def count(self):
        if self.refwt:
            return 1
        if self.A:
            return self.A.count() + self.B.count()
        return 0


class termSpace:
    def __init__(self):
        self.elements = []
        self.sf = _SetFinder(None)

    def add(self, term):
        wt, found = self.sf.find(term)
        if not found:
            self.elements.append(wt)
        return wt

    @runCompiled()
    def traceAll(self, tr, atoms):
        logInfo("Calculating traces")
        for wt in self.elements:
            wt.trace = tr.getTraceOfTerm(wt.cset, atoms)

    @runCompiled()
    def freeTraceAll(self, tr):
        logInfo("Calculating free traces")
        for wt in self.elements:
            wt.freeTrace = tr.getFreeTraceOfTerm(wt.cset, None)

    def updateTraces(self, tr, newAtoms):
        for wt in self.elements:
            for at in newAtoms:
                if not at.ucs.isdisjoint(wt.cset):
                    wt.trace &= tr.getTraceOfAtom(at)

    def returnFreeTraces(self, tr):
        for wt in self.elements:
            wt.freeTrace = None
            wt.freeTrace_ba = None

    @runCompiled()
    def calculateLowerAtomicSegments(self, atoms, las):
        logInfo("Calculating lower atomic segments of terms")
        for wt in self.elements:
            wt.las = amlset()
            for c in wt.cset:
                if c in las:
                    wt.las |= las[c]


# -----------------------------------------------------------------------------


class TraceHelper:
    def __init__(self, constants, numIndicators):
        self.maxTrace = amlset([i for i in range(numIndicators)])
        self.tD = [None] * len(self.maxTrace)
        self.atomIDs = amlset()
        self.constants = constants
        self.fastTable = None

        for i in self.maxTrace:
            self.tD[i] = amlset([])

    def atomFromId(self, ID):
        left = 0
        right = len(self.fastTable) - 1
        while left <= right:
            mid = (left + right) // 2
            at = self.fastTable[mid]
            if at.ID == ID:
                return at
            elif at.ID < ID:
                left = mid + 1
            else:
                right = mid - 1

        raise NotImplementedError()

    def update(self, atoms, tracer, complete):
        self.fastTable = atoms.copy()
        ids = amlset([at.ID for at in atoms])

        newatoms = ids - self.atomIDs

        if complete:
            self.atomIDs = ids
        else:
            self.atomIDs |= ids

        laset = len(atoms)
        for at in atoms:
            ID = at.ID
            if ID in newatoms:
                trace = tracer.getTraceOfAtom(at)
                out = self.maxTrace - trace
                for i in out:
                    self.tD[i].add(ID)

        return ids


class Tracer:
    def __init__(self, period, cmanager):
        self.indicators = []
        self.atomIndicators = []
        self.discardedIndicators = amlset([])
        self.period = period
        self.storeTraces = True
        self.checkStoreTraces = False
        self.warnOnTraceViolation = True
        self.warningSent = False
        self.cmanager = cmanager
        self.traceHelper = None

        self.constToFreeTraces = {}
        self.constToStoredTraces = {}
        self.recalculateConstantTraces = False

    def numIndicators(self):
        return len(self.indicators) + len(self.atomIndicators)

    def addNegativeH(self, nr):
        self.indicators.append(nr.copy())
        self.period += 1

    def addPinningAtom(self, at):
        self.atomIndicators.append(at)
        self.period += 1

    @runCompiled()
    def considerPositiveDuples(self, pduples):
        for i in range(len(self.indicators)):
            modified = True
            while modified:
                modified = False
                for pr in pduples:
                    if pr.R.issubset(self.indicators[i]):
                        sizeBefore = len(self.indicators[i])
                        self.indicators[i] |= pr.L
                        sizeAfter = len(self.indicators[i])
                        modified = modified or (sizeAfter > sizeBefore)

        self.period += 1

    def ensureIndicatorsAreUnique(self):
        logInfo(f"Number of indicators {self.numIndicators()}")

        if LCSegment == set:
            self.indicators = {frozenset(s) for s in self.indicators}
            self.indicators = [amlset(s) for s in self.indicators]
        else:
            self.indicators = list(frozenset(self.indicators))

        self.period += 1

        logInfo(f"Number of unique indicators {self.numIndicators()}")

    def getTraceOfAtom(self, at):
        if not at.trace is None:
            if self.period < at.trace[1]:
                raise ValueError("getTraceOfAtom failure")

            if self.period == at.trace[1]:
                return at.trace[0]

        aux = amlset([])
        for c in at.ucs:
            aux |= self.getFreeTraceOfConstant(c)

        if self.storeTraces:
            at.trace = [amlset(aux), self.period]
        return aux

    def getTraceOfAtomFromIndicators(self, at):
        aux = []
        for i in range(len(self.indicators)):
            if not at.ucs.isdisjoint(self.indicators[i]):
                aux.append(i)

        shift = len(self.indicators)
        for i in range(len(self.atomIndicators)):
            if not at.ucs.issubset(self.atomIndicators[i].ucs):
                aux.append(i + shift)

        return amlset(aux)

    def getFreeTraceOfTerm(self, term, constLowAtomicSegment=None):
        if bool(self.discardedIndicators):
            raise ValueError("getFreeTraceOfTerm error discardedIndicators")

        aux = []
        for i in range(len(self.indicators)):
            if term.issubset(self.indicators[i]):
                aux.append(i)

        shift = len(self.indicators)
        if constLowAtomicSegment is None:
            for i in range(len(self.atomIndicators)):
                if self.atomIndicators[i].ucs.isdisjoint(term):
                    aux.append(i + shift)
        else:
            atinds = amlset()
            for c in term:
                if c in constLowAtomicSegment:
                    atinds |= constLowAtomicSegment[c]
            atinds = amlset([i for i in range(len(self.atomIndicators))]) - atinds
            for i in atinds:
                aux.append(i + shift)

        return amlset(aux)

    def getFreeTraceOfTermOverSubsetOfInidicators(self, term, subset, shift):
        if bool(self.discardedIndicators):
            raise ValueError("getFreeTraceOfTermOverSubsetOfInidicators")

        aux = []
        for i in subset:
            if i < shift:
                if term.issubset(self.indicators[i]):
                    aux.append(i)
            else:
                if self.atomIndicators[i - shift].ucs.isdisjoint(term):
                    aux.append(i)

        return amlset(aux)

    def getTraceOfTerm(self, term, atoms):
        if bool(self.discardedIndicators):
            raise ValueError("getTraceOfTerm error discardedIndicators")

        trace = amlset([i for i in range(self.numIndicators())])
        for at in atoms:
            if not at.ucs.isdisjoint(term):
                trace &= self.getTraceOfAtom(at)

        if self.checkStoreTraces:
            ftrace = self.getFreeTraceOfTerm(term)
            if not ftrace.issubset(trace):
                for at in atoms:
                    at.trace = None

                trace = amlset([i for i in range(self.numIndicators())])
                for at in atoms:
                    if not at.ucs.isdisjoint(term):
                        trace &= self.getTraceOfAtom(at)

                if ftrace.issubset(trace):
                    logError("Problem in the cache system")

                raise ValueError("getTraceOfTerm error")

        return trace

    @runCompiled()
    def selectAllUsefulIndicators(self, nduplesIn, reversedNameDictionary):
        """
        Select all indicators that discriminate any negative Duple.
        This subset still discriminates the dual of the negative duples,
        i.e. there's at least one indicator in the discriminator of the traces
        of those duples.
        """

        if bool(self.discardedIndicators):
            raise ValueError("selectAllUsefulIndicators error discardedIndicators")

        take = amlset([])
        nrels = []
        for nr in nduplesIn:
            if nr.wL is None:
                tL = self.getFreeTraceOfTerm(nr.L)
            else:
                tL = nr.wL.freeTrace

            if nr.wH is None:
                tH = self.getFreeTraceOfTerm(nr.R)
            else:
                tH = nr.wH.freeTrace

            useful = tH - tL - self.discardedIndicators
            if not bool(useful):
                if nr.hypothesis:
                    logDebug("Hypothesis deleted")
                elif self.warnOnTraceViolation and not self.warningSent:
                    self.warningSent = True
                    logError("SelectAllUsefulIndicators error")
                    logError(interpretTerm(nr.R, reversedNameDictionary), tH)
                    logError(interpretTerm(nr.L, reversedNameDictionary), tL)
                    tb = traceback.format_exc()
                    logError(tb)
                    raise ValueError("Inconsistent")
                    nrels.append(nr)
            else:
                take |= useful
                nrels.append(nr)

        self.discardedIndicators = amlset([i for i in range(self.numIndicators())]) - take  # fmt:skip

        logInfo(f"Number of indicators after selecting useful {len(take)}")

        return nrels

    @runCompiled()
    def reduceIndicators(self, nduplesIn, reversedNameDictionary, singles):
        """
        Recursively select a subset of indicators until a minimum
        (not optimal) is reached.
        This subset still discriminates the dual of the negative duples,
        i.e. there's at least one indicator in the discriminator of the traces
        of those duples.
        """

        take = amlset([])
        duplesOut = amlset([])
        nduples = nduplesIn.copy()
        random.shuffle(nduples)

        for i, nr in enumerate(nduples):
            if nr.wL is None:
                tL = self.getFreeTraceOfTerm(nr.L)
            else:
                tL = nr.wL.freeTrace

            if nr.wH is None:
                tH = self.getFreeTraceOfTerm(nr.R)
            else:
                tH = nr.wH.freeTrace

            tDisc = tH - tL - self.discardedIndicators
            if not bool(tDisc):
                if self.warnOnTraceViolation and not self.warningSent:
                    self.warningSent = True
                    logError("ReduceIndicators error")
                    logError(interpretTerm(nr.R, reversedNameDictionary), tH)
                    logError(interpretTerm(nr.L, reversedNameDictionary), tL)
                    tb = traceback.format_exc()
                    logError(tb)
                    raise ValueError("Inconsistent")
            elif tDisc.isdisjoint(singles):
                aux = tuple(tDisc)
                if len(aux) == 1:
                    singles.add(aux[0])
                    duplesOut.add(i)
                elif tDisc.isdisjoint(take):
                    take.add(random.choice(aux))
            else:
                duplesOut.add(i)

        take |= singles

        aux = amlset([i for i in range(len(nduples))]) - duplesOut
        nduples = [nduples[i] for i in aux]

        logInfo(f"Number of unique indicators after reduction {len(take)}")

        discardedIndicators = amlset([i for i in range(self.numIndicators())]) - take

        if len(discardedIndicators) > len(self.discardedIndicators) and nduples:
            self.discardedIndicators = discardedIndicators
            self.reduceIndicators(nduples, reversedNameDictionary, singles)
        else:
            self.discardedIndicators = discardedIndicators

    def removeDiscardedIndicators(self):
        shift = len(self.indicators)

        self.atomIndicators = [
            self.atomIndicators[i - shift]
            for i in range(len(self.indicators), self.numIndicators())
            if i not in self.discardedIndicators
        ]

        self.indicators = [
            self.indicators[i]
            for i in range(len(self.indicators))
            if i not in self.discardedIndicators
        ]

        self.discardedIndicators = amlset([])
        self.period += 1

    def calculateAtomSetProduct(self, setL, setH, epoch):
        """
        Product operation for sparse crossing.
        """
        if self.traceHelper is None:
            tD = [None] * self.numIndicators()
            maxTrace = amlset([i for i in range(self.numIndicators())])
            for atH in setH:
                out = maxTrace - self.getTraceOfAtom(atH)
                for i in out:
                    if tD[i] is None:
                        tD[i] = []
                    tD[i].append(atH)
        else:
            tD = [-1] * self.numIndicators()
            setH.sort(key=lambda at: at.ID)
            setHIDs = self.traceHelper.update(setH, self, False)
            maxTrace = self.traceHelper.maxTrace

        ret = []
        setLIDS = amlset()
        for atL in setL:
            trL = self.getTraceOfAtom(atL)
            if self.traceHelper is not None:
                setLIDS.add(atL.ID)
            picked = False

            out = maxTrace - trL
            while bool(out):
                eta = random.choice(tuple(out))
                if self.traceHelper is not None:
                    if tD[eta] == -1:
                        self.traceHelper.tD[eta] &= self.traceHelper.atomIDs
                        tD[eta] = tuple(self.traceHelper.tD[eta] & setHIDs)
                tDeta = tD[eta]
                if tDeta is not None:
                    atH = random.choice(tDeta)
                    if self.traceHelper is not None:
                        atH = self.traceHelper.atomFromId(atH)
                    out &= self.getTraceOfAtom(atH)
                    nAt = atL.atomUnion(atH, epoch)
                    if self.storeTraces:
                        nAt.trace = [trL | self.getTraceOfAtom(atH), self.period]
                    ret.append(nAt)
                    picked = True

                elif self.warnOnTraceViolation and not self.warningSent:
                    raise ValueError("calculateAtomSetProduct trace error")
                    self.warningSent = True
                    out = out - amlset([eta])
                else:
                    out = out - amlset([eta])

            if not picked:
                atH = random.choice(tuple(setH))
                nAt = atL.atomUnion(atH, epoch)
                if self.storeTraces:
                    nAt.trace = [trL | self.getTraceOfAtom(atH), self.period]
                ret.append(nAt)

        if self.traceHelper is not None:
            self.traceHelper.atomIDs -= setLIDS
        return ret

    def getFreeTraceOfConstant(self, c):
        if self.recalculateConstantTraces:
            ctrace = self.getFreeTraceOfTerm(LCSegment([c]))
        else:
            if c in self.constToFreeTraces:
                aux = self.constToFreeTraces[c]
                if self.period == aux[1]:
                    ctrace = aux[0]
                else:
                    ctrace = self.getFreeTraceOfTerm(LCSegment([c]))
                    self.constToFreeTraces[c] = [ctrace, self.period]
            else:
                ctrace = self.getFreeTraceOfTerm(LCSegment([c]))
                self.constToFreeTraces[c] = [ctrace, self.period]
        return ctrace

    def getStoredTraceOfConstant(self, c):
        if c in self.constToStoredTraces:
            aux = self.constToStoredTraces[c]
            if self.period == aux[1]:
                ctrace = aux[0]
            else:
                raise ValueError("getStoredTraceOfConstant Error A")
        else:
            raise ValueError("getStoredTraceOfConstant Error B")
        return ctrace

    @runCompiled()
    def simplifyFromConstants(self, constants, atoms, generation):
        maxTrace = amlset([i for i in range(self.numIndicators())])
        tD = [None] * len(maxTrace)
        for i in maxTrace:
            tD[i] = amlset([])
        las = {}
        for c in constants:
            las[c] = amlset([])
        for x, at in enumerate(atoms):
            trace = self.getTraceOfAtom(at)
            out = maxTrace - trace
            for i in out:
                tD[i].add(x)
            for c in at.ucs & constants:
                las[c].add(x)

        # ------------------------------------------------------------

        constantList = list(constants)
        random.shuffle(constantList)

        selectedIds = amlset([])
        selected = []
        xcount = 0
        for c in constantList:
            ctrace = self.getStoredTraceOfConstant(c)

            lasc = las[c]
            out = maxTrace - ctrace

            while bool(out):
                xcount += 1
                eta = random.choice(tuple(out))
                candidates = tD[eta] & lasc

                if len(candidates) == 0:
                    if self.warnOnTraceViolation and not self.warningSent:
                        input("trace warning. Continue?")
                        self.warningSent = True

                    out = out - amlset([eta])
                    break

                aux = candidates & selectedIds
                if not bool(aux):
                    x = random.choice(tuple(candidates))
                    at = atoms[x]
                    selectedIds.add(x)
                    selected.append(at)
                else:
                    x = random.choice(tuple(aux))
                    at = atoms[x]

                out &= self.getTraceOfAtom(at)

        # ------------------------------------------------------------
        if not self.traceHelper is None:
            self.traceHelper.update(selected, self, True)

        logInfo(f"Trace simplification: {len(atoms)} to {len(selected)} > {xcount}")

        return selected

    def simplifyFromTerms(self, constants, atoms, generation):
        maxTrace = amlset([i for i in range(self.numIndicators())])
        tD = [None] * len(maxTrace)
        for i in maxTrace:
            tD[i] = amlset([])
        las = {}
        for c in constants:
            las[c] = amlset([])
        for x, at in enumerate(atoms):
            trace = self.getTraceOfAtom(at)
            out = maxTrace - trace
            for i in out:
                tD[i].add(x)
            for c in at.ucs & constants:
                las[c].add(x)

        # ------------------------------------------------------------

        termList = self.space.elements.copy()
        random.shuffle(termList)

        selectedIds = amlset([])

        for wt in termList:
            las_term = amlset()
            for c in wt.cset:
                las_term |= las[c]

            ttrace = wt.trace
            out = maxTrace - ttrace

            if not bool(out):
                if not bool(las_term & selectedIds):
                    if bool(las_term):
                        x = random.choice(tuple(las_term))
                        at = atoms[x]
                        selectedIds.add(x)

            while bool(out):
                eta = random.choice(tuple(out))
                candidates = tD[eta] & las_term
                if len(candidates) == 0:
                    if self.warnOnTraceViolation and not self.warningSent:
                        input("trace warning. Continue?")
                        self.warningSent = True

                    out = out - amlset([eta])
                    break

                aux = candidates & selectedIds
                if not bool(aux):
                    x = random.choice(tuple(candidates))
                    at = atoms[x]
                    selectedIds.add(x)
                else:
                    at = atoms[random.choice(tuple(aux))]

                out &= self.getTraceOfAtom(at)

        selected = []
        for x in selectedIds:
            selected.append(atoms[x])

        if not self.traceHelper is None:
            self.traceHelper.update(selected, self, True)

        logInfo("Trace simplification from term: {len(atoms)} to {len(selected)} >")

        return selected

    def enforcePositiveTraceConstraint(self, r, atoms, cmanager, epoch, generation):
        if r.positive == False:
            raise ValueError("Not a positive Duple")

        if r.wL is None:
            trL = self.getTraceOfTerm(r.L, atoms)
        else:
            trL = r.wL.trace

        if r.wH is None:
            trH = self.getTraceOfTerm(r.R, atoms)
            H = r.R
        else:
            trH = r.wH.trace
            H = r.wH.cset

        ret = []
        out = trH - trL
        lout = len(out)
        shift = -1
        if lout != 0:
            cH = list(H)
            if len(cH) == 0:
                raise ValueError("enforcePositiveTraceConstraint inconsistent")

            random.shuffle(cH)
            while lout != 0:
                if len(cH) == 0:
                    if self.warnOnTraceViolation and not self.warningSent:
                        self.warningSent = True
                        logError("enforcePositiveTraceConstraint trace error")

                    break

                c = cH[-1]
                del cH[-1]
                if shift == -1:
                    shift = len(self.indicators)
                out = self.getFreeTraceOfTermOverSubsetOfInidicators(LCSegment([c]), out, shift)  # fmt:skip
                if len(out) < lout:
                    lout = len(out)

                    at = Atom(epoch, generation, [c])
                    ret.append(at)

                    break

        return ret

    def enforceNegativeTraceConstraint(self, r, atoms, cmanager, epoch, generation):
        if r.positive == True:
            raise ValueError("Not a negative Duple")

        if r.wL is None:
            trL = self.getTraceOfTerm(r.L, atoms)
            L = r.L
        else:
            trL = r.wL.trace
            L = r.wL.cset

        if r.wH is None:
            trH = self.getTraceOfTerm(r.R, atoms)
            H = r.R
        else:
            trH = r.wH.trace
            H = r.wH.cset

        ret = []
        out = trH - trL
        lout = len(out)
        if lout == 0:
            extraC = list(L - H)
            if len(extraC) == 0:
                raise ValueError("enforceNegativeTraceConstraint inconsistent")

            random.shuffle(extraC)
            while lout == 0:
                if len(extraC) == 0:
                    raise ValueError("enforceNegativeTraceConstraint trace error")
                    break

                c = extraC[-1]
                del extraC[-1]
                out = trH - (trL & self.getFreeTraceOfConstant(c))
                if len(out) > 0:
                    lout = len(out)
                    at = Atom(epoch, generation, [c])
                    ret.append(at)

                    break

        return ret

    def enforceNegativeTraceConstraintByQuotient(self, r, atoms, cmanager, epoch, generation, las):  # fmt:skip
        if r.positive == True:
            raise TypeError("Not a negative Duple")

        if r.wL is None:
            trL = self.getTraceOfTerm(r.L, atoms)
            L = r.L
        else:
            trL = r.wL.trace
            L = r.wL.cset

        if r.wH is None:
            trH = self.getTraceOfTerm(r.R, atoms)
            H = r.R
        else:
            trH = r.wH.trace
            H = r.wH.cset

        ret = []
        out = trH - trL
        lout = len(out)
        if lout == 0:
            extraC = list(L - H)
            if len(extraC) == 0:
                raise ValueError("enforceNegativeTraceConstraintByQuotient inconsistent")  # fmt:skip

            random.shuffle(extraC)
            while lout == 0:
                if len(extraC) == 0:
                    if self.warnOnTraceViolation and not self.warningSent:
                        self.warningSent = True
                        raise ValueError("enforceNegativeTraceConstraintByQuotient trace error")  # fmt:skip

                    break

                c = extraC[-1]
                del extraC[-1]
                # -------------------------------------------------------------
                subAts = []
                maxSize = 0

                if c in las:
                    candidates = las[c].copy()
                else:
                    candidates = None

                while candidates:
                    at = random.choice(tuple(candidates))
                    candidates -= set([at])

                    ucs = at.ucs - H
                    if len(ucs) > 1:
                        if len(ucs) / len(at.ucs) >= maxSize:
                            nAt = Atom(epoch, generation, ucs)

                            out = trH - (trL & self.getTraceOfAtom(nAt))
                            if len(out) > 0:
                                lout = len(out)
                                if len(ucs) / len(at.ucs) > maxSize:
                                    maxSize = len(ucs) / len(at.ucs)
                                    subAts = []

                                if len(ucs) / len(at.ucs) == maxSize:
                                    subAts.append(nAt)

                ret.extend(subAts)
                # -------------------------------------------------------------
                if len(subAts) == 0:
                    out = trH - (trL & self.getFreeTraceOfConstant(c))
                    if len(out) > 0:
                        lout = len(out)

                        at = Atom(epoch, generation, [c])
                        ret.append(at)

        return ret

    @runCompiled()
    def storeTracesOfConstants(self, constants, atoms):
        logInfo("Traces of constants")
        for c in constants:
            self.constToStoredTraces[c] = [
                self.getTraceOfTerm(LCSegment([c]), atoms),
                self.period,
            ]


# -----------------------------------------------------------------------------


class Model:
    __slots__ = (
        "epoch",
        "generation",
        "cmanager",
        "atomization",
    )

    def __init__(self):
        self.epoch = 0
        self.generation = 0
        self.cmanager = ConstantManager()
        self.atomization = []


def enforce(
    model,
    disc,
    noDisc,
    lasH,
    tracer=None,
    removeRepetitions=False,
    calculateRedundancy=False,
    binary=False,
):
    model.epoch += 1
    if tracer == None:
        model.atomization = cross(
            disc,
            noDisc,
            lasH,
            model.atomization,
            model.cmanager.embeddingConstants,
            model.epoch,
            binary,
        )
    else:
        model.atomization = crossWithTraces(
            tracer, disc, noDisc, lasH, model.atomization, model
        )

    if removeRepetitions:
        model.atomization = removeRepeatedAtoms(model.atomization)

    if calculateRedundancy:
        embeddingConstants = model.cmanager.embeddingConstants
        if model.generation == 0:
            model.atomization = removeRedundantAtoms(
                model.atomization, embeddingConstants, True
            )
        else:
            model.atomization = removeRedundantAtomsSegregatingCurrentGeneration(
                model.atomization, embeddingConstants, model.generation
            )

    if config.Verbosity.Info >= config.verbosityLevel:
        printGSpectrum(model.atomization)
        printLSpectrum(model.atomization)
        printGENSpectrum(model.atomization)
