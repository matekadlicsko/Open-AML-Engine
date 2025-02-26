// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include <stdio.h>

#include "cbar.h"

/* General Segment Manager */
generalSegmentManager* createGenSegMgr()
{
    generalSegmentManager* theGeneralSegmentManager = NULL;
    theGeneralSegmentManager = generalSegmentManager_new(1);
    return theGeneralSegmentManager;
}

void deleteGenSegMgr(generalSegmentManager* theGeneralSegmentManager)
{
    if (!generalSegmentManager_allReturned(theGeneralSegmentManager)) {
        d("Leaked segments: %d", generalSegmentManager_countSegmentsOut(theGeneralSegmentManager));
    }
    generalSegmentManager_delete(&theGeneralSegmentManager);
}

boolean verifyAllRetGenSegMgr(generalSegmentManager* theGeneralSegmentManager)
{
    if (!generalSegmentManager_allReturned(theGeneralSegmentManager)) {
        d("Leaked segments: %d", generalSegmentManager_countSegmentsOut(theGeneralSegmentManager));
        return false;
    }
    return true;
}
