// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include "cbar.h"

int segment_getAllSegmentsBufferLength(segmentHead** segments, int segments_len);
void segment_getAllSegmentsBuffer(char* buffer, segmentHead** segments, int segments_len);
int segment_getBufferNumberOfCbars(char* buffer);
void segment_buildFromBuffer(char* buffer, segmentHead** segments[], generalSegmentManager* gsm);
