// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#pragma once

#include <inttypes.h>

#include "cbar.h"

typedef struct CS {
    segmentHead* constants;
    uint32_t* constants_as_array;
    uint32_t len;
} CS;

typedef struct UCS {
    segmentHead* constants;
} UCS;

typedef struct LCS {
    segmentHead* constants;
} LCS;

typedef struct UCS_mut {
    segmentHead** constants;
} UCS_mut;

typedef UCS_mut LCS_mut;

typedef struct Atom {
    UCS ucs;
    segmentHead** trace;
} Atom;

typedef struct Tracer {
    LCS_mut* indicators;
    UCS* atomIndicators;
    uint32_t indicators_len;
    uint32_t atomIndicators_len;
} Tracer;

typedef struct Atomization {
    Atom* atoms;
    uint32_t len;
} Atomization;

typedef struct Atom_s {
    UCS ucs;
    segmentHead* trace;
    uint32_t epoch;
    uint32_t G;
    uint32_t gen;
    uint32_t ID;
} Atom_s;

typedef struct Atomization_s {
    Atom_s* atoms;
    uint32_t len;
} Atomization_s;

void calculateTraceOfAtom(const Tracer* tracer, Atom* at, generalSegmentManager* gsm);
int segment_chooseItemIn_withBuffer(segmentHead* out, int* buffer);
