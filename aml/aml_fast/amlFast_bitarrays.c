// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include <stdio.h>

#include "cbar.h"

segmentHead* bitarray_new() { return NULL; }

void bitarray_delete(
    segmentHead** segment, generalSegmentManager* theGeneralSegmentManager)
{
    generalSegmentManager_returnSegment(theGeneralSegmentManager, segment);
}

int bitarray_howManyAreOut(generalSegmentManager* theGeneralSegmentManager)
{
    return generalSegmentManager_countSegmentsOut(theGeneralSegmentManager);
}

void bitarray_clone(
    segmentHead** new_segment, segmentHead* segment, generalSegmentManager* theGeneralSegmentManager)
{
    generalSegmentManager_returnSegment(theGeneralSegmentManager, new_segment);

    segmentWriter writer;
    segmentWriter_set(&writer, new_segment, theGeneralSegmentManager);
    segmentWriter_cloneFrom(&writer, segment);
}

int bitarray_length(segmentHead* segment)
{
    return segment_countItems(segment);
}

int bitarray_length_upto2(segmentHead* segment)
{
    return segment_countItems_upto2(segment);
}

int bitarray_compare(segmentHead* segmentA, segmentHead* segmentB)
{
    return segment_compareSegments(segmentA, segmentB) ? false : true;
}

int bitarray_contains(segmentHead* segment, int item)
{
    return segment_containsItem(segment, item);
}

int bitarray_isdisjoint(segmentHead* segmentA, segmentHead* segmentB)
{
    return segment_isDisjoint(segmentA, segmentB);
}

int bitarray_issubset(segmentHead* segment, segmentHead* container)
{
    return segment_inSegment(segment, container);
}

void bitarray_unpack(int ret[], segmentHead* segment)
{
    segmentReader reader;
    segmentReader_set(&reader, segment);
    int idx = 0;
    while (segmentReader_nextItem(&reader)) {
        ret[idx++] = segmentReader_currentItem(&reader);
    }
}

void bitarray_addItem(
    segmentHead** segment, int item,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segment, theGeneralSegmentManager);
    segmentWriter_addItem(&writer, item);
}

void bitarray_addItems(
    segmentHead** segment, int items[], int items_len,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    int __attribute__((unused)) iH = -1;
    int __attribute__((unused)) unit = -1;
    segmentWriter_set(&writer, segment, theGeneralSegmentManager);
    for (int idx = 0; idx < items_len; ++idx) {
        segmentWriter_addItemRepeatedExclusiveUse(
            &writer, items[idx], &iH, &unit);
    }
}

void bitarray_removeItem(
    segmentHead** segment, int item,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segment, theGeneralSegmentManager);
    segmentWriter_removeItem(&writer, item);
}

void bitarray_add(
    segmentHead** segmentA, segmentHead* segmentB,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segmentA, theGeneralSegmentManager);
    segmentWriter_addSegmentNoReturn(&writer, segmentB);
}

void bitarray_intersect(
    segmentHead** segmentA, segmentHead* segmentB,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segmentA, theGeneralSegmentManager);
    segmentWriter_intersectSegmentNoReturn(&writer, segmentB);
}

void bitarray_subtract(
    segmentHead** segmentA, segmentHead* segmentB,
    generalSegmentManager* theGeneralSegmentManager)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segmentA, theGeneralSegmentManager);
    segmentWriter_subtractSegmentNoReturn(&writer, segmentB);
}
