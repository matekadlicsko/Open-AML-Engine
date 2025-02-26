// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include "aml_fast.h"

#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bitarrays.h"
#include "cbar.h"

#define IGNORE_ERROR_B true

#define QUOTIENT(a, b) (a / b + (a % b != 0 ? 1 : 0))
#define MIN(X, Y) (((X) < (Y)) ? (X) : (Y))
#define MAX(X, Y) (((X) > (Y)) ? (X) : (Y))

#define __maybe_unused __attribute__((unused))

#define IF_THEN_ABORT(check, message)             \
    {                                             \
        if (check) {                              \
            const char* COLOR_RED = "\033[1;31m"; \
            const char* COLOR_RESET = "\033[0m";  \
            printf("%s", COLOR_RED);              \
            printf(message);                      \
            printf("%s", COLOR_RESET);            \
            printf("\n");                         \
            abort();                              \
        }                                         \
    }

#define IF_THEN_WARN(check, message)              \
    {                                             \
        if (check) {                              \
            const char* COLOR_RED = "\033[1;31m"; \
            const char* COLOR_RESET = "\033[0m";  \
            printf("%s", COLOR_RED);              \
            printf(message);                      \
            printf("%s", COLOR_RESET);            \
            printf("\n");                         \
        }                                         \
    }

const uint32_t MAX_MEMBLOCK_SIZE = 16000000;

struct CrossAll_Params {
    bool calculate_redundancy;
    bool remove_repetitions;
    bool verbose;
    bool use_tracehelper;
    float simplify_threshold;
    bool ignore_single_const_ucs;
};

typedef struct Space {
    LCS* cset;
    segmentHead*** freeTrace;
    segmentHead*** trace;
    uint32_t len;
} Space;

typedef struct Duples {
    LCS* H;
    LCS* L;
    int* hyp;
    uint32_t len;
} Duples;

// ----------------------------

// Perform binary search of value in array and returns its index.
// Return length if the value cannot be found in array.
// Array must be sorted.
static uint32_t array_index(uint32_t array[], uint32_t length, uint32_t value)
{
    if (length == 0) return 0;
    if (value < length && array[value] == value) return value;  // short-circuit

    int32_t l = 0;
    int32_t r = length - 1;

    while (l <= r) {
        int32_t m = (r + l) / 2;
        if (array[m] < value) {
            l = m + 1;
        } else if (array[m] > value) {
            r = m - 1;
        } else {
            return m;
        }
    }
    return length;
}

static __maybe_unused void as_array(segmentHead* segment, uint32_t* arr)
{
    segmentReader reader;
    segmentReader_set(&reader, segment);
    uint32_t idx = 0;
    while (segmentReader_nextItem(&reader)) {
        arr[idx++] = segmentReader_currentItem(&reader);
    }
    assert(idx == segment_countItems(segment));
}

static __maybe_unused void shuffle_array(uint32_t array[], uint32_t length)
{
    if (length > 1) {
        for (int i = length - 1; i > 0; --i) {
            int j = rand() % (i + 1);
            int temp = array[j];
            array[j] = array[i];
            array[i] = temp;
        }
    }
}

// ----------------------------

Space* linkSpace(uint32_t sp_len, segmentHead* sp_cset_constants[], segmentHead** sp_ftrace[], segmentHead** sp_trace[])
{
    Space* space = malloc(sizeof(Space));

    space->len = sp_len;
    space->cset = malloc(sp_len * sizeof(LCS));

    space->freeTrace = malloc(sp_len * sizeof(segmentHead**));
    space->trace = malloc(sp_len * sizeof(segmentHead**));

    for (uint32_t k = 0; k < sp_len; ++k) {
        space->cset[k].constants = sp_cset_constants[k];
    }

    for (uint32_t k = 0; k < sp_len; ++k) {
        if (*sp_ftrace[k] != NULL) abort();
        space->freeTrace[k] = sp_ftrace[k];
        if (*sp_trace[k] != NULL) abort();
        space->trace[k] = sp_trace[k];
    }

    return space;
}

void unlinkSpace(Space* space)
{
    free(space->cset);
    free(space->freeTrace);
    free(space->trace);
    free(space);
}

Tracer* linkTracer(
    uint32_t tr_ind_len, segmentHead** tr_ind_constants[], uint32_t tr_atind_len, segmentHead* tr_atind_constants[])
{
    Tracer* tracer = malloc(sizeof(Tracer));

    tracer->indicators_len = tr_ind_len;
    tracer->indicators = malloc(tr_ind_len * sizeof(LCS));

    tracer->atomIndicators_len = tr_atind_len;
    tracer->atomIndicators = malloc(tr_atind_len * sizeof(UCS));

    for (uint32_t k = 0; k < tr_ind_len; ++k) {
        tracer->indicators[k].constants = tr_ind_constants[k];
    }
    for (uint32_t k = 0; k < tr_atind_len; ++k) {
        tracer->atomIndicators[k].constants = tr_atind_constants[k];
    }

    return tracer;
}

void unlinkTracer(Tracer* tracer)
{
    free(tracer->indicators);
    free(tracer->atomIndicators);
    free(tracer);
}

Atomization* linkAtomization(
    uint32_t atomization_len, segmentHead* atomization_at_ucs_constants[], segmentHead** atomization_at_trace[])
{
    Atomization* atomization = malloc(sizeof(Atomization));
    atomization->len = atomization_len;
    atomization->atoms = malloc(atomization_len * sizeof(Atom));

    for (uint32_t k = 0; k < atomization_len; ++k) {
        atomization->atoms[k].trace = atomization_at_trace[k];
        atomization->atoms[k].ucs.constants = atomization_at_ucs_constants[k];
    }

    return atomization;
}

void unlinkAtomization(Atomization* atomization)
{
    free(atomization->atoms);
    free(atomization);
}

Atomization_s* linkAtomization_s(
    uint32_t atomization_len, segmentHead* atomization_at_ucs_constants[], segmentHead* atomization_at_trace[],
    uint32_t atomization_epoch[], uint32_t atomization_G[], uint32_t atomization_gen[], generalSegmentManager* gsm)
{
    Atomization_s* atomization = malloc(sizeof(Atomization_s));

    atomization->len = atomization_len;
    atomization->atoms = calloc(atomization_len, sizeof(Atom_s));

    for (uint32_t k = 0; k < atomization_len; ++k) {
        segment_clone_to(&atomization->atoms[k].trace, atomization_at_trace[k], gsm);
        segment_clone_to(&atomization->atoms[k].ucs.constants, atomization_at_ucs_constants[k], gsm);
        atomization->atoms[k].epoch = atomization_epoch[k];
        atomization->atoms[k].G = atomization_G[k];
        atomization->atoms[k].gen = atomization_gen[k];
    }

    return atomization;
}

void unlinkAtomization_s(Atomization_s* atomization, generalSegmentManager* gsm)
{
    for (uint32_t k = 0; k < atomization->len; ++k) {
        generalSegmentManager_returnSegment(gsm, &atomization->atoms[k].ucs.constants);
        generalSegmentManager_returnSegment(gsm, &atomization->atoms[k].trace);
    }
    free(atomization->atoms);
    free(atomization);
}

void extractAtomization_s(
    Atomization_s* atomization, segmentHead** at_ucs_constants[], segmentHead** at_trace[], uint32_t at_epoch[],
    uint32_t at_G[], uint32_t at_gen[])
{
    for (uint32_t idx = 0; idx < atomization->len; ++idx) {
        assert(!*at_ucs_constants[idx]);
        assert(!*at_trace[idx]);

        *at_ucs_constants[idx] = atomization->atoms[idx].ucs.constants;
        atomization->atoms[idx].ucs.constants = NULL;

        *at_trace[idx] = atomization->atoms[idx].trace;
        atomization->atoms[idx].trace = NULL;

        at_epoch[idx] = atomization->atoms[idx].epoch;
        at_G[idx] = atomization->atoms[idx].G;
        at_gen[idx] = atomization->atoms[idx].gen;
    }
}

CS* linkCS_constants(segmentHead* cs_constants)
{
    CS* cs = calloc(1, sizeof(CS));
    cs->constants = cs_constants;
    cs->len = segment_countItems(cs_constants);
    cs->constants_as_array = malloc(cs->len * sizeof(uint32_t));
    as_array(cs_constants, cs->constants_as_array);
    return cs;
}

void unlinkCS_constants(CS* cs)
{
    free(cs->constants_as_array);
    free(cs);
}

static LCS* linkLCS(uint32_t lcs_len, segmentHead* lcs_constants[])
{
    LCS* lcs = calloc(lcs_len, sizeof(LCS));
    for (uint32_t k = 0; k < lcs_len; ++k) {
        lcs[k].constants = lcs_constants[k];
    }

    return lcs;
}

static void unlinkLCS(LCS* lcs) { free(lcs); }

Duples* linkDuple(uint32_t rel_len, segmentHead* L_constants[], segmentHead* H_constants[], int rel_hyp[])
{
    Duples* rels = calloc(1, sizeof(Duples));
    rels->L = linkLCS(rel_len, L_constants);
    rels->H = linkLCS(rel_len, H_constants);
    rels->hyp = (int*)malloc(rel_len * sizeof(int));
    for (uint32_t pr = 0; pr < rel_len; ++pr) {
        rels->hyp[pr] = rel_hyp[pr];
    }
    rels->len = rel_len;

    return rels;
}

void unlinkDuple(Duples* rels)
{
    unlinkLCS(rels->L);
    unlinkLCS(rels->H);
    free(rels->hyp);
    free(rels);
}

static bool isDisjoint(const UCS* ucs, const LCS* lcs)
{
    if (!segment_isDisjoint(ucs->constants, lcs->constants)) {
        return false;
    }
    return true;
}

static bool isSubset(const LCS* left, const LCS_mut* right)
{
    return segment_inSegment(left->constants, *right->constants);
}

static segmentHead* getFreeTraceOfTerm(const LCS* cset, const Tracer* tracer, generalSegmentManager* gsm)
{
    segmentHead* ret = NULL;
    segmentWriter writer;
    segmentWriter_set(&writer, &ret, gsm);

    for (uint32_t k = 0; k < tracer->indicators_len; ++k) {
        if (isSubset(cset, &tracer->indicators[k])) {
            segmentWriter_addItem(&writer, k);
        }
    }

    uint32_t shift = tracer->indicators_len;
    for (uint32_t k = 0; k < tracer->atomIndicators_len; ++k) {
        if (isDisjoint(&tracer->atomIndicators[k], cset)) {
            segmentWriter_addItem(&writer, k + shift);
        }
    }

    return ret;
}

void freeTraceAll(Space* space, Tracer* tracer, generalSegmentManager* gsm)
{
    /* With tiling to avoid cache misses */
    uint32_t tileSize = 5000;
    uint32_t blocks = (int)((tracer->indicators_len + tileSize - 1) / tileSize);
    for (uint32_t b = 0; b < blocks; ++b) {
        #pragma omp parallel for
        for (uint32_t el = 0; el < space->len; ++el) {
            const LCS* cset = &space->cset[el];
            segmentWriter writer;
            int __maybe_unused iH = -1;
            int __maybe_unused unit = -1;
            uint32_t i = b * tileSize;
            uint32_t f = MIN(tracer->indicators_len, (b + 1) * tileSize);
            if (b == 0) {
                if (*space->freeTrace[el] != NULL) abort();
            }
            segmentWriter_set(&writer, space->freeTrace[el], gsm);
            for (uint32_t k = i; k < f; ++k) {
                if (isSubset(cset, &tracer->indicators[k])) {
                    segmentWriter_addItemRepeatedExclusiveUse(&writer, k, &iH, &unit);
                }
            }
        }
    }

    uint32_t shift = tracer->indicators_len;
    blocks = (int)((tracer->atomIndicators_len + tileSize - 1) / tileSize);
    for (uint32_t b = 0; b < blocks; ++b) {
        #pragma omp parallel for
        for (uint32_t el = 0; el < space->len; ++el) {
            const LCS* cset = &space->cset[el];
            segmentWriter writer;
            int __maybe_unused iH = -1;
            int __maybe_unused unit = -1;
            uint32_t i = b * tileSize;
            uint32_t f = MIN(tracer->atomIndicators_len, (b + 1) * tileSize);
            segmentWriter_set(&writer, space->freeTrace[el], gsm);
            for (uint32_t k = i; k < f; ++k) {
                if (isDisjoint(&tracer->atomIndicators[k], cset)) {
                    segmentWriter_addItemRepeatedExclusiveUse(&writer, k + shift, &iH, &unit);
                }
            }
        }
    }
}

static segmentHead* getFreeTraceOfIsolatedConstant(
    const Tracer* tracer, const uint32_t constant_idx, generalSegmentManager* gsm)
{
    LCS* constant = calloc(1, sizeof(LCS));
    segment_addItem(&constant->constants, constant_idx, gsm);

    segmentHead* trace = getFreeTraceOfTerm(constant, tracer, gsm);
    generalSegmentManager_returnSegment(gsm, &constant->constants);
    free(constant);
    return trace;
}

void calculateTraceOfAtom(const Tracer* tracer, Atom* at, generalSegmentManager* gsm)
{
    if (*at->trace != NULL) {
        const char* COLOR_RED = "\033[1;31m";
        const char* COLOR_RESET = "\033[0m";
        printf("%s", COLOR_RED);
        printf("Caller must ensure atom trace is empty");
        printf("%s", COLOR_RESET);
        printf("\n");
        abort();
    }

    segmentWriter writer;
    segmentWriter_set(&writer, at->trace, gsm);

    segmentReader reader;
    segmentReader_set(&reader, at->ucs.constants);
    while (segmentReader_nextItem(&reader)) {
        uint32_t constant_idx = segmentReader_currentItem(&reader);
        segmentHead* constant_trace = getFreeTraceOfIsolatedConstant(tracer, constant_idx, gsm);
        segmentWriter_addSegmentNoReturn(&writer, constant_trace);
        generalSegmentManager_returnSegment(gsm, &constant_trace);
    }
}

static segmentHead* getTraceOfTerm(
    const LCS* term, const Tracer* tracer, Atomization* atomization, generalSegmentManager* gsm)
{
    segmentHead* trace = NULL;
    segmentWriter writer;
    segmentWriter_set(&writer, &trace, gsm);

    uint32_t num_indicators = tracer->indicators_len + tracer->atomIndicators_len;
    for (uint32_t j = 0; j < num_indicators; ++j) {
        segmentWriter_addItem(&writer, j);
    }

    for (uint32_t k = 0; k < atomization->len; ++k) {
        if (!isDisjoint(&atomization->atoms[k].ucs, term)) {
            segmentWriter_intersectSegmentNoReturn(&writer, *atomization->atoms[k].trace);
        }
    }

    return trace;
}

void traceAll(Space* space, Tracer* tracer, Atomization* atomization, generalSegmentManager* gsm)
{
    #pragma omp parallel for
    for (uint32_t k = 0; k < atomization->len; ++k) {
        calculateTraceOfAtom(tracer, &atomization->atoms[k], gsm);
    }

    #pragma omp parallel for
    for (uint32_t k = 0; k < space->len; ++k) {
        if (*space->trace[k] != NULL) abort();
        *space->trace[k] = getTraceOfTerm(&space->cset[k], tracer, atomization, gsm);
    }
}

void storeTracesOfConstants(
    segmentHead*** traces, uint32_t total_num_indicators, uint32_t constants_len, int constants[],
    Atomization* atomization, generalSegmentManager* gsm)
{
    {
        segmentHead* all_indicators = NULL;
        {
            segmentWriter writer;
            segmentWriter_set(&writer, &all_indicators, gsm);
            for (uint32_t j = 0; j < total_num_indicators; ++j) {
                segmentWriter_addItem(&writer, j);
            }
        }

        #pragma omp parallel for
        for (uint32_t c_idx = 0; c_idx < constants_len; ++c_idx) {
            LCS constant;
            constant.constants = NULL;
            segment_addItem(&constant.constants, constants[c_idx], gsm);

            {  // getTraceOfTerm
                segmentWriter writer;
                segmentWriter_set(&writer, traces[c_idx], gsm);
                segmentWriter_cloneFrom(&writer, all_indicators);

                for (uint32_t k = 0; k < atomization->len; ++k) {
                    if (!isDisjoint(&atomization->atoms[k].ucs, &constant)) {
                        segmentWriter_intersectSegmentNoReturn(&writer, *atomization->atoms[k].trace);
                    }
                }
            }
            generalSegmentManager_returnSegment(gsm, &constant.constants);
        }
        generalSegmentManager_returnSegment(gsm, &all_indicators);
    }
}

void considerPositiveDuples(Tracer* tr, Duples* duples, generalSegmentManager* gsm)
{
    uint32_t duples_len = duples->len;
    LCS* duplesL = duples->L;
    LCS* duplesH = duples->H;

    #pragma omp parallel for
    for (uint32_t i = 0; i < tr->indicators_len; ++i) {
        bool used[duples_len];
        for (uint32_t k = 0; k < duples_len; ++k) used[k] = false;

        segmentWriter writer;
        segmentWriter_set(&writer, tr->indicators[i].constants, gsm);
        uint32_t end = duples_len;
        uint32_t pr = 0;
        for (uint32_t bpr = 0; bpr < end; ++bpr) {
            pr = bpr % duples_len;
            if (used[pr] == false) {
                if (isSubset(&duplesH[pr], &tr->indicators[i])) {
                    used[pr] = true;
                    if (segmentWriter_addSegment(&writer, duplesL[pr].constants)) {
                        end = bpr + duples_len;
                    }
                }
            }
        }
    }
}

/* --- */

/* Fill segment with continues items from index beg to index end */
static void segment_fillWithRange(segmentHead** segment, int beg, int end, generalSegmentManager* gsm)
{
    int __maybe_unused iH = -1;
    int __maybe_unused unit = -1;
    segmentWriter writer;
    segmentWriter_set(&writer, segment, gsm);
    for (int idx = beg; idx < end; ++idx) {
        segmentWriter_addItemRepeatedExclusiveUse(&writer, idx, &iH, &unit);
    }
}

static int segment_chooseItemIn_maxSizeKnown(segmentHead* out, int maxvalue, int* buffer)
{
    segmentReader reader;
    segmentReader_set(&reader, out);
    int count = 0;
    int choose = rand() % maxvalue;
    while (segmentReader_nextItem(&reader)) {
        buffer[count] = segmentReader_currentItem(&reader);
        if (count == choose) return buffer[count];
        count++;
    }
    IF_THEN_ABORT(count == 0, "Segment_chooseItemIn_maxSizeKnown: segment must not be empty");
    return buffer[choose % count];
}

int segment_chooseItemIn_withBuffer(segmentHead* out, int* buffer)
{
    return segment_chooseItemIn_maxSizeKnown(out, segment_countItems(out), buffer);
}

/* las and constToStoredTraces are read in consecutive order following the order
 * (already shuffled) of the list of constants */
void simplifyFromConstants_inner_loop(
    segmentHead** ret_selected, const uint32_t constants_len, segmentHead* las[], segmentHead* tD[],
    segmentHead* constToStoredTraces[], const uint32_t atomization_len, segmentHead* atomization_traces[],
    const uint32_t total_indicators_len, generalSegmentManager* gsm)
{
    segmentHead* maxTrace = NULL;
    segment_fillWithRange(&maxTrace, 0, total_indicators_len, gsm);

    uint32_t buffer_size = total_indicators_len > atomization_len ? total_indicators_len : atomization_len;
    int buffer[buffer_size];

    segmentHead* out = NULL;
    for (uint32_t c_idx = 0; c_idx < constants_len; ++c_idx) {
        segment_subtract_to(&out, maxTrace, constToStoredTraces[c_idx], gsm);

        // leave at least one atom per constant
        if (!out) {
            if (segment_isDisjoint(las[c_idx], *ret_selected)) {
                if (las[c_idx]) {
                    int at_idx = segment_chooseItemIn_withBuffer(las[c_idx], buffer);
                    segment_addItem(ret_selected, at_idx, gsm);
                }
            }
        }

        while (out) {
            int eta_idx = segment_chooseItemIn_withBuffer(out, buffer);

            segmentHead* candidates = NULL;
            segment_intersect_to(&candidates, tD[eta_idx], las[c_idx], gsm);

            if (IGNORE_ERROR_B) {
                IF_THEN_WARN(!candidates, "Simplify From Constants: Trace error B");
                if (!candidates) {
                    segment_removeItem(&out, eta_idx, gsm);
                    break;
                }
            } else {
                IF_THEN_ABORT(!candidates, "Simplify From Constants: Trace error B");
            }

            segmentHead* aux = NULL;
            segment_intersect_to(&aux, candidates, *ret_selected, gsm);
            {
                int at_idx;
                if (!aux) {
                    at_idx = segment_chooseItemIn_withBuffer(candidates, buffer);
                    segment_addItem(ret_selected, at_idx, gsm);
                } else {
                    at_idx = segment_chooseItemIn_withBuffer(aux, buffer);
                }
                segment_intersect(&out, atomization_traces[at_idx], gsm);
            }
            generalSegmentManager_returnSegment(gsm, &aux);
            generalSegmentManager_returnSegment(gsm, &candidates);
        }
    }
    generalSegmentManager_returnSegment(gsm, &out);
    generalSegmentManager_returnSegment(gsm, &maxTrace);
}

void updateUnionModelWithSetOfPduples(
    segmentHead** atoms_to_keep, segmentHead** atoms_deleted, segmentHead** exclude_from_pinningterm,
    Atomization* unionModel, Duples* duples, int64_t* unionUpdateEntrance, int64_t* lastUnionUpdate,
    generalSegmentManager* gsm)
{
    if (*atoms_to_keep) abort();
    if (*atoms_deleted) abort();
    if (*exclude_from_pinningterm) abort();

    uint32_t threads = 64 * 3 * 5;
    uint32_t loadsize = unionModel->len / threads + 1;
    uint32_t loadsizeStoredSize = loadsize / 64 + 1;

    size_t size = loadsizeStoredSize * sizeof(uint64_t);

    uint64_t* keep[threads];
    uint64_t* exclude[threads];
    uint64_t* deleted[threads];
    for (uint32_t t = 0; t < threads; ++t) {
        keep[t] = (uint64_t*)malloc(size);
        exclude[t] = (uint64_t*)malloc(size);
        deleted[t] = (uint64_t*)malloc(size);
    }

    #pragma omp parallel for
    for (uint32_t t = 0; t < threads; ++t) {
        for (uint32_t ldb = 0; ldb < loadsizeStoredSize; ++ldb) {
            *(keep[t] + ldb) = (uint64_t)0;
            *(exclude[t] + ldb) = (uint64_t)0;
            *(deleted[t] + ldb) = (uint64_t)0;
        }

        for (uint32_t ld = 0; ld < loadsize; ++ld) {
            uint32_t at_idx = ld * threads + t;
            if (at_idx >= unionModel->len) continue;

            bool take = true;
            UCS* atom_ucs = &unionModel->atoms[at_idx].ucs;
            LCS* rel_L = NULL;
            LCS* rel_H = NULL;

            for (uint32_t rel_idx = 0; rel_idx < duples->len; ++rel_idx) {
                /* Rels are sorted by update time. If atom is newer than relation, skip the rest */
                if (unionUpdateEntrance[at_idx] <= lastUnionUpdate[rel_idx]) break;
                /* If relation is newer, update atoms in union model */
                rel_L = &duples->L[rel_idx];
                if (!isDisjoint(atom_ucs, rel_L)) {
                    rel_H = &duples->H[rel_idx];
                    if (isDisjoint(atom_ucs, rel_H)) {
                        if (!duples->hyp[rel_idx]) {
                            take = false;
                            *(deleted[t] + ld / 64) |= ((uint64_t)1 << (ld % 64));
                        } else {
                            *(exclude[t] + ld / 64) |= ((uint64_t)1 << (ld % 64));
                        }
                        break;  // Escape inner for
                    }
                }
            }
            if (take) *(keep[t] + ld / 64) |= ((uint64_t)1 << (ld % 64));
        }
    }

    {
        segmentWriter writerA;
        segmentWriter writerB;
        segmentWriter writerC;
        segmentWriter_set(&writerA, atoms_to_keep, gsm);
        segmentWriter_set(&writerB, atoms_deleted, gsm);
        segmentWriter_set(&writerC, exclude_from_pinningterm, gsm);
        for (uint32_t t = 0; t < threads; ++t) {
            for (uint32_t ld = 0; ld < loadsize; ++ld) {
                uint32_t at_idx = ld * threads + t;
                if (at_idx >= unionModel->len) continue;

                if ((*(keep[t] + ld / 64) >> (ld % 64)) & (uint64_t)1) {
                    segmentWriter_addItem(&writerA, at_idx);
                }
                if ((*(deleted[t] + ld / 64) >> (ld % 64)) & (uint64_t)1) {
                    segmentWriter_addItem(&writerB, at_idx);
                }
                if ((*(exclude[t] + ld / 64) >> (ld % 64)) & (uint64_t)1) {
                    segmentWriter_addItem(&writerC, at_idx);
                }
            }
        }

        for (uint32_t t = 0; t < threads; ++t) {
            free(keep[t]);
            free(exclude[t]);
            free(deleted[t]);
        }
    }
}

void calculateLowerAtomicSegments(
    segmentHead** element_las[], segmentHead* element_cset[], uint32_t elements_len, segmentHead* las[],
    uint32_t las_idx[], uint32_t las_len, generalSegmentManager* gsm)
{
    #pragma omp parallel for
    for (uint32_t e = 0; e < elements_len; ++e) {
        if (*element_las[e]) abort();
        segmentReader reader;
        segmentReader_set(&reader, element_cset[e]);
        while (segmentReader_nextItem(&reader)) {
            uint32_t constant = segmentReader_currentItem(&reader);
            uint32_t constant_idx = array_index(las_idx, las_len, constant);
            if (constant_idx < las_len) {
                segment_add(element_las[e], las[constant_idx], gsm);
            }
        }
    }
}

// CrossAll

typedef struct SegmentSetNode {
    char* key;
} SegmentSetNode;

char* BitarrayMap_getKey(pointer data) { return ((SegmentSetNode*)data)->key; }

bool SegmentSet_contains(hashMap* map, segmentHead* segment)
{
    char* key = segment_to_str(segment);
    SegmentSetNode* ret = (SegmentSetNode*)hashMap_get_masked(map, key);
    return ret != NULL;
}

void SegmentSet_add(hashMap* map, segmentHead* segment)
{
    char* key = segment_to_str(segment);
    SegmentSetNode* node = (SegmentSetNode*)malloc(sizeof(SegmentSetNode));
    node->key = key;
    hashMap_map_masked(map, key, (pointer)node);
}

// ----------

void get_repeated_atoms(segmentHead** ret_repeated, Atomization_s* atomization, generalSegmentManager* gsm)
{
    // build ucs
    segmentWriter writer;
    segmentHead** ucs_extended = calloc(atomization->len, sizeof(segmentHead*));
    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        segmentWriter_set(&writer, &ucs_extended[at_idx], gsm);
        segmentWriter_cloneFrom(&writer, atomization->atoms[at_idx].ucs.constants);
    }

    // new hasmap for storing atoms' ucs
    hashMap* map = hashMap_new(NULL, 42, &BitarrayMap_getKey);

    // Add all ucs to the map. Add index to output if ucs is already in map.
    generalSegmentManager_returnSegment(gsm, ret_repeated);
    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        if (!SegmentSet_contains(map, ucs_extended[at_idx])) {
            SegmentSet_add(map, ucs_extended[at_idx]);
        } else {
            segment_addItem(ret_repeated, at_idx, gsm);
        }
    }

    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        generalSegmentManager_returnSegment(gsm, &ucs_extended[at_idx]);
    }
    free(ucs_extended);
    hashMap_delete(&map);
}

int sort_by_id(const void* at1, const void* at2) { return (int)((Atom_s*)at1)->ID - (int)((Atom_s*)at2)->ID; }

void Atomization_s_sort_by_id(Atomization_s* atomization)
{
    qsort(atomization->atoms, atomization->len, sizeof(Atom_s), sort_by_id);
}

void Atomization_s_remove_atoms(Atomization_s* atomization, segmentHead* atoms_to_remove, generalSegmentManager* gsm)
{
    if (!atoms_to_remove) return;
    uint32_t i = 0;
    uint32_t prev_at_idx = 0;
    segmentReader reader;
    segmentReader_set(&reader, atoms_to_remove);
    while (segmentReader_nextItem(&reader)) {
        uint32_t at_idx = segmentReader_currentItem(&reader);
        // cleanup
        generalSegmentManager_returnSegment(gsm, &atomization->atoms[at_idx].ucs.constants);
        generalSegmentManager_returnSegment(gsm, &atomization->atoms[at_idx].trace);

        if (prev_at_idx == 0) {
            i = at_idx;
        } else {
            memmove(&atomization->atoms[i], &atomization->atoms[prev_at_idx], (at_idx - prev_at_idx) * sizeof(Atom_s));
            i += at_idx - prev_at_idx;
        }
        prev_at_idx = at_idx + 1;
    }
    memmove(
        &atomization->atoms[i], &atomization->atoms[prev_at_idx], (atomization->len - prev_at_idx) * sizeof(Atom_s));
    i += atomization->len - prev_at_idx;
    atomization->len = i;
    atomization->atoms = (Atom_s*)realloc(atomization->atoms, atomization->len * sizeof(Atom_s));
}

void remove_repeated_atoms(Atomization_s* atomization, generalSegmentManager* gsm)
{
    segmentHead* repeated_atoms = NULL;
    get_repeated_atoms(&repeated_atoms, atomization, gsm);
    Atomization_s_remove_atoms(atomization, repeated_atoms, gsm);
    generalSegmentManager_returnSegment(gsm, &repeated_atoms);
}

bool lowerOrEqual(LCS* L, LCS* H, Atomization_s* atomization)
{
    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        if (!isDisjoint(&atomization->atoms[at_idx].ucs, L)) {
            if (isDisjoint(&atomization->atoms[at_idx].ucs, H)) {
                return false;
            }
        }
    }
    return true;
}

// TraceHelper for C ---------------------

typedef struct TraceHelper {
    segmentHead* maxTrace;
    segmentHead** tD;
    segmentHead* atomIDs;
    CS* constants;
    uint32_t nextID;
} TraceHelper;

void TraceHelper_init(TraceHelper* th, CS* constants, int indicators_num, generalSegmentManager* gsm)
{
    th->atomIDs = NULL;
    th->constants = constants;
    th->tD = (segmentHead**)calloc(indicators_num, sizeof(segmentHead*));
    th->nextID = 0;

    segment_fillWithRange(&th->maxTrace, 0, indicators_num, gsm);
    int maxTrace_len = segment_countItems(th->maxTrace);
    IF_THEN_ABORT(maxTrace_len != indicators_num, "TraceHelper initialization: incorrect number of indicators.");
}

void TraceHelper_delete(TraceHelper* th, generalSegmentManager* gsm)
{
    int indicators_num = segment_countItems(th->maxTrace);
    for (int ind_idx = 0; ind_idx < indicators_num; ++ind_idx) {
        generalSegmentManager_returnSegment(gsm, &th->tD[ind_idx]);
    }
    free(th->tD);
    generalSegmentManager_returnSegment(gsm, &th->atomIDs);
    generalSegmentManager_returnSegment(gsm, &th->maxTrace);
}

__maybe_unused static Atom_s* atom_from_id_lin(Atomization_s* atomization, uint32_t idx)
{
    // Linear search to avoid sorting
    for (uint32_t k = 0; k < atomization->len; ++k) {
        if (atomization->atoms[k].ID == idx) return &atomization->atoms[k];
    }
    IF_THEN_ABORT(true, "Atom ID not in atomization");
}

__maybe_unused static Atom_s* atom_from_id_binary(Atomization_s* atomization, uint32_t id)
{
    if (atomization->len == 0) return NULL;
    if (id < atomization->len && atomization->atoms[id].ID == id) return &atomization->atoms[id];  // short-circuit

    int32_t l = 0;
    int32_t r = atomization->len - 1;

    while (l <= r) {
        int32_t m = (r + l) / 2;
        if (atomization->atoms[m].ID < id) {
            l = m + 1;
        } else if (atomization->atoms[m].ID > id) {
            r = m - 1;
        } else {
            IF_THEN_ABORT(atomization->atoms[m].ID != id, "Error: binary search ID");
            return &atomization->atoms[m];
        }
    }
    IF_THEN_ABORT(true, "Atom ID not in atomization");
    return NULL;
}

bool checkSorted(Atomization_s* atomization, char* legend)
{
    uint32_t lastID = 0;
    bool started = false;
    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        uint32_t ID = atomization->atoms[at_idx].ID;
        if (started && (ID <= lastID)) {
            fprintf(stdout, "warning, atomization not sirted %s (%d  before  %d)", legend, lastID, ID);
            return false;
        }
        lastID = ID;
        started = true;
    }
    return true;
}

void TraceHelper_update(
    segmentHead** ids, TraceHelper* th, Atomization_s* atomization, segmentHead* LrR, bool complete,
    generalSegmentManager* gsm)
{
    IF_THEN_ABORT(*ids != NULL, "The return bitarray must be NULL");

    if (!checkSorted(atomization, "at TraceHelper_update")) {
        Atomization_s_sort_by_id(atomization);
    }

    if (complete) {
        IF_THEN_ABORT(LrR != NULL, "LrR must be NULL");
        for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
            segment_addItem(ids, atomization->atoms[at_idx].ID, gsm);
        }
    } else {
        segmentReader reader;
        segmentReader_set(&reader, LrR);
        while (segmentReader_nextItem(&reader)) {
            int at_idx = segmentReader_currentItem(&reader);
            segment_addItem(ids, atomization->atoms[at_idx].ID, gsm);
        }
    }

    segmentHead* newatoms = NULL;
    segment_subtract_to(&newatoms, *ids, th->atomIDs, gsm);

    if (complete) {
        segment_clone_to(&th->atomIDs, *ids, gsm);
    } else {
        segment_add(&th->atomIDs, *ids, gsm);
    }

    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        if (segment_containsItem(newatoms, atomization->atoms[at_idx].ID)) {
            segmentHead* out = NULL;
            segment_subtract_to(&out, th->maxTrace, atomization->atoms[at_idx].trace, gsm);

            segmentReader reader_out;
            segmentReader_set(&reader_out, out);
            while (segmentReader_nextItem(&reader_out)) {
                int ind_idx = segmentReader_currentItem(&reader_out);
                segment_addItem(&th->tD[ind_idx], atomization->atoms[at_idx].ID, gsm);
            }

            generalSegmentManager_returnSegment(gsm, &out);
        }
    }
    generalSegmentManager_returnSegment(gsm, &newatoms);
}

// -----

void reduction_by_traces(
    Atomization_s* atomization, TraceHelper* th, CS* constants, segmentHead* stored_trace_of_constant[],
    uint32_t total_indicators_len, bool verbose, generalSegmentManager* gsm)
{
    // NOTE: stored_trace_of_constant are calculated between closing traces and
    // enforcing positive duples
    // They are up to date at this stage and remain unmodified in crossAll

    // compute traces and las
    segmentHead* maxTrace = NULL;
    segment_fillWithRange(&maxTrace, 0, total_indicators_len, gsm);

    segmentHead* tD[total_indicators_len];
    for (uint32_t k = 0; k < total_indicators_len; ++k) tD[k] = NULL;

    segmentHead** las = (segmentHead**)malloc(sizeof(segmentHead*) * constants->len);
    for (uint32_t c = 0; c < constants->len; ++c) las[c] = NULL;

    {
        segmentHead* inverse_trace = NULL;
        segmentHead* atom_ucs = NULL;
        for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
            segmentReader reader;

            segmentHead* trace = atomization->atoms[at_idx].trace;
            segment_subtract_to(&inverse_trace, maxTrace, trace, gsm);
            segmentReader_set(&reader, inverse_trace);
            while (segmentReader_nextItem(&reader)) {
                int ind_idx = segmentReader_currentItem(&reader);
                segment_addItem(&tD[ind_idx], at_idx, gsm);
            }

            segment_intersect_to(&atom_ucs, atomization->atoms[at_idx].ucs.constants, constants->constants, gsm);
            segmentReader_set(&reader, atom_ucs);
            while (segmentReader_nextItem(&reader)) {
                int c = segmentReader_currentItem(&reader);
                uint32_t c_idx = array_index(constants->constants_as_array, constants->len, c);
                assert(c_idx < constants->len);
                assert(constants->constants_as_array[c_idx] == c);
                segment_addItem(&las[c_idx], at_idx, gsm);
            }
        }
        generalSegmentManager_returnSegment(gsm, &inverse_trace);
        generalSegmentManager_returnSegment(gsm, &atom_ucs);
    }

    uint32_t buffer_size = total_indicators_len > atomization->len ? total_indicators_len : atomization->len;
    int* buffer = (int*)malloc(sizeof(int) * buffer_size);

    uint32_t* shuffled_constants = (uint32_t*)malloc(sizeof(uint32_t) * constants->len);
    for (uint32_t k = 0; k < constants->len; ++k) shuffled_constants[k] = k;
    shuffle_array(shuffled_constants, constants->len);

    segmentHead* selectedIds = NULL;
    segmentHead* out = NULL;
    for (uint32_t idx = 0; idx < constants->len; ++idx) {
        uint32_t c_idx = shuffled_constants[idx];

        segmentHead* ctrace = stored_trace_of_constant[c_idx];
        segment_subtract_to(&out, maxTrace, ctrace, gsm);

        // leave at least one atom per constant
        if (!out) {
            if (segment_isDisjoint(las[c_idx], selectedIds)) {
                if (las[c_idx]) {
                    int at_idx = segment_chooseItemIn_maxSizeKnown(las[c_idx], atomization->len, buffer);
                    segment_addItem(&selectedIds, at_idx, gsm);
                }
            }
        }

        while (out) {
            int eta_idx = segment_chooseItemIn_maxSizeKnown(out, total_indicators_len, buffer);

            segmentHead* candidates = NULL;
            segment_intersect_to(&candidates, tD[eta_idx], las[c_idx], gsm);

            if (IGNORE_ERROR_B) {
                IF_THEN_WARN(!candidates, "Simplify From Constants: Trace error B");
                if (!candidates) {
                    segment_removeItem(&out, eta_idx, gsm);
                    break;
                }
            } else {
                IF_THEN_ABORT(!candidates, "Simplify From Constants: Trace error B");
            }

            segmentHead* aux = NULL;
            segment_intersect_to(&aux, candidates, selectedIds, gsm);
            {
                int at_idx;
                if (!aux) {
                    at_idx = segment_chooseItemIn_maxSizeKnown(candidates, atomization->len, buffer);
                    segment_addItem(&selectedIds, at_idx, gsm);
                } else {
                    at_idx = segment_chooseItemIn_maxSizeKnown(aux, atomization->len, buffer);
                }
                segment_intersect(&out, atomization->atoms[at_idx].trace, gsm);
            }
            generalSegmentManager_returnSegment(gsm, &aux);
            generalSegmentManager_returnSegment(gsm, &candidates);
        }
    }
    generalSegmentManager_returnSegment(gsm, &out);
    generalSegmentManager_returnSegment(gsm, &maxTrace);

    if (verbose) printf("<Trace simplification> Result: %d to %d\n", atomization->len, segment_countItems(selectedIds));

    // Remove atoms
    segmentHead* atoms_to_remove = NULL;
    segment_fillWithRange(&atoms_to_remove, 0, atomization->len, gsm);
    segment_subtract(&atoms_to_remove, selectedIds, gsm);
    Atomization_s_remove_atoms(atomization, atoms_to_remove, gsm);
    generalSegmentManager_returnSegment(gsm, &atoms_to_remove);

    // clean-up
    free(buffer);
    free(shuffled_constants);
    generalSegmentManager_returnSegment(gsm, &selectedIds);
    for (uint32_t k = 0; k < total_indicators_len; ++k) {
        generalSegmentManager_returnSegment(gsm, &tD[k]);
    }
    for (uint32_t c = 0; c < constants->len; ++c) {
        generalSegmentManager_returnSegment(gsm, &las[c]);
    }
    free(las);

    if (th) {
        // Update traceHelper
        segmentHead* ids = NULL;
        TraceHelper_update(&ids, th, atomization, NULL, true, gsm);
        generalSegmentManager_returnSegment(gsm, &ids);
    }
}

Atom_s atom_union(Atom_s* atomA, Atom_s* atomB, uint32_t epoch, generalSegmentManager* gsm)
{
    Atom_s atom = {0};
    segment_add_to(&atom.ucs.constants, atomA->ucs.constants, atomB->ucs.constants, gsm);
    segment_add_to(&atom.trace, atomA->trace, atomB->trace, gsm);

    atom.gen = atomA->gen > atomB->gen ? atomA->gen : atomB->gen;
    atom.G = atomA->G + 1 > atomB->G ? atomA->G + 1 : atomB->G;
    atom.epoch = epoch;

    return atom;
}

// discriminant and LrR contain the idx of the corresponding atoms in atomization
// NOTE: use the correct index for discriminant and LrR.
//  I need to read them as arrays and run over them, not the plain index.
//  for idx in LrR_len: at = at_as_array[idx]
Atomization_s* atomization_product(
    Atomization_s* atomization, segmentHead* discriminant, segmentHead* LrR, TraceHelper* th,
    uint32_t total_indicators_len, uint32_t epoch, generalSegmentManager* gsm)
{
    segmentHead* tD[total_indicators_len];
    for (uint32_t k = 0; k < total_indicators_len; ++k) tD[k] = NULL;

    segmentHead* maxTrace = NULL;
    segmentHead* setHIDs = NULL;
    if (th) {
        maxTrace = th->maxTrace;
        TraceHelper_update(&setHIDs, th, atomization, LrR, false, gsm);
    } else {
        segment_fillWithRange(&maxTrace, 0, total_indicators_len, gsm);
        segmentHead* out = NULL;
        segmentReader reader_out;
        segmentReader reader;
        segmentReader_set(&reader, LrR);
        while (segmentReader_nextItem(&reader)) {
            int at_r_idx = segmentReader_currentItem(&reader);
            segment_subtract_to(&out, maxTrace, atomization->atoms[at_r_idx].trace, gsm);
            segmentReader_set(&reader_out, out);
            while (segmentReader_nextItem(&reader_out)) {
                uint32_t ind = segmentReader_currentItem(&reader_out);
                segment_addItem(&tD[ind], at_r_idx, gsm);
            }
        }
        generalSegmentManager_returnSegment(gsm, &out);
    }

    // Output atomization
    Atomization_s* ret = (Atomization_s*)calloc(1, sizeof(Atomization_s));
    uint32_t ret_capacity = 1000;
    ret->atoms = calloc(ret_capacity, sizeof(Atom_s));

    segmentHead* setLIDs = NULL;
    segmentHead* out = NULL;
    segmentReader reader;
    segmentReader_set(&reader, discriminant);
    while (segmentReader_nextItem(&reader)) {
        int at_disc_idx = segmentReader_currentItem(&reader);
        Atom_s* at_disc = &atomization->atoms[at_disc_idx];  // atL
        if (th) {
            segment_addItem(&setLIDs, at_disc->ID, gsm);
        }

        bool picked = false;
        segment_subtract_to(&out, maxTrace, at_disc->trace, gsm);
        while (out) {
            int eta_idx = segment_chooseItemIn(out);
            if (th) {
                if (!tD[eta_idx]) {
                    segment_intersect(&th->tD[eta_idx], th->atomIDs, gsm);
                    segment_intersect_to(&tD[eta_idx], th->tD[eta_idx], setHIDs, gsm);
                }
            }
            segmentHead* tDeta = tD[eta_idx];

            IF_THEN_ABORT(!tDeta, "calculateAtomSetProduct trace error");

            // if tDeta is not NULL
            int at_r_id = segment_chooseItemIn(tDeta);
            Atom_s* at_r = NULL;
            if (th) {
                at_r = atom_from_id_binary(atomization, at_r_id);
            } else {
                at_r = &atomization->atoms[at_r_id];
            }
            segment_intersect(&out, at_r->trace, gsm);

            // Atom union
            if (ret->len >= ret_capacity) {
                ret_capacity *= 2;
                ret->atoms = realloc(ret->atoms, ret_capacity * sizeof(Atom_s));
                IF_THEN_ABORT(!(ret->len < ret_capacity), "Capacity exceeded");
            }
            ret->atoms[ret->len] = atom_union(at_disc, at_r, epoch, gsm);
            if (th) {
                ret->atoms[ret->len].ID = th->nextID;
                ++th->nextID;
            }
            ++ret->len;

            picked = true;
        }

        if (!picked) {
            int at_r_idx = segment_chooseItemIn(LrR);
            Atom_s* at_r = &atomization->atoms[at_r_idx];

            // Atom union
            if (ret->len >= ret_capacity) {
                ret_capacity *= 2;
                ret->atoms = realloc(ret->atoms, ret_capacity * sizeof(Atom_s));
                assert(ret->len < ret_capacity);
            }
            ret->atoms[ret->len] = atom_union(at_disc, at_r, epoch, gsm);
            if (th) {
                ret->atoms[ret->len].ID = th->nextID;
                ++th->nextID;
            }
            ++ret->len;
        }
    }
    IF_THEN_ABORT(out, "calculateAtomSetProduct out not null");
    if (th) {
        generalSegmentManager_returnSegment(gsm, &setHIDs);
        segment_subtract(&th->atomIDs, setLIDs, gsm);
        generalSegmentManager_returnSegment(gsm, &setLIDs);
    } else {
        generalSegmentManager_returnSegment(gsm, &maxTrace);
    }

    for (uint32_t k = 0; k < total_indicators_len; ++k) generalSegmentManager_returnSegment(gsm, &tD[k]);

    return ret;
}

// Remove the discriminant L - H from the atomization.
// Then, add the product dis x H to the atomization.
void cross(
    Atomization_s* atomization, LCS* rL, LCS* rH, TraceHelper* th, uint32_t total_indicators_len, uint32_t epoch,
    generalSegmentManager* gsm)
{
    if (th) {
        if (!checkSorted(atomization, "at cross")) {
            Atomization_s_sort_by_id(atomization);
        }
    }

    // Discriminant L(rL) - L(rR)
    segmentHead* discriminant = NULL;
    segmentHead* LrR = NULL;
    // Discriminant L(rL) - L(rR)
    for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
        if (isDisjoint(&atomization->atoms[at_idx].ucs, rH)) {
            if (!isDisjoint(&atomization->atoms[at_idx].ucs, rL)) {
                segment_addItem(&discriminant, at_idx, gsm);
            }
        } else {
            segment_addItem(&LrR, at_idx, gsm);
        }
    }

    IF_THEN_ABORT(!discriminant, "cross, no discriminant");

    // Discriminant x L(rR)
    Atomization_s* ret = atomization_product(atomization, discriminant, LrR, th, total_indicators_len, epoch, gsm);

    // M - (L(rL)-L(rR))
    Atomization_s_remove_atoms(atomization, discriminant, gsm);

    // Union
    if (ret) {
        uint32_t final_len = atomization->len + ret->len;
        atomization->atoms = (Atom_s*)realloc(atomization->atoms, final_len * sizeof(Atom_s));
        memcpy(&atomization->atoms[atomization->len], ret->atoms, ret->len * sizeof(Atom_s));
        atomization->len = final_len;
        free(ret->atoms);
        free(ret);
    }

    // cleanup
    generalSegmentManager_returnSegment(gsm, &discriminant);
    generalSegmentManager_returnSegment(gsm, &LrR);
}

void enforce(
    Atomization_s* atomization, LCS* L, LCS* H, TraceHelper* th, uint32_t total_indicators_len, uint32_t* epoch,
    struct CrossAll_Params params, generalSegmentManager* gsm)
{
    (*epoch) += 1;

    cross(atomization, L, H, th, total_indicators_len, *epoch, gsm);

    if (params.remove_repetitions) remove_repeated_atoms(atomization, gsm);

    if (params.calculate_redundancy) IF_THEN_ABORT(true, "Redundancy not implemented");
}

uint32_t countSizeNotOne(Atomization_s* atomization)
{
    uint32_t count = 0;
    for (uint32_t k = 0; k < atomization->len; ++k) {
        if (segment_countItems_upto2(atomization->atoms[k].ucs.constants) > 1) {
            count += 1;
        }
    }
    return count;
}

uint32_t crossAll(
    segmentHead** ret_crossed, segmentHead** ret_not_crossed, int* ret_lastj, uint32_t* ret_epoch,
    Atomization_s* atomization, CS* constants, Duples* positive_duples, segmentHead** stored_trace_of_constant,
    uint32_t total_indicators_len, _Bool* do_not_store_these_rels, struct CrossAll_Params params,
    generalSegmentManager* gsm)
{
    IF_THEN_ABORT(*ret_crossed, "crossAll (ret_crossed): Output bitarrays must be initialized to NULL.");
    IF_THEN_ABORT(
        *ret_not_crossed,
        "crossAll (ret_not_crossed): Output "
        "bitarrays must be initialized to NULL.");

    // DO NOT SHUFFLE

    __maybe_unused TraceHelper tracehelper = {0};
    TraceHelper* th = NULL;
    if (params.use_tracehelper) {
        th = &tracehelper;
        TraceHelper_init(th, constants, total_indicators_len, gsm);
        for (uint32_t at_idx = 0; at_idx < atomization->len; ++at_idx) {
            atomization->atoms[at_idx].ID = at_idx;
        }
        th->nextID = atomization->len;

        if (!checkSorted(atomization, "at crossAll start")) {
            Atomization_s_sort_by_id(atomization);
        }
    }

    uint32_t last_number_of_atoms;
    if (params.ignore_single_const_ucs) {
        last_number_of_atoms = countSizeNotOne(atomization);
    } else {
        last_number_of_atoms = atomization->len;
    }

    segmentHead* crossed = NULL;
    segmentHead* not_crossed = NULL;

    uint32_t j = 0;
    uint32_t lastj = 0;
    for (uint32_t rel_idx = 0; rel_idx < positive_duples->len; ++rel_idx) {
        LCS* L = &positive_duples->L[rel_idx];
        LCS* H = &positive_duples->H[rel_idx];
        if (lowerOrEqual(L, H, atomization)) {
            if (!do_not_store_these_rels[rel_idx]) {
                segment_addItem(&not_crossed, rel_idx, gsm);
                ++j;
            }
        } else {
            enforce(atomization, L, H, th, total_indicators_len, ret_epoch, params, gsm);
            if (!do_not_store_these_rels[rel_idx]) {
                lastj = j;
                segment_addItem(&crossed, rel_idx, gsm);
                ++j;
            }
            bool modelGettingLarger;
            if (params.ignore_single_const_ucs) {
                modelGettingLarger = countSizeNotOne(atomization) > params.simplify_threshold * last_number_of_atoms;
            } else {
                modelGettingLarger = atomization->len > params.simplify_threshold * last_number_of_atoms;
            }
            if (modelGettingLarger) {
                reduction_by_traces(
                    atomization, th, constants, stored_trace_of_constant, total_indicators_len, params.verbose, gsm);
                if (params.ignore_single_const_ucs) {
                    last_number_of_atoms = countSizeNotOne(atomization);  // atomization->len;
                    if (params.verbose)
                        fprintf(
                            stdout, "%d%% - (%d ->  %d) ", (rel_idx * 100) / positive_duples->len, atomization->len,
                            last_number_of_atoms);
                } else {
                    last_number_of_atoms = atomization->len;
                    if (params.verbose) fprintf(stdout, "%d%% - ", (rel_idx * 100) / positive_duples->len);
                }
            }
        }
    }

    reduction_by_traces(
        atomization, th, constants, stored_trace_of_constant, total_indicators_len, params.verbose, gsm);

    if (params.use_tracehelper) {
        TraceHelper_delete(th, gsm);
    }

    if (params.verbose) fprintf(stdout, "100%% - ");

    *ret_crossed = crossed;
    *ret_not_crossed = not_crossed;
    *ret_lastj = lastj;

    return atomization->len;
}

void selectAllUsefulIndicators(
    segmentHead** take, segmentHead** duples_keep, uint32_t duples_len, segmentHead* discardedIndicators,
    segmentHead* rel_L_freeTrace[], segmentHead* rel_H_freeTrace[], bool duples_hyp[], bool verbose,
    generalSegmentManager* gsm)
{
    (void)verbose;
    /* clang-format off */
    IF_THEN_ABORT(discardedIndicators != NULL, "selectAllUsefulIndicators error discardedIndicators");
    IF_THEN_ABORT(*take != NULL, "selectAllUsefulIndicators error: take must be null");
    IF_THEN_ABORT(*duples_keep != NULL, "selectAllUsefulIndicators: duples_to_keep must be null");
    /* clang-format on */

    segmentHead* tDisc[duples_len];

    #pragma omp parallel for
    for (uint32_t k = 0; k < duples_len; ++k) {
        segmentHead* tH = rel_H_freeTrace[k];
        segmentHead* tL = rel_L_freeTrace[k];
        tDisc[k] = NULL;
        segment_subtract_to(&tDisc[k], tH, tL, gsm);
    }

    for (uint32_t nr = 0; nr < duples_len; ++nr) {
        if (tDisc[nr]) {
            segment_add(take, tDisc[nr], gsm);
            segment_addItem(duples_keep, nr, gsm);
        } else {
            IF_THEN_ABORT(
                !duples_hyp[nr],
                "selectAllUsefulIndicators error\n"
                "Inconsistent\n"
                "Try using the Python version for debugging.");
        }
        generalSegmentManager_returnSegment(gsm, &tDisc[nr]);
    }
}

void reduceIndicators(
    uint32_t duples_len, uint32_t num_indicators, segmentHead** discardedIndicators, segmentHead* rel_L_freeTrace[],
    segmentHead* rel_H_freeTrace[], segmentHead** singles, bool verbose, generalSegmentManager* gsm)
{
    // Create index array to be shuffled
    uint32_t idx_arr[duples_len];
    for (uint32_t k = 0; k < duples_len; ++k) {
        idx_arr[k] = k;
    }

    segmentHead* indexes = NULL;
    segment_fillWithRange(&indexes, 0, duples_len, gsm);

    segmentHead* tDisc[duples_len];

    #pragma omp parallel for
    for (uint32_t k = 0; k < duples_len; ++k) {
        segmentHead* tH = rel_H_freeTrace[k];
        segmentHead* tL = tL = rel_L_freeTrace[k];
        tDisc[k] = NULL;
        segment_subtract_to(&tDisc[k], tH, tL, gsm);
    }

    int unique_indicators_len = num_indicators;
    int unique_indicators_len_prev = num_indicators;
    uint32_t indexes_len = duples_len;

    segmentHead* duplesOut = NULL;

    segmentWriter writer;
    segmentReader reader;
    do {
        unique_indicators_len_prev = unique_indicators_len;

        shuffle_array(idx_arr, indexes_len);

        segmentHead* take = NULL;
        for (uint32_t k = 0; k < indexes_len; ++k) {
            uint32_t nr = idx_arr[k];
            segmentWriter_set(&writer, &tDisc[nr], gsm);
            segmentWriter_subtractSegmentNoReturn(&writer, *discardedIndicators);

            IF_THEN_ABORT(
                !tDisc[nr],
                "reduceIndicators error\n"
                "Inconsistent\n"
                "Try using the Python version for debugging.");

            if (segment_isDisjoint(tDisc[nr], *singles)) {
                segmentReader_set(&reader, tDisc[nr]);
                segmentReader_nextItem(&reader);
                int ind = segmentReader_currentItem(&reader);
                if (!segmentReader_nextItem(&reader)) {
                    /* if tDisc has exactly one element */
                    segment_addItem(singles, ind, gsm);
                    segment_addItem(&duplesOut, nr, gsm);
                } else if (segment_isDisjoint(tDisc[nr], take)) {
                    segment_addItem(&take, segment_chooseItemIn(tDisc[nr]), gsm);
                }
            } else {
                segment_addItem(&duplesOut, nr, gsm);
            }
        }

        segment_add(&take, *singles, gsm);

        unique_indicators_len = segment_countItems(take);
        if (verbose) printf("Number of unique indicators after reduction %d\n", unique_indicators_len);

        segment_subtract(&indexes, duplesOut, gsm);
        as_array(indexes, idx_arr);
        indexes_len = segment_countItems(indexes);

        segment_fillWithRange(discardedIndicators, 0, num_indicators, gsm);
        segment_subtract(discardedIndicators, take, gsm);

        generalSegmentManager_returnSegment(gsm, &take);
    } while (unique_indicators_len < unique_indicators_len_prev && indexes_len);

    for (uint32_t k = 0; k < duples_len; ++k) {
        generalSegmentManager_returnSegment(gsm, &tDisc[k]);
    }
    generalSegmentManager_returnSegment(gsm, &duplesOut);
    generalSegmentManager_returnSegment(gsm, &indexes);
}
