# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from . import core as sc
from . import amlset
from . import config
from .io import logDebug, logInfo, logWarn, logError
from .aml_fast import aml_fast as af
from .aml_fast.aml_fast import runCompiled
from .aml_fast.amlFastBitarrays import bitarray

import random
import time


class params_full:
    def __init__(
        self,
        calculateRedundancy=False,
        removeRepetitions=False,
        sortDuples=False,
        binary=False,
    ):
        self.calculateRedundancy = calculateRedundancy
        self.removeRepetitions = removeRepetitions
        self.sortDuples = sortDuples
        self.binary = binary


class full_crossing_embedder:
    def __init__(self, model):
        self.model = model
        self.params = params_full()

    def sortDuplesBySolvability(self, atoms, duples):
        """
        Sort list of duples to improve efficiency in the full crossing
        """
        logInfo("Sorting duples")
        aux = []
        for r in duples:
            disc, outOfDisc, _ = sc.separateDiscriminant(r.L, r.R, atoms)
            hsize = len(sc.atomsIn(atoms, r.R))
            aux.append([len(disc), len(r.R), hsize, r])
        aux.sort(key=lambda rd: rd[0] * (rd[2] - 1))
        aux.sort(key=lambda rd: rd[1])
        return [rd[3] for rd in aux]

    def enforce(self, duples):
        rels = duples.copy()
        while len(rels) > 0:
            if self.params.sortDuples:
                rels = self.sortDuplesBySolvability(self.model.atomization, rels)
            r = rels.pop(0)
            (
                disc,
                nodisc,
                lasH,
            ) = sc.separateDiscriminant(r.L, r.R, self.model.atomization)
            if bool(disc):
                sc.enforce(
                    self.model,
                    disc,
                    nodisc,
                    lasH,
                    removeRepetitions=self.params.removeRepetitions,
                    calculateRedundancy=self.params.calculateRedundancy,
                    binary=self.params.binary,
                )


class params_sparse:
    def __init__(
        self,
        removeRepetitions=False,
        reductionByTraces=True,
        useSimplifyFromTerms=False,
        segregateByGeneration=True,
        enforceTraceConstraints=True,
        byQuotient=False,
        storePositives=True,
        useReduceIndicators=False,
        negativeIndicatorThreshold=0.1,  # -1 for no threshold
        staticConstants=False,
        simplify_threshold=1.5,
        ignore_single_const_ucs=True,
    ):
        self.removeRepetitions = removeRepetitions
        self.reductionByTraces = reductionByTraces
        self.useSimplifyFromTerms = useSimplifyFromTerms
        self.segregateByGeneration = segregateByGeneration
        # If enforceTraceConstraints is False a fresh atom is added to each constant every cycle.
        self.enforceTraceConstraints = enforceTraceConstraints
        self.byQuotient = byQuotient
        self.storePositives = storePositives
        self.useReduceIndicators = useReduceIndicators
        self.negativeIndicatorThreshold = negativeIndicatorThreshold
        self.staticConstants = staticConstants
        # Growing factor between crossings that would trigger a simplify action
        self.simplify_threshold = simplify_threshold
        # When computing the growth of an atomization, only account for atoms with more than one atom in their ucs
        self.ignore_single_const_ucs = ignore_single_const_ucs


class sparse_crossing_embedder_vars:
    def __init__(
        self,
        FPR=1,
        FNR=0,
        pcount=0,
        ncount=0,
        ndi=0,
        frac=1,
        unionModelFraction=0,
        unionUpdates=0,
    ):
        self.FPR = FPR
        self.FNR = FNR
        self.pcount = pcount
        self.ncount = ncount
        self.ndi = ndi
        self.frac = frac
        self.unionModelFraction = unionModelFraction
        self.unionUpdates = unionUpdates


class sparse_crossing_embedder_internals:
    def __init__(self):
        self.constantsInMasterAndTraining = sc.CSegment()
        self.constantsInTrainingSet = sc.CSegment()
        self.doCleanUp = False
        self.updateUnionModelWithStorePositives = False


class sparse_crossing_embedder:
    __slots__ = (
        "model",
        "params",
        "vars",
        "tracer",
        "unionModel",
        "lastUnionModel",
        "exampleSet",
        "counterexampleSet",
        "constantsInTrainingSet",
        "internals",
        "Atom",  # used in crossAll (fast)
    )

    def __init__(self, model):
        if not isinstance(model, sc.Model):
            raise ValueError("model parameter must be of type model")

        self.model = model
        self.params = params_sparse()
        self.vars = sparse_crossing_embedder_vars()
        self.internals = sparse_crossing_embedder_internals()
        self.tracer = None
        self.unionModel = []
        self.lastUnionModel = []

        self.exampleSet = []
        self.counterexampleSet = []

    def updateConstantsAndMaster(self, additionalDuples):
        constantsInTrainingSet = sc.CSegment()
        for r in self.exampleSet:
            constantsInTrainingSet |= r.L
            constantsInTrainingSet |= r.R

        for r in additionalDuples:
            constantsInTrainingSet |= r.L
            constantsInTrainingSet |= r.R

        for r in self.counterexampleSet:
            constantsInTrainingSet |= r.L
            constantsInTrainingSet |= r.R

        constantsInMasterAndTraining = constantsInTrainingSet.copy()
        for at in self.model.atomization:
            constantsInMasterAndTraining |= at.ucs

        thisEpochNewConsts = (
            constantsInTrainingSet - self.internals.constantsInTrainingSet
        )
        for c in thisEpochNewConsts:
            at = sc.Atom(self.model.epoch, self.model.generation, [c])
            self.model.atomization.append(at)

        maxc = -1
        for c in constantsInMasterAndTraining:
            maxc = max(maxc, c)

        if self.model.cmanager.lastDefConstantOrChain < maxc:
            raise ValueError("unknown constant")

        self.internals.constantsInTrainingSet = constantsInTrainingSet
        self.internals.doCleanUp = bool(
            constantsInMasterAndTraining - self.internals.constantsInMasterAndTraining
        )
        self.internals.constantsInMasterAndTraining = constantsInMasterAndTraining

    @runCompiled()
    def updateUnionModelWithSetOfPduples(self, pDuples):
        logInfo("Updating unionModel", len(self.unionModel))
        self.vars.unionUpdates += 1
        aux = []
        discarded = []
        excluseFromPinning = set()

        pDuplesSorted = pDuples.copy()
        pDuplesSorted.sort(key=lambda r: r.lastUnionUpdate)
        for at in self.unionModel:
            if at.unionUpdateEntrance == -1:
                at.unionUpdateEntrance = self.vars.unionUpdates

            take = True
            for r in pDuplesSorted:
                if at.unionUpdateEntrance > r.lastUnionUpdate:
                    if not at.ucs.isdisjoint(r.L):
                        if at.ucs.isdisjoint(r.R):
                            if not r.hypothesis:
                                take = False
                                discarded.append(at)
                            else:
                                excluseFromPinning.add(at)
                            break
                else:
                    break

            if take:
                aux.append(at)

        for r in pDuples:
            if not r.hypothesis:
                r.lastUnionUpdate = self.vars.unionUpdates

        logInfo("final unionModel size:", len(aux))

        return aux, excluseFromPinning, discarded

    def __reductionByTraces(self):
        if self.params.reductionByTraces:
            if self.params.useSimplifyFromTerms:
                self.model.atomization = self.tracer.simplifyFromTerms(
                    self.internals.constantsInTrainingSet,
                    self.model.atomization,
                    self.model.generation,
                )
            else:
                self.model.atomization = self.tracer.simplifyFromConstants(
                    self.internals.constantsInTrainingSet,
                    self.model.atomization,
                    self.model.generation,
                )
        # check leaks
        if isinstance(amlset, set):
            assert bitarray.howManyAreOut() == 0

    @runCompiled()
    def crossAll(self, exampleSet):
        # DO NOT SHUFFLE
        if self.params.ignore_single_const_ucs:
            lastNumberOfAtoms = len(
                [at for at in self.model.atomization if not at.isSizeOne()]
            )
        else:
            lastNumberOfAtoms = len(self.model.atomization)

        if config.use_tracehelper:
            self.tracer.traceHelper = af.TraceHelper(
                self.tracer,
                self.model.cmanager,
                self.internals.constantsInTrainingSet,
                self.tracer.numIndicators(),
            )

        lastj = 0
        crossed = []
        notCrossed = []

        j = 0
        for i, pRel in enumerate(exampleSet):
            disc, nodisc, lasH = sc.separateDiscriminant(
                pRel.L, pRel.R, self.model.atomization
            )
            if not bool(disc):
                if pRel.region != 0:
                    notCrossed.append(pRel)
                    j += 1
            else:
                sc.enforce(
                    self.model,
                    disc,
                    nodisc,
                    lasH,
                    tracer=self.tracer,
                    removeRepetitions=self.params.removeRepetitions,
                )
                if pRel.region != 0:
                    lastj = j
                    crossed.append(pRel)
                    j += 1

                if self.params.ignore_single_const_ucs:
                    numberOfAtoms = len(
                        [at for at in self.model.atomization if not at.isSizeOne()]
                    )
                else:
                    numberOfAtoms = len(self.model.atomization)

                modelGettingLarger = (
                    numberOfAtoms > self.params.simplify_threshold * lastNumberOfAtoms
                )

                if modelGettingLarger:
                    self.__reductionByTraces()
                    if self.params.ignore_single_const_ucs:
                        numberOfAtoms = len(
                            [at for at in self.model.atomization if not at.isSizeOne()]
                        )
                    else:
                        numberOfAtoms = len(self.model.atomization)
                    lastNumberOfAtoms = numberOfAtoms
                    logInfo(
                        f"{round(100 * i / len(exampleSet), 1)}% ",
                        end="",
                        flush=True,
                    )

        self.__reductionByTraces()
        self.tracer.traceHelper = None

        return crossed, notCrossed, lastj

    def internalEnforceAllPositives(self):
        self.Atom = sc.Atom
        timing_start = time.time_ns()
        crossed, notCrossed, lastj = self.crossAll(self.exampleSet)
        timing_end = time.time_ns()
        timing_res_total = (timing_end - timing_start) / 1000_000_000
        logInfo(f"CrossAll time: {timing_res_total:.3f}s")
        # check leaks
        if isinstance(amlset, set):
            assert bitarray.howManyAreOut() == 0

        toTheUnionModel = sc.atomizationCopy(self.model.atomization)

        self.lastUnionModel = self.unionModel.copy()
        for at in toTheUnionModel:
            at.unionUpdateEntrance = self.vars.unionUpdates
        self.unionModel.extend(toTheUnionModel)
        self.unionModel = sc.removeRepeatedAtoms(self.unionModel)  # fmt:skip

        if self.params.storePositives:
            self.exampleSet = crossed

            logInfo("Stored", len(self.exampleSet))
        else:
            self.exampleSet = []

    def externalExtendUnionModel(self, atSet):
        self.unionModel.extend(atSet)
        self.unionModel = sc.removeRepeatedAtoms(self.unionModel)  # fmt:skip
        self.internals.updateUnionModelWithStorePositives = True

    def enforce(self, pDuples, nDuples):
        self.vars.pcount += len([r for r in pDuples if r.region != 0])
        self.vars.ncount += len([r for r in nDuples if r.region != 0])

        # Update the union model
        updateDuples = pDuples.copy()
        if self.internals.updateUnionModelWithStorePositives:
            updateDuples.extend(self.exampleSet)
            self.internals.updateUnionModelWithStorePositives = False
        else:
            updateDuples.extend([r for r in self.exampleSet if r.hypothesis])
        self.unionModel, excluseFromPinning, _ = self.updateUnionModelWithSetOfPduples(
            updateDuples
        )

        aux = pDuples.copy()
        random.shuffle(aux)  # imprescindible for repeated batches
        aux.extend(self.exampleSet)
        self.exampleSet = aux

        self.counterexampleSet.extend(nDuples.copy())
        self.updateConstantsAndMaster([])

        if config.Verbosity.Info >= config.verbosityLevel:
            count = [0] * 100
            for rel in self.exampleSet:
                count[rel.region] += 1
            for region in range(len(count)):
                if count[region] > 0:
                    logInfo(f" + region  {region} > {count[region]}")
            count = [0] * 100
            for rel in self.counterexampleSet:
                count[rel.region] += 1
            for region in range(len(count)):
                if count[region] > 0:
                    logInfo(f" - region  {region} > {count[region]}")

        reversedNameDictionary = self.model.cmanager.getReversedNameDictionary()

        # Update tracer
        if self.tracer is None:
            warningSent = False
            period = 0
        else:
            warningSent = self.tracer.warningSent
            period = self.tracer.period

        self.tracer = sc.Tracer(period + 1, self.model.cmanager)
        self.tracer.warningSent = warningSent

        dupleRHS = frozenset([r.R for r in self.counterexampleSet])
        for R in dupleRHS:
            self.tracer.addNegativeH(R)

        CS = None
        if self.vars.unionModelFraction == 0:
            unionModel = [at for at in self.unionModel if at not in excluseFromPinning]
        else:
            unionModel = [at for at in self.unionModel if (at not in excluseFromPinning) and (at.isSizeOne() or random.randint(0, self.vars.unionModelFraction) == 0)]  # fmt:skip
        random.shuffle(unionModel)
        for at in unionModel:
            self.tracer.addPinningAtom(at)

        self.tracer.ensureIndicatorsAreUnique()
        self.tracer.considerPositiveDuples(self.exampleSet)
        self.tracer.ensureIndicatorsAreUnique()

        # -----------------------------------------------------------------

        space = sc.termSpace()
        logInfo("Preparing space class")
        for r in self.counterexampleSet:
            r.wL = space.add(r.L)
            r.wH = space.add(r.R)
        for r in self.exampleSet:
            r.wL = space.add(r.L)
            r.wH = space.add(r.R)
        space.freeTraceAll(self.tracer)

        # -----------------------------------------------------------------

        nDuples = self.counterexampleSet
        nDuples = self.tracer.selectAllUsefulIndicators(nDuples, reversedNameDictionary)  # fmt:skip
        if self.params.useReduceIndicators:
            self.tracer.reduceIndicators(nDuples, reversedNameDictionary, amlset())  # fmt:skip
        self.tracer.removeDiscardedIndicators()
        logInfo(f"Final number of indicators: {self.tracer.numIndicators()}")

        # -----------------------------------------------------------------

        self.vars.ndi = len(self.tracer.indicators)
        logInfo(f"Negative duple indicators {self.vars.ndi}")
        self.vars.frac = self.vars.ndi / max(1, self.tracer.numIndicators())

        # -----------------------------------------------------------------
        space.returnFreeTraces(self.tracer)
        # -----------------------------------------------------------------

        initial = []
        if not self.params.enforceTraceConstraints:
            initial = []
            atoms = self.model.atomization.copy()

            for c in self.internals.constantsInMasterAndTraining:
                at = sc.Atom(self.model.epoch, self.model.generation, [c])
                initial.append(at)
            # -----------------------------------------------------------------
            aux = atoms.copy()
            aux.extend(initial)
            space.traceAll(self.tracer, aux)
        else:
            cexamples = nDuples.copy()
            random.shuffle(cexamples)
            examples = self.exampleSet.copy()
            random.shuffle(examples)
            atoms = self.model.atomization.copy()

            # -----------------------------------------------------------------
            space.traceAll(self.tracer, atoms)
            # -----------------------------------------------------------------
            initial = self.traceClosure(space, examples, cexamples, atoms)

        for r in self.counterexampleSet:
            r.wL = None
            r.wH = None
        for r in self.exampleSet:
            r.wL = None
            r.wH = None

        if self.params.segregateByGeneration:
            self.model.generation += 1
            for at in initial:
                at.gen = self.model.generation

        self.model.atomization.extend(initial)
        self.model.atomization = sc.removeRepeatedAtoms(self.model.atomization)  # fmt:skip

        self.tracer.storeTracesOfConstants(
            self.internals.constantsInTrainingSet,
            self.model.atomization,
        )

        if self.params.useSimplifyFromTerms:
            self.tracer.space = space

        self.internalEnforceAllPositives()

        if config.Verbosity.Info >= config.verbosityLevel:
            sc.printLSpectrum(self.model.atomization)

        if self.params.negativeIndicatorThreshold != -1:
            if self.vars.frac < self.params.negativeIndicatorThreshold:
                self.vars.unionModelFraction += 1
            logInfo(
                f"Fraction of negative indicators: {self.vars.frac}, "
                f"Union model fraction: {self.vars.unionModelFraction}"
            )

        self.counterexampleSet = []

        if (not self.params.staticConstants) and self.internals.doCleanUp:
            duples = self.exampleSet.copy()
            duples.extend(self.counterexampleSet)
            self.model.cmanager.updateConstantsTo(
                self.model.atomization, self.unionModel, duples
            )

    def traceClosure(self, space, examples, cexamples, atoms):
        if self.params.byQuotient:
            logInfo(f"Calculating lower atomic segments")
            las = sc.calculateLowerAtomicSegment(
                self.model.atomization,
                self.internals.constantsInMasterAndTraining,
                False,
            )
        # ------------------------------------------------------------
        initial = []

        allEnforced = False
        while not allEnforced:
            allEnforced = True
            for rel in cexamples:
                if self.params.byQuotient:
                    aux = self.tracer.enforceNegativeTraceConstraintByQuotient(
                        rel,
                        atoms,
                        self.model.cmanager,
                        self.model.epoch,
                        self.model.generation,
                        las,
                    )
                else:
                    aux = self.tracer.enforceNegativeTraceConstraint(
                        rel,
                        atoms,
                        self.model.cmanager,
                        self.model.epoch,
                        self.model.generation,
                    )

                if len(aux) > 0:
                    logDebug("-", len(aux), " ", end="", flush=True)
                    allEnforced = False
                    initial.extend(aux)
                    logDebug("<", end="", flush=True)
                    space.updateTraces(self.tracer, aux)
                    logDebug(">", end="", flush=True)

            logDebug("--")

            for rel in examples:
                aux = self.tracer.enforcePositiveTraceConstraint(
                    rel,
                    atoms,
                    self.model.cmanager,
                    self.model.epoch,
                    self.model.generation,
                )
                if len(aux) > 0:
                    logDebug(f"+ {len(aux)}  ", end="", flush=True)
                    allEnforced = False
                    initial.extend(aux)
                    space.updateTraces(self.tracer, aux)
            logDebug("--")

        initial = sc.removeRepeatedAtoms(initial)

        logInfo(f"Traces enforced with {len(initial)} atoms")
        return initial

    def testAccuracy(self, rels):
        """
        Compute FPR and FNR.

        All terms need to have their lower atomic segment calculated by
        termSpace.calculateLowerAtomicSegments()

        Vars:
        duples (List[duples])  : list of positive and negative duples
        """
        falsePositives = 0
        falseNegatives = 0
        numPositives = 0
        numNegatives = 0
        for r in rels:
            disc = r.wL.las - r.wH.las

            if r.positive:
                numPositives += 1
                failsPositive = disc
                if failsPositive:
                    falseNegatives += 1
            else:
                numNegatives += 1
                failsNegative = not (disc)
                if failsNegative:
                    falsePositives += 1

        FPR = -1
        FNR = -1
        if numNegatives > 0:
            FPR = falsePositives / numNegatives
        if numPositives > 0:
            FNR = falseNegatives / numPositives

        return FPR, FNR

    def test(self, duples, region=-1):
        """
        Report FPR and FNR as a string

        Vars:
        duples (List[duples])  : list of positive and negative duples
        region (int, optional) : if defined only duples in that region
                                 are considered
        """

        if region != -1:
            duples = [r for r in duples if r.region == region]

        if len(duples) > 0:
            self.vars.FPR, self.vars.FNR = self.testAccuracy(duples)  # fmt:skip
            return f"FPR: {self.vars.FPR}  FNR: {self.vars.FNR}"
        else:
            return "No data"

    def setAtomization(self, atomization):
        self.model.atomization = atomization
