// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include "cbar.h"

void segment_add(segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_addSegmentNoReturn(&writer, segment);
}

void segment_add_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_cloneFrom(&writer, segmentA);
    segmentWriter_addSegmentNoReturn(&writer, segmentB);
}

void segment_intersect(
    segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_intersectSegmentNoReturn(&writer, segment);
}

void segment_intersect_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_cloneFrom(&writer, segmentA);
    segmentWriter_intersectSegmentNoReturn(&writer, segmentB);
}

void segment_subtract(
    segmentHead** destination, segmentHead* subtract, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_subtractSegmentNoReturn(&writer, subtract);
}

void segment_subtract_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_cloneFrom(&writer, segmentA);
    segmentWriter_subtractSegmentNoReturn(&writer, segmentB);
}

void segment_addItem(segmentHead** segment, int item, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segment, gsm);
    segmentWriter_addItem(&writer, item);
}

void segment_removeItem(segmentHead** segment, int item, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, segment, gsm);
    segmentWriter_removeItem(&writer, item);
}

void segment_clone_to(segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm)
{
    segmentWriter writer;
    segmentWriter_set(&writer, destination, gsm);
    segmentWriter_cloneFrom(&writer, segment);
}

