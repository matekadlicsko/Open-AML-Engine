// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "cbar.h"
#include "aml_fast.h"
#include "bitarrays.h"

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

typedef struct TraceHelperPy {
    segmentHead* maxTrace;
    segmentHead*** tD;
    segmentHead** atomIDs;
    CS* constants;
} TraceHelperPy;

TraceHelperPy* TraceHelper_init_from_python(
    CS* constants, int indicators_num, segmentHead** atomIDs, segmentHead*** tD, generalSegmentManager* gsm)
{
    TraceHelperPy* th = (TraceHelperPy*)calloc(1, sizeof(TraceHelperPy));
    // Clone constants (never modified)
    th->constants = constants;
    // Init maxTrace (never modified in same iteration)
    segmentWriter writer;
    segmentWriter_set(&writer, &th->maxTrace, gsm);
    for (int idx_ind = 0; idx_ind < indicators_num; ++idx_ind) {
        segmentWriter_addItem(&writer, idx_ind);
    }
    int maxTrace_len = segment_countItems(th->maxTrace);
    if (maxTrace_len != indicators_num) abort();
    // atomIDs
    th->atomIDs = atomIDs;
    // Init indicators
    th->tD = (segmentHead***)malloc(indicators_num * sizeof(segmentHead**));
    for (int k = 0; k < indicators_num; ++k) {
        th->tD[k] = tD[k];
    }

    return th;
}

void TraceHelper_delete_from_python(TraceHelperPy* th, generalSegmentManager* gsm)
{
    free(th->tD);
    generalSegmentManager_returnSegment(gsm, &th->maxTrace);
}

void TraceHelperPy_update(
    TraceHelperPy* th, uint32_t atomization_len, segmentHead** atomization_at_trace[], int atomization_id[],
    bool complete, generalSegmentManager* gsm)
{
    segmentHead* ids = NULL;
    for (uint32_t k = 0; k < atomization_len; ++k) {
        segment_addItem(&ids, atomization_id[k], gsm);
    }

    segmentHead* newatoms = NULL;
    segment_subtract_to(&newatoms, ids, *th->atomIDs, gsm);

    if (complete) {
        segment_clone_to(th->atomIDs, ids, gsm);
    } else {
        segment_add(th->atomIDs, ids, gsm);
    }
    generalSegmentManager_returnSegment(gsm, &ids);

    {
        int last_id = -1;
        for (uint32_t at_idx = 0; at_idx < atomization_len; ++at_idx) {
            IF_THEN_ABORT(atomization_id[at_idx] <= last_id, "TraceHelper: Atomization not sorted");
            last_id = atomization_id[at_idx];
            if (segment_containsItem(newatoms, atomization_id[at_idx])) {
                segmentHead* out = NULL;
                segment_subtract_to(&out, th->maxTrace, *atomization_at_trace[at_idx], gsm);

                segmentReader reader_out;
                segmentReader_set(&reader_out, out);
                while (segmentReader_nextItem(&reader_out)) {
                    int ind_idx = segmentReader_currentItem(&reader_out);
                    segment_addItem(th->tD[ind_idx], atomization_id[at_idx], gsm);
                }

                generalSegmentManager_returnSegment(gsm, &out);
            }
        }
    }
    generalSegmentManager_returnSegment(gsm, &newatoms);
}
