# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from .amlCompiledLibrary import ffi
from .amlCompiledLibrary import lib as caml
from .amlFastBitarrays import bitarray
import functools
import time

from .. import amlset
from ..io import logDebug, logInfo, logWarn, logError, logCrit
from .. import config
from .. import core as sc


def runCompiled(fast=True):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if fast and getattr(config.compiledFunc, func.__name__):
                return __func_dict[func.__name__](*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return inner

    return outer


# Functions


def freeTraceAll(space, tracer):
    if bool(tracer.discardedIndicators):
        raise ValueError("getFreeTraceOfTerm error discardedIndicators")

    logInfo("Calculating free traces")

    timing_start = time.time_ns()

    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not space.elements:
        sp_cset_constants = []
        sp_cset_constants_ptr = []
    elif isinstance(space.elements[0].cset, set):
        sp_cset_constants = [bitarray(wt.cset) for wt in space.elements]
        sp_cset_constants_ptr = [b._segment_handle[0] for b in sp_cset_constants]
    elif isinstance(space.elements[0].cset, bitarray):
        sp_cset_constants_ptr = [wt.cset._segment_handle[0] for wt in space.elements]
    else:
        raise TypeError("Must be of type 'set' or 'LCSegment'")

    sp_ftrace = [bitarray() for wt in space.elements]
    sp_ftrace_ptr = [b._segment_handle for b in sp_ftrace]
    sp_trace = [bitarray() for wt in space.elements]
    sp_trace_ptr = [b._segment_handle for b in sp_trace]

    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not tracer.indicators:
        tr_ind_constants = []
        tr_ind_constants_ptr = []
    elif isinstance(tracer.indicators[0], set):
        tr_ind_constants = [bitarray(ind) for ind in tracer.indicators]
        tr_ind_constants_ptr = [b._segment_handle for b in tr_ind_constants]
    elif isinstance(tracer.indicators[0], bitarray):
        tr_ind_constants_ptr = [ind._segment_handle for ind in tracer.indicators]
    else:
        raise TypeError("Must be of type 'set' or 'LCSegment'")

    if not tracer.atomIndicators:
        tr_atind_constants = []
        tr_atind_constants_ptr = []
    elif isinstance(tracer.atomIndicators[0].ucs, set):
        tr_atind_constants = [bitarray(atind.ucs) for atind in tracer.atomIndicators]
        tr_atind_constants_ptr = [b._segment_handle[0] for b in tr_atind_constants]
    elif isinstance(tracer.atomIndicators[0].ucs, bitarray):
        tr_atind_constants_ptr = [atind.ucs._segment_handle[0] for atind in tracer.atomIndicators]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    space_ptr = caml.linkSpace(
        len(space.elements),
        sp_cset_constants_ptr,
        sp_ftrace_ptr,
        sp_trace_ptr,
    )
    tracer_ptr = caml.linkTracer(
        len(tracer.indicators),
        tr_ind_constants_ptr,
        len(tracer.atomIndicators),
        tr_atind_constants_ptr,
    )

    timing_prev = time.time_ns()
    caml.freeTraceAll(
        space_ptr,
        tracer_ptr,
        bitarray.gsm,
    )
    timing_post = time.time_ns()

    for wt, ft in zip(space.elements, sp_ftrace):
        wt.freeTrace_ba = ft
        if amlset == set:
            wt.freeTrace = set(ft)
        elif amlset == bitarray:
            wt.freeTrace = ft

    caml.unlinkTracer(tracer_ptr)
    caml.unlinkSpace(space_ptr)

    timing_end = time.time_ns()
    timing_res_total = (timing_end - timing_start) / 1000_000_000
    timing_res_c = (timing_post - timing_prev) / 1000_000_000
    timing_res_faff = timing_res_total - timing_res_c
    logDebug(
        f"- ({timing_res_total:.3f}s : c {timing_res_c:.3f}s - py {timing_res_faff:.3f}s)"
    )


def traceAll(space, tracer, atomization):
    if bool(tracer.discardedIndicators):
        raise ValueError("getFreeTraceOfTerm error discardedIndicators")

    logInfo("Calculating traces")

    timing_start = time.time_ns()

    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not space.elements:
        sp_cset_constants = []
        sp_cset_constants_ptr = []
    elif isinstance(space.elements[0].cset, set):
        sp_cset_constants = [bitarray(wt.cset) for wt in space.elements]
        sp_cset_constants_ptr = [b._segment_handle[0] for b in sp_cset_constants]
    elif isinstance(space.elements[0].cset, bitarray):
        sp_cset_constants_ptr = [wt.cset._segment_handle[0] for wt in space.elements]
    else:
        raise TypeError("Must be of type 'set' or 'LCSegment'")

    sp_ftrace = [bitarray() for wt in space.elements]
    sp_ftrace_ptr = [b._segment_handle for b in sp_ftrace]
    sp_trace = [bitarray() for wt in space.elements]
    sp_trace_ptr = [b._segment_handle for b in sp_trace]

    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not tracer.indicators:
        tr_ind_constants = []
        tr_ind_constants_ptr = []
    elif isinstance(tracer.indicators[0], set):
        tr_ind_constants = [bitarray(ind) for ind in tracer.indicators]
        tr_ind_constants_ptr = [b._segment_handle for b in tr_ind_constants]
    elif isinstance(tracer.indicators[0], bitarray):
        tr_ind_constants_ptr = [ind._segment_handle for ind in tracer.indicators]
    else:
        raise TypeError("Must be of type 'set' or 'LCSegment'")

    if not tracer.atomIndicators:
        tr_atind_constants = []
        tr_atind_constants_ptr = []
    elif isinstance(tracer.atomIndicators[0].ucs, set):
        tr_atind_constants = [bitarray(atind.ucs) for atind in tracer.atomIndicators]
        tr_atind_constants_ptr = [b._segment_handle[0] for b in tr_atind_constants]
    elif isinstance(tracer.atomIndicators[0].ucs, bitarray):
        tr_atind_constants_ptr = [atind.ucs._segment_handle[0] for atind in tracer.atomIndicators]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not atomization:
        atomization_at_ucs_constants = []
        atomization_at_ucs_constants_ptr = []
    elif isinstance(atomization[0].ucs, set):
        atomization_at_ucs_constants = [bitarray(at.ucs) for at in atomization]
        atomization_at_ucs_constants_ptr = [b._segment_handle[0] for b in atomization_at_ucs_constants]  # fmt:skip
    elif isinstance(atomization[0].ucs, bitarray):
        atomization_at_ucs_constants_ptr = [at.ucs._segment_handle[0] for at in atomization]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    atomization_trace = [bitarray() for at in atomization]
    atomization_trace_ptr = [b._segment_handle for b in atomization_trace]

    space_ptr = caml.linkSpace(
        len(space.elements),
        sp_cset_constants_ptr,
        sp_ftrace_ptr,
        sp_trace_ptr,
    )
    tracer_ptr = caml.linkTracer(
        len(tracer.indicators),
        tr_ind_constants_ptr,
        len(tracer.atomIndicators),
        tr_atind_constants_ptr,
    )
    atomization_ptr = caml.linkAtomization(
        len(atomization),
        atomization_at_ucs_constants_ptr,
        atomization_trace_ptr,
    )

    timing_prev = time.time_ns()
    caml.traceAll(
        space_ptr,
        tracer_ptr,
        atomization_ptr,
        bitarray.gsm,
    )
    timing_post = time.time_ns()

    if amlset == set:
        for wt, tr in zip(space.elements, sp_trace):
            wt.trace = set(tr)
        for at, tr in zip(atomization, atomization_trace):
            at.trace = [set(tr), tracer.period]
    else:
        for wt, tr in zip(space.elements, sp_trace):
            wt.trace = tr
        for at, tr in zip(atomization, atomization_trace):
            at.trace = [tr, tracer.period]

    caml.unlinkAtomization(atomization_ptr)
    caml.unlinkTracer(tracer_ptr)
    caml.unlinkSpace(space_ptr)

    timing_end = time.time_ns()
    timing_res_total = (timing_end - timing_start) / 1000_000_000
    timing_res_c = (timing_post - timing_prev) / 1000_000_000
    timing_res_faff = timing_res_total - timing_res_c

    logDebug(
        f"> ({timing_res_total:.3f}s : c {timing_res_c:.3f}s - py {timing_res_faff:.3f}s)"
    )


def storeTracesOfConstants(tracer, constants, atomization):
    if bool(tracer.discardedIndicators):
        raise ValueError("getFreeTraceOfTerm error discardedIndicators")

    logInfo("Traces of constants")
    ### ATTENTION: This block cannot be extracted.
    ### If in a function, Python garbage collects pointers before they're used
    if not atomization:
        atomization_at_ucs_constants = []
        atomization_at_ucs_constants_ptr = []
    elif isinstance(atomization[0].ucs, set):
        atomization_at_ucs_constants = [bitarray(at.ucs) for at in atomization]
        atomization_at_ucs_constants_ptr = [b._segment_handle[0] for b in atomization_at_ucs_constants]  # fmt:skip
    elif isinstance(atomization[0].ucs, bitarray):
        atomization_at_ucs_constants_ptr = [at.ucs._segment_handle[0] for at in atomization]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    if amlset == set:
        atomization_trace = [bitarray(at.trace[0]) for at in atomization]
        atomization_trace_ptr = [b._segment_handle for b in atomization_trace]
    else:
        atomization_trace_ptr = [at.trace[0]._segment_handle for at in atomization]

    atomization_ptr = caml.linkAtomization(
        len(atomization),
        atomization_at_ucs_constants_ptr,
        atomization_trace_ptr,
    )

    traces = [bitarray() for c in constants]
    traces_ptr = [b._segment_handle for b in traces]

    if isinstance(sc.LCSegment([0]), amlset):
        raw_constants = list(constants)
    else:
        raise TypeError("Must be of type 'set' or 'CSegment'")

    caml.storeTracesOfConstants(
        traces_ptr,
        len(tracer.indicators) + len(tracer.atomIndicators),
        len(raw_constants),
        raw_constants,
        atomization_ptr,
        bitarray.gsm,
    )

    if amlset == set:
        for c, t in zip(raw_constants, traces):
            tracer.constToStoredTraces[c] = [set(t), tracer.period]
    else:
        for c, t in zip(raw_constants, traces):
            tracer.constToStoredTraces[c] = [t, tracer.period]

    caml.unlinkAtomization(atomization_ptr)


def considerPositiveDuples(tracer, pduples):
    tracer.period += 1
    #### ATTENTION: This block cannot be extracted.
    #### If in a function, Python garbage collects pointers before they're used
    if not tracer.indicators:
        tr_ind_constants = []
        tr_ind_constants_ptr = []
    elif isinstance(tracer.indicators[0], set):
        tr_ind_constants = [bitarray(ind) for ind in tracer.indicators]
        tr_ind_constants_ptr = [b._segment_handle for b in tr_ind_constants]
    elif isinstance(tracer.indicators[0], bitarray):
        tr_ind_constants_ptr = [ind._segment_handle for ind in tracer.indicators]
    else:
        raise TypeError("Indicators must be of type 'set' or 'LCSegment'")

    if not tracer.atomIndicators:
        tr_atind_constants = []
        tr_atind_constants_ptr = []
    elif isinstance(tracer.atomIndicators[0].ucs, set):
        tr_atind_constants = [bitarray(atind.ucs) for atind in tracer.atomIndicators]
        tr_atind_constants_ptr = [b._segment_handle[0] for b in tr_atind_constants]
    elif isinstance(tracer.atomIndicators[0].ucs, bitarray):
        tr_atind_constants_ptr = [atind.ucs._segment_handle[0] for atind in tracer.atomIndicators]  # fmt:skip
    else:
        raise TypeError("Indicators must be of type 'set' or 'UCSegment'")

    #### ATTENTION: This block cannot be extracted.
    #### If in a function, Python garbage collects pointers before they're used
    pduples = pduples
    if not pduples:
        rels_L_lcs_constants = []
        rels_L_lcs_constants_ptr = []
        rels_H_lcs_constants = []
        rels_H_lcs_constants_ptr = []
    elif isinstance(pduples[0].L, set):
        rels_L_lcs_constants = [bitarray(rel.L) for rel in pduples]
        rels_L_lcs_constants_ptr = [b._segment_handle[0] for b in rels_L_lcs_constants]
        rels_H_lcs_constants = [bitarray(rel.R) for rel in pduples]
        rels_H_lcs_constants_ptr = [b._segment_handle[0] for b in rels_H_lcs_constants]
    elif isinstance(pduples[0].L, bitarray):
        rels_L_lcs_constants_ptr = [rel.L._segment_handle[0] for rel in pduples]
        rels_H_lcs_constants_ptr = [rel.R._segment_handle[0] for rel in pduples]
    else:
        raise TypeError("Terms must be of type 'set' or 'LCSegment'")

    duples_hyp = [rel.hypothesis for rel in pduples]

    tracer_ptr = caml.linkTracer(
        len(tracer.indicators),
        tr_ind_constants_ptr,
        len(tracer.atomIndicators),
        tr_atind_constants_ptr,
    )
    rel_ptr = caml.linkDuple(
        len(pduples),
        rels_L_lcs_constants_ptr,
        rels_H_lcs_constants_ptr,
        duples_hyp,
    )
    ###

    caml.considerPositiveDuples(
        tracer_ptr,
        rel_ptr,
        bitarray.gsm,
    )

    ## Update tracer indicators
    if tracer.indicators:  # if emtpy, skip this block
        if amlset == set:
            if isinstance(tracer.indicators[0], set):
                for idx, ind_new in enumerate(tr_ind_constants):  # fmt:skip
                    tracer.indicators[idx] = ind_new
            else:
                raise TypeError("Indicators must be of type 'set' or 'LCSegment'")
        if amlset == bitarray:
            if isinstance(tracer.indicators[0], bitarray):
                pass
            else:
                raise TypeError("Indicators must be of type 'set' or 'LCSegment'")

    caml.unlinkDuple(rel_ptr)
    caml.unlinkTracer(tracer_ptr)


def simplifyFromConstants(tracer, constants, atoms, generation):
    maxTrace = amlset([i for i in range(tracer.numIndicators())])

    tD = [None] * len(maxTrace)
    for i in maxTrace:
        tD[i] = amlset([])

    las = {}
    for c in constants:
        las[c] = amlset([])

    for x, at in enumerate(atoms):
        trace = tracer.getTraceOfAtom(at)
        out = maxTrace - trace
        for i in out:
            tD[i].add(x)

        for c in at.ucs & constants:
            las[c].add(x)

    constantList = list(constants)
    random.shuffle(constantList)

    selectedIds = bitarray()
    selectedIds_ptr = selectedIds._segment_handle

    # las and constToStoredTraces are read in consecutive order following the order
    # (already shuffled) of the constantList
    b_las = []
    b_constToStoredTraces = []
    if amlset == set:
        for c in constantList:
            b_las.append(bitarray(las[c]))
            b_constToStoredTraces.append(bitarray(tracer.getStoredTraceOfConstant(c)))
    else:
        for c in constantList:
            b_las.append(las[c])
            b_constToStoredTraces.append(tracer.getStoredTraceOfConstant(c))
    b_las_ptr = [b._segment_handle[0] for b in b_las]
    b_constToStoredTraces_ptr = [b._segment_handle[0] for b in b_constToStoredTraces]

    if amlset == set:
        b_tD = [bitarray(s) for s in tD]
        b_tD_ptr = [b._segment_handle[0] for b in b_tD]
        b_at_traces = [bitarray(tracer.getTraceOfAtom(at)) for at in atoms]
        b_at_traces_ptr = [b._segment_handle[0] for b in b_at_traces]
    else:
        b_tD = tD
        b_tD_ptr = [b._segment_handle[0] for b in b_tD]
        b_at_traces = [tracer.getTraceOfAtom(at) for at in atoms]
        b_at_traces_ptr = [b._segment_handle[0] for b in b_at_traces]

    caml.simplifyFromConstants_inner_loop(
        selectedIds_ptr,
        len(constantList),
        b_las_ptr,
        b_tD_ptr,
        b_constToStoredTraces_ptr,
        len(atoms),
        b_at_traces_ptr,
        tracer.numIndicators(),
        random.randint(0, 4_294_967_295),
        bitarray.gsm,
    )

    selected = []
    for x in selectedIds:
        selected.append(atoms[x])

    if not tracer.traceHelper is None:
        tracer.traceHelper.update(selected, tracer, True)

    logInfo(f"Trace simplification: {len(atoms)} to {len(selected)}")

    return selected


def updateUnionModelWithSetOfPduples(embedder, pDuples):
    logInfo("Updating unionModel...", len(embedder.unionModel))

    embedder.vars.unionUpdates += 1

    atoms_to_keep = bitarray()
    atoms_to_keep_ptr = atoms_to_keep._segment_handle
    exclude_from_pinningterm = bitarray()
    exclude_from_pinningterm_ptr = exclude_from_pinningterm._segment_handle
    atoms_deleted = bitarray()
    atoms_deleted_ptr = atoms_deleted._segment_handle

    for at in embedder.unionModel:
        if at.unionUpdateEntrance == -1:
            at.unionUpdateEntrance = embedder.vars.unionUpdates

    if not embedder.unionModel:
        unionModel_at_ucs_constants = []
        unionModel_at_ucs_constants_ptr = []
    elif isinstance(embedder.unionModel[0].ucs, set):
        unionModel_at_ucs_constants = [bitarray(at.ucs) for at in embedder.unionModel]  # fmt:skip
        unionModel_at_ucs_constants_ptr = [b._segment_handle[0] for b in unionModel_at_ucs_constants]  # fmt:skip
    elif isinstance(embedder.unionModel[0].ucs, bitarray):
        unionModel_at_ucs_constants_ptr = [at.ucs._segment_handle[0] for at in embedder.unionModel]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    # trace is not used, we just need an empty bitarray
    unionModel_trace = [bitarray() for at in embedder.unionModel]
    unionModel_trace_ptr = [b._segment_handle for b in unionModel_trace]

    unionModel_ptr = caml.linkAtomization(
        len(embedder.unionModel),
        unionModel_at_ucs_constants_ptr,
        unionModel_trace_ptr,
    )

    # pduples = pDuples
    pDuplesSorted = pDuples.copy()
    pDuplesSorted.sort(key=lambda r: r.lastUnionUpdate)
    if not pDuplesSorted:
        rels_L_lcs_constants = []
        rels_L_lcs_constants_ptr = []
        rels_H_lcs_constants = []
        rels_H_lcs_constants_ptr = []
    elif isinstance(pDuplesSorted[0].L, set):
        rels_L_lcs_constants = [bitarray(rel.L) for rel in pDuplesSorted]
        rels_L_lcs_constants_ptr = [b._segment_handle[0] for b in rels_L_lcs_constants]
        rels_H_lcs_constants = [bitarray(rel.R) for rel in pDuplesSorted]
        rels_H_lcs_constants_ptr = [b._segment_handle[0] for b in rels_H_lcs_constants]
    elif isinstance(pDuplesSorted[0].L, bitarray):
        rels_L_lcs_constants_ptr = [rel.L._segment_handle[0] for rel in pDuplesSorted]
        rels_H_lcs_constants_ptr = [rel.R._segment_handle[0] for rel in pDuplesSorted]
    else:
        raise TypeError("Terms must be of type 'set' or 'LCSegment'")

    duples_hyp = [rel.hypothesis for rel in pDuplesSorted]

    rel_ptr = caml.linkDuple(
        len(pDuplesSorted),
        rels_L_lcs_constants_ptr,
        rels_H_lcs_constants_ptr,
        duples_hyp,
    )

    unionUpdateEntrance = [at.unionUpdateEntrance for at in embedder.unionModel]
    lastUnionUpdate = [r.lastUnionUpdate for r in pDuplesSorted]

    caml.updateUnionModelWithSetOfPduples(
        atoms_to_keep_ptr,
        atoms_deleted_ptr,
        exclude_from_pinningterm_ptr,
        unionModel_ptr,
        rel_ptr,
        unionUpdateEntrance,
        lastUnionUpdate,
        bitarray.gsm,
    )

    caml.unlinkDuple(rel_ptr)
    caml.unlinkAtomization(unionModel_ptr)

    take = []
    for idx in atoms_to_keep:
        take.append(embedder.unionModel[idx])

    deleted = []
    for idx in atoms_deleted:
        deleted.append(embedder.unionModel[idx])

    excluseFromPinning = []
    for idx in exclude_from_pinningterm:
        excluseFromPinning.append(embedder.unionModel[idx])

    for r in pDuples:
        if not r.hypothesis:
            r.lastUnionUpdate = embedder.vars.unionUpdates

    if len(take) + len(deleted) + len(excluseFromPinning) != len(embedder.unionModel):  # fmt:skip
        raise ValueError("updateUnionModelWithSetOfPduples count failed")

    logInfo("final unionModel size:", len(take))

    return take, excluseFromPinning, deleted


def calculateLowerAtomicSegments(space, atoms, las):
    element_las = [bitarray() for el in space.elements]
    element_las_ptr = [b._segment_handle for b in element_las]
    if amlset == set:
        element_cset = [bitarray(el.cset) for el in space.elements]
        element_cset_ptr = [b._segment_handle[0] for b in element_cset]
    else:
        element_cset_ptr = [el.cset._segment_handle[0] for el in space.elements]

    las_idx = []
    las_value = []
    las_value_ptr = []
    for k in sorted(las.keys()):
        las_idx.append(k)
        las_value.append(bitarray(las[k]))
        las_value_ptr.append(las_value[-1]._segment_handle[0])

    caml.calculateLowerAtomicSegments(
        element_las_ptr,
        element_cset_ptr,
        len(space.elements),
        las_value_ptr,
        las_idx,
        len(las),
        bitarray.gsm,
    )

    if amlset == set:
        for idx, el in enumerate(space.elements):
            el.las = set(element_las[idx])
    else:
        for idx, el in enumerate(space.elements):
            el.las = element_las[idx]


def crossAll(embedder, exampleSet):
    # ret_crossed_ptr
    ret_crossed = bitarray()
    ret_crossed_ptr = ret_crossed._segment_handle

    # ret_not_crossed_ptr
    ret_not_crossed = bitarray()
    ret_not_crossed_ptr = ret_not_crossed._segment_handle

    # ret_lastj
    ret_lastj = ffi.new("int[]", 1)

    # epoch
    ret_epoch = ffi.new("uint32_t[]", 1)
    ret_epoch[0] = embedder.model.epoch

    # atomization
    atomization = embedder.model.atomization
    if not atomization:
        atomization_at_ucs_constants = []
        atomization_at_ucs_constants_ptr = []
    elif isinstance(atomization[0].ucs, set):
        atomization_at_ucs_constants = [bitarray(at.ucs) for at in atomization]
        atomization_at_ucs_constants_ptr = [b._segment_handle[0] for b in atomization_at_ucs_constants]  # fmt:skip
    elif isinstance(atomization[0].ucs, bitarray):
        atomization_at_ucs_constants_ptr = [at.ucs._segment_handle[0] for at in atomization]  # fmt:skip
    else:
        raise TypeError("Must be of type 'set' or 'UCSegment'")

    tracer_get_trace = embedder.tracer.getTraceOfAtom
    atomization_trace = [bitarray(tracer_get_trace(at)) for at in atomization]
    atomization_trace_ptr = [b._segment_handle[0] for b in atomization_trace]

    atomization_epoch = [at.epoch for at in atomization]
    atomization_G = [at.G for at in atomization]
    atomization_gen = [at.gen for at in atomization]

    atomization_ptr = caml.linkAtomization_s(
        len(atomization),
        atomization_at_ucs_constants_ptr,
        atomization_trace_ptr,
        atomization_epoch,
        atomization_G,
        atomization_gen,
        bitarray.gsm,
    )

    # constants
    constants_in_trainingset = embedder.internals.constantsInTrainingSet
    cs_constants = bitarray(list(constants_in_trainingset))
    cs_constants_ptr = cs_constants._segment_handle[0]
    if not constants_in_trainingset:
        raise TypeError("sparse_crossing_embedder.internals.constantsInTrainingSet seems to be empty.")  # fmt:skip
    if not isinstance(constants_in_trainingset, amlset):
        raise TypeError("Terms must be of type 'set' or 'LCSegment'")

    constants_ptr = caml.linkCS_constants(cs_constants_ptr)

    pduples = exampleSet
    if not pduples:
        rels_L_lcs_constants = []
        rels_L_lcs_constants_ptr = []
        rels_H_lcs_constants = []
        rels_H_lcs_constants_ptr = []
    elif isinstance(pduples[0].L, set):
        rels_L_lcs_constants = [bitarray(rel.L) for rel in pduples]
        rels_L_lcs_constants_ptr = [b._segment_handle[0] for b in rels_L_lcs_constants]
        rels_H_lcs_constants = [bitarray(rel.R) for rel in pduples]
        rels_H_lcs_constants_ptr = [b._segment_handle[0] for b in rels_H_lcs_constants]
    elif isinstance(pduples[0].L, bitarray):
        rels_L_lcs_constants_ptr = [rel.L._segment_handle[0] for rel in pduples]
        rels_H_lcs_constants_ptr = [rel.R._segment_handle[0] for rel in pduples]
    else:
        raise TypeError("Terms must be of type 'set' or 'LCSegment'")
    duples_hyp = [rel.hypothesis for rel in pduples]
    rel_ptr = caml.linkDuple(
        len(pduples),
        rels_L_lcs_constants_ptr,
        rels_H_lcs_constants_ptr,
        duples_hyp,
    )

    # stored_trace_of_constant_ptr,
    constantsList = sorted(list(embedder.internals.constantsInTrainingSet))
    stored_trace_of_constant = [
        bitarray(embedder.tracer.getStoredTraceOfConstant(c))
        for c in constantsList
    ]
    stored_trace_of_constant_ptr = [b._segment_handle[0] for b in stored_trace_of_constant]  # fmt:skip

    # total_indicators_len,
    total_indicators_len = embedder.tracer.numIndicators()

    # ignore_crossing,
    ignore_crossing = [pRel.region == 0 for pRel in exampleSet]

    atomization_len = caml.crossAll(
        ret_crossed_ptr,
        ret_not_crossed_ptr,
        ret_lastj,
        ret_epoch,
        atomization_ptr,
        constants_ptr,
        rel_ptr,
        stored_trace_of_constant_ptr,
        total_indicators_len,
        ignore_crossing,
        {
            "calculate_redundancy": False,
            "remove_repetitions": embedder.params.removeRepetitions,
            "verbose": bool(config.Verbosity.Info >= config.verbosityLevel),
            "use_tracehelper": config.use_tracehelper,
            "simplify_threshold": embedder.params.simplify_threshold,
            "ignore_single_const_ucs": embedder.params.ignore_single_const_ucs,
        },
        random.randint(0, 4_294_967_295),
        bitarray.gsm,
    )

    # return
    at_ucs_constants = [bitarray() for _ in range(atomization_len)]
    at_ucs_constants_ptr = [b._segment_handle for b in at_ucs_constants]
    at_trace = [bitarray() for _ in range(atomization_len)]
    at_trace_ptr = [b._segment_handle for b in at_trace]

    at_epoch = ffi.new("uint32_t[]", atomization_len)
    at_G = ffi.new("uint32_t[]", atomization_len)
    at_gen = ffi.new("uint32_t[]", atomization_len)

    caml.extractAtomization_s(
        atomization_ptr,
        at_ucs_constants_ptr,
        at_trace_ptr,
        at_epoch,
        at_G,
        at_gen,
    )

    Atom = embedder.Atom
    cmanager = embedder.model.cmanager
    tracer_period = embedder.tracer.period
    atomization = [Atom(0, 0, set()) for _ in range(atomization_len)]
    for idx in range(atomization_len):
        if isinstance(atomization[0].ucs, set):
            atomization[idx].ucs = set(at_ucs_constants[idx])
        elif isinstance(atomization[0].ucs, bitarray):
            atomization[idx].ucs = at_ucs_constants[idx]
        else:
            raise TypeError("Atoms' ucs must be of type 'set' or 'LCSegment'")

        if amlset == set:
            atomization[idx].trace = [set(at_trace[idx]), tracer_period]
        else:
            atomization[idx].trace = [at_trace[idx], tracer_period]

        atomization[idx].epoch = at_epoch[idx]
        atomization[idx].gen = at_gen[idx]
        atomization[idx].G = at_G[idx]

    embedder.model.atomization = atomization

    embedder.model.epoch = ret_epoch[0]

    # clean-up
    caml.unlinkAtomization_s(atomization_ptr, bitarray.gsm)
    caml.unlinkCS_constants(constants_ptr)
    caml.unlinkDuple(rel_ptr)

    crossed = [exampleSet[idx] for idx in ret_crossed]
    notCrossed = [exampleSet[idx] for idx in ret_not_crossed]

    return crossed, notCrossed, ret_lastj[0]


def selectAllUsefulIndicators(self, nduplesIn, reversedNameDictionary):
    if bool(self.discardedIndicators):
        raise ValueError("selectAllUsefulIndicators error discardedIndicators")

    nrels = []

    ret_take = bitarray()
    ret_take_ptr = ret_take._segment_handle

    ret_duples_keep = bitarray()
    ret_duples_keep_ptr = ret_duples_keep._segment_handle

    if amlset == set:
        tr_discardedIndicators = bitarray(self.discardedIndicators)
        tr_discardedIndicators_ptr = tr_discardedIndicators._segment_handle[0]
    else:
        tr_discardedIndicators_ptr = self.discardedIndicators._segment_handle[0]

    rel_L_freeTrace_ptr = [nr.wL.freeTrace_ba._segment_handle[0] for nr in nduplesIn]
    rel_H_freeTrace_ptr = [nr.wH.freeTrace_ba._segment_handle[0] for nr in nduplesIn]

    duples_hyp = [nr.hypothesis for nr in nduplesIn]

    caml.selectAllUsefulIndicators(
        ret_take_ptr,
        ret_duples_keep_ptr,
        len(nduplesIn),
        tr_discardedIndicators_ptr,
        rel_L_freeTrace_ptr,
        rel_H_freeTrace_ptr,
        duples_hyp,
        bool(config.Verbosity.Info >= config.verbosityLevel),  # verbose
        bitarray.gsm,
    )

    nrels = [nduplesIn[nr_idx] for nr_idx in ret_duples_keep]

    self.discardedIndicators = amlset(
        [i for i in range(self.numIndicators()) if i not in ret_take]
    )

    logInfo(f"Number of indicators after selecting useful {len(ret_take)}")

    return nrels


def reduceIndicators(self, nduplesIn, reversedNameDictionary, singles):
    if amlset == set:
        tr_discardedIndicators = bitarray(self.discardedIndicators)
        tr_discardedIndicators_ptr = tr_discardedIndicators._segment_handle
    else:
        tr_discardedIndicators_ptr = self.discardedIndicators._segment_handle

    rel_L_freeTrace_ptr = [nr.wL.freeTrace_ba._segment_handle[0] for nr in nduplesIn]
    rel_H_freeTrace_ptr = [nr.wH.freeTrace_ba._segment_handle[0] for nr in nduplesIn]

    singles_ptr = singles._segment_handle

    caml.reduceIndicators(
        len(nduplesIn),
        self.numIndicators(),
        tr_discardedIndicators_ptr,
        rel_L_freeTrace_ptr,
        rel_H_freeTrace_ptr,
        singles_ptr,
        bool(config.Verbosity.Info >= config.verbosityLevel),  # verbose
        random.randint(0, 4_294_967_295),
        bitarray.gsm,
    )

    if amlset == set:
        self.discardedIndicators = amlset(tr_discardedIndicators)


class TraceHelper:
    def __init__(self, tracer, cmanager, constants, numIndicators):
        self.maxTrace = amlset([*range(numIndicators)])
        self.tD = [amlset() for _ in self.maxTrace]
        tD_pointers = [b._segment_handle for b in self.tD]

        self.atomIDs = amlset()
        self.constants = constants

        # constants
        constants_in_trainingset = constants
        self.cs_constants = bitarray(list(constants_in_trainingset))
        cs_constants_ptr = self.cs_constants._segment_handle[0]
        if not constants_in_trainingset:
            raise TypeError("sparse_crossing_embedder.internals.constantsInTrainingSet seems to be empty.")  # fmt:skip
        if not isinstance(constants_in_trainingset, amlset):
            raise TypeError("Terms must be of type 'set' or 'LCSegment'")

        constants_ptr = caml.linkCS_constants(cs_constants_ptr)
        self.constants_ptr = constants_ptr

        # TraceHelper init
        self.pointer = caml.TraceHelper_init_from_python(
            constants_ptr,
            numIndicators,
            self.atomIDs._segment_handle,
            tD_pointers,
            bitarray.gsm,
        )

        # Trace pointer
        if not tracer.indicators:
            tr_ind_constants = []
            tr_ind_constants_ptr = []
        elif isinstance(tracer.indicators[0], set):
            tr_ind_constants = [bitarray(ind) for ind in tracer.indicators]
            tr_ind_constants_ptr = [b._segment_handle for b in tr_ind_constants]
        elif isinstance(tracer.indicators[0], bitarray):
            tr_ind_constants_ptr = [ind._segment_handle for ind in tracer.indicators]
        else:
            raise TypeError("Must be of type 'set' or 'LCSegment'")

        if not tracer.atomIndicators:
            tr_atind_constants = []
            tr_atind_constants_ptr = []
        elif isinstance(tracer.atomIndicators[0].ucs, set):
            tr_atind_constants = [
                bitarray(atind.ucs) for atind in tracer.atomIndicators
            ]
            tr_atind_constants_ptr = [b._segment_handle[0] for b in tr_atind_constants]
        elif isinstance(tracer.atomIndicators[0].ucs, bitarray):
            tr_atind_constants_ptr = [atind.ucs._segment_handle[0] for atind in tracer.atomIndicators]  # fmt:skip
        else:
            raise TypeError("Must be of type 'set' or 'UCSegment'")

        self.tracer_ptr = caml.linkTracer(
            len(tracer.indicators),
            tr_ind_constants_ptr,
            len(tracer.atomIndicators),
            tr_atind_constants_ptr,
        )

    def __del__(self):
        caml.TraceHelper_delete_from_python(
            self.pointer,
            bitarray.gsm,
        )
        caml.unlinkCS_constants(self.constants_ptr)
        caml.unlinkTracer(self.tracer_ptr)

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

    def update(self, atomization, tracer, complete):
        if complete:
            atomization.sort(key=lambda at: at.ID)

        self.fastTable = atomization.copy()

        for at in atomization:
            if at.trace is None:
                at.trace = [bitarray(), 0]
        atomization_trace_ptr = [at.trace[0]._segment_handle for at in atomization]

        atomization_id = [at.ID for at in atomization]

        caml.TraceHelperPy_update(
            self.pointer,
            len(atomization),
            atomization_trace_ptr,
            atomization_id,
            complete,
            bitarray.gsm,
        )

        return amlset(atomization_id)


__func_dict = {
    "freeTraceAll": freeTraceAll,
    "traceAll": traceAll,
    "storeTracesOfConstants": storeTracesOfConstants,
    "considerPositiveDuples": considerPositiveDuples,
    "simplifyFromConstants": simplifyFromConstants,
    "updateUnionModelWithSetOfPduples": updateUnionModelWithSetOfPduples,
    "calculateLowerAtomicSegments": calculateLowerAtomicSegments,
    "crossAll": crossAll,
    "selectAllUsefulIndicators": selectAllUsefulIndicators,
    "reduceIndicators": reduceIndicators,
}
