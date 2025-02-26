// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

/* Types */
struct CrossAll_Params {
    _Bool calculate_redundancy;
    _Bool remove_repetitions;
    _Bool verbose;
    _Bool use_tracehelper;
    float simplify_threshold;
    _Bool ignore_single_const_ucs;
};

/* Main Functions */
void freeTraceAll(void* space, void* tracer, void* theGeneralSegmentManager);
void traceAll(void* space, void* tracer, void* atomization, void* gsm);
void storeTracesOfConstants(
    void*** traces, uint32_t total_num_indicators, uint32_t constants_len, int constants[], void* atomization,
    void* gsm);
void considerPositiveDuples(void* tr, void* duples, void* gsm);
void simplifyFromConstants_inner_loop(
    void** ret_selected, const uint32_t constants_len, void* las[], void* tD[], void* constToStoredTraces[],
    const uint32_t atomization_len, void* atomization_traces[], const uint32_t total_indicators_len, void* gsm);
void updateUnionModelWithSetOfPduples(
    void** atoms_to_keep, void** atoms_deleted, void** exclude_from_pinningterm, void* unionModel, void* duples,
    int64_t* unionUpdateEntrance, int64_t* lastUnionUpdate, void* gsm);
void calculateLowerAtomicSegments(
    void** element_las[], void* element_cset[], uint32_t elements_len, void* las[], uint32_t las_idx[],
    uint32_t las_len, void* gsm);
uint32_t crossAll(
    void** ret_crossed, void** ret_not_crossed, int* ret_lastj, uint32_t* ret_epoch, void* atomization, void* constants,
    void* positive_duples, void** stored_trace_of_constant, uint32_t total_indicators_len,
    _Bool* do_not_store_these_rels, struct CrossAll_Params params, void* gsm);
void selectAllUsefulIndicators(
    void** take, void** duples_keep, uint32_t duples_len, void* discardedIndicators, void* rel_L_freeTrace[],
    void* rel_H_freeTrace[], _Bool duples_hyp[], _Bool verbose, void* gsm);
void reduceIndicators(
    uint32_t duples_len, uint32_t num_indicators, void** discardedIndicators, void* rel_L_freeTrace[],
    void* rel_H_freeTrace[], void** singles, _Bool verbose, void* gsm);

/* TraceHelper */
void* TraceHelper_init_from_python(void* constants, int indicators_num, void** atomIDs, void*** tD, void* gsm);
void TraceHelper_delete_from_python(void* th, void* gsm);
void TraceHelperPy_update(
    void* th, uint32_t atomization_len, void** atomization_at_trace[], int atomization_id[], _Bool complete, void* gsm);

/* Loading and saving */
int segment_getAllSegmentsBufferLength(void** segments, int segments_len);
void segment_getAllSegmentsBuffer(char* buffer, void** segments, int segments_len);
int segment_getBufferNumberOfCbars(char* buffer);
void segment_buildFromBuffer(char* buffer, void** segments[], void* gsm);

/* Linkers */
void* linkSpace(uint32_t sp_len, void* sp_cset_constants[], void** sp_ftrace[], void** sp_trace[]);
void unlinkSpace(void* space);
void* linkTracer(uint32_t tr_ind_len, void** tr_ind_constants[], uint32_t tr_atind_len, void* tr_atind_constants[]);
void unlinkTracer(void* tracer);
void* linkAtomization(uint32_t atomization_len, void* atomization_at_ucs_constants[], void** atomization_at_trace[]);
void unlinkAtomization(void* atomization);
void* linkAtomization_s(
    uint32_t atomization_len, void* atomization_at_ucs_constants[], void* atomization_at_trace[],
    uint32_t atomization_epoch[], uint32_t atomization_G[], uint32_t atomization_gen[], void* gsm);
void unlinkAtomization_s(void* atomization, void* gsm);
void extractAtomization_s(
    void* atomization, void** at_ucs_constants[], void** at_trace[], uint32_t at_epoch[], uint32_t at_G[],
    uint32_t at_gen[]);
void* linkCS_constants(void* cs_constants);
void unlinkCS_constants(void* cs);
void* linkDuple(uint32_t rel_len, void* L_constants[], void* H_constants[], int rel_hyp[]);
void unlinkDuple(void* rels);

/* General Segment Manager */
void* createGenSegMgr();
void deleteGenSegMgr(void* theGeneralSegmentManager);
int verifyAllRetGenSegMgr(void* theGeneralSegmentManager);
