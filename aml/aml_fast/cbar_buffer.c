// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include "cbar.h"

#include <string.h>

// NOTE: It only works with compressed bitarrays

int segment_getAllSegmentsBufferLength(segmentHead** segments, int segments_len)
{
    /* get length of buffer based on cbars' size */
    int total_length = 0;
    for (int bar = 0; bar < segments_len; ++bar) {
        total_length += segment_size(segments[bar]);
    }
    return sizeof(segments_len) + segments_len * sizeof(osUnsignedLong) + total_length;
}

void segment_getAllSegmentsBuffer(
    char* buffer, segmentHead** segments, int segments_len)
{
    char* ptr = buffer;

    /* Record segments length */
    memcpy(ptr, &segments_len, sizeof(segments_len));
    ptr += sizeof(segments_len);

    for (int bar = 0; bar < segments_len; ++bar) {
        osUnsignedLong size = segment_size(segments[bar]);
        /* Record length */
        memcpy(ptr, &size, sizeof(size));
        ptr += sizeof(size);
        /* Record cbar */
        memcpy(ptr, segments[bar], size);
        ptr += size;
    }
}

int segment_getBufferNumberOfCbars(char* buffer) { return *(int*)buffer; }

void segment_buildFromBuffer(
    char* buffer, segmentHead** segments[], generalSegmentManager* gsm)
{
    char* ptr = buffer;

    /* Read atomization length */
    int atomization_len;
    memcpy(&atomization_len, ptr, sizeof(atomization_len));
    ptr += sizeof(atomization_len);

    for (int bar = 0; bar < atomization_len; ++bar) {
        osUnsignedLong size;
        /* Read length */
        memcpy(&size, ptr, sizeof(size));
        ptr += sizeof(size);

        /* Return input cbar */
        generalSegmentManager_returnSegment(gsm, segments[bar]);

        if (!size) continue;

        /* Rebuild cbar */
        *segments[bar] = generalSegmentManager_getSegment(gsm, size);
        memcpy(*segments[bar], ptr, size);
        ptr += size;
    }
}
