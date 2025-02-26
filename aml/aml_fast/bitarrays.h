// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#pragma once

#include "cbar.h"

void segment_add(segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm);

void segment_add_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm);

void segment_intersect(segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm);

void segment_intersect_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm);

void segment_subtract(segmentHead** destination, segmentHead* subtract, generalSegmentManager* gsm);

void segment_subtract_to(
    segmentHead** destination, segmentHead* segmentA, segmentHead* segmentB, generalSegmentManager* gsm);

void segment_addItem(segmentHead** segment, int item, generalSegmentManager* gsm);

void segment_removeItem(segmentHead** segment, int item, generalSegmentManager* gsm);

void segment_clone_to(segmentHead** destination, segmentHead* segment, generalSegmentManager* gsm);
