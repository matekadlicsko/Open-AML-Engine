// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#pragma once

#include <omp.h>
#include <stdio.h>

//-----------------------------------------------------

#define segmentHead cbarHead
#define segmentReader cbarReader
#define segmentReader_set   cbarReader_set
#define segmentReader_setAndExecuteOnEachItem  cbarReader_setAndExecuteOnEachItem
#define segmentWriter cbarWriter
#define segmentReader_nextItem  cbarReader_nextItem
#define segmentReader_currentItem  cbarReader_currentItem
#define generalSegmentManager  generalCbarManager
#define segmentWriter_cloneFrom  cbarWriter_cloneFrom
#define segmentWriter_addSegmentNoReturn  cbarWriter_addCbar
#define segmentWriter_addSegment  cbarWriter_addCbar
#define segmentWriter_intersectSegment  cbarWriter_intersectCbar
#define segmentWriter_intersectSegmentNoReturn   cbarWriter_intersectCbar
#define segmentWriter_subtractSegmentNoReturn  cbarWriter_subtractCbar
#define segmentWriter_subtractSegment   cbarWriter_subtractCbar
#define segmentWriter_addItemRepeatedExclusiveUse(a,b,c,d)  cbarWriter_addItem(a,b)
#define segmentWriter_addItem   cbarWriter_addItem
#define segmentWriter_removeItem  cbarWriter_removeItem
#define segment_countItems  cbar_countItems
#define segment_countItems_upto2  cbar_countItems_upto2
#define segment_chooseItemIn cbar_chooseItemIn
#define segmentWriter_set   cbarWriter_set
#define segmentWriter_addTransformFromTable   cbarWriter_addTransformFromTable
#define generalSegmentManager_getSegment  generalCbarManager_getCbar
#define generalSegmentManager_returnSegment   generalCbarManager_returnCbar
#define generalSegmentManager_new   generalCbarManager_new
#define generalSegmentManager_delete  generalCbarManager_delete
#define generalSegmentManager_allReturned  generalCbarManager_allReturned
#define generalSegmentManager_countSegmentsOut generalCbarManager_countCbarsOut
#define maxSegmentIndex  2147483648
#define segment_inSegment   cbar_inCbar
#define segment_compareSegments  cbar_compareCbars
#define segment_containsItem   cbar_containsItem
#define segment_isDisjoint   cbar_isDisjoint
#define segment_size   cbar_getSize
#define segment_print   cbar_print

//-----------------------------------------------------

#define d(...)                                                   \
    printf("[%s] %s(%04d): ", __FILE__, __FUNCTION__, __LINE__); \
    printf(__VA_ARGS__);                                         \
    printf("\n");

#define min(vara_, varb_) (((vara_) < (varb_)) ? vara_ : varb_)

#define max(vara_, varb_) (((vara_) < (varb_)) ? varb_ : vara_)

//-----------------------------------------------------
#define true 1
#define false 0
#define null 0

typedef _Bool boolean;
typedef unsigned long long osUnsignedLong;
typedef long long osLong;

#define maxFrequencyMatrixEntryName 2048

#define osLongSizeBytes 8

#define cbarHeaderCbarLength osUnsignedLong
#define cbarHeaderCbarMaxLength osUnsignedLong
#define cbarHeaderLastByteOffset osLong
#define cbarHeaderLastSequenceLength short
#define cbarHeaderFirstAuxInt int

#define cbarHeaderCbarLength_Offset 0
#define cbarHeaderCbarMaxLength_Offset sizeof(cbarHeaderCbarLength)
#define cbarHeaderLastByteOffset_Offset (cbarHeaderCbarMaxLength_Offset + sizeof(cbarHeaderCbarMaxLength))
#define cbarHeaderLastSequenceLength_Offset (cbarHeaderLastByteOffset_Offset + sizeof(cbarHeaderLastByteOffset))
#define cbarHeaderFirstAuxInt_Offset (cbarHeaderLastSequenceLength_Offset + sizeof(cbarHeaderLastSequenceLength))

#define cbarHeaderSize (cbarHeaderFirstAuxInt_Offset + sizeof(cbarHeaderFirstAuxInt))

/*-----------------------------------------------------------------------------*/

typedef void* pointer;
typedef size_t memSize;

/*-----------------------------------------------------------------------------*/
/*------------------------------- stack ---------------------------------------*/
/*-----------------------------------------------------------------------------*/

typedef struct stack {
    memSize size;
    pointer* pC;  // points to first available
    pointer* pF;
    pointer* data;
} stack;

/*-----------------------------------------------------------------------------*/
/*----------------------------- unounded stack --------------------------------*/
/*-----------------------------------------------------------------------------*/

typedef struct unboundedStack {
    memSize largestStackSize;
    unsigned int stackArraySize;
    unsigned int currentStackIndex;
    stack** stackArray;
    stack* currentStack;
    long long pointersIn; /* allow negatives for bound check */
} unboundedStack;

/*-----------------------------------------------------------------------------*/
/*-------------------------------- allocator ----------------------------------*/
/*-----------------------------------------------------------------------------*/

typedef struct allocator {
    memSize size;
    memSize byteSize;
    char* pI;
    char* pC;  // points to first available
    char* pF;
    void* data;
} allocator;

/*-----------------------------------------------------------------------------*/
/*----------------------------- unboundedAllocator ----------------------------*/
/*-----------------------------------------------------------------------------*/

typedef struct unboundedAllocator {
    memSize byteSize;
    memSize largestAllocatorSize;
    unsigned int allocatorArraySize;
    allocator** AllocatorArray;
    allocator* currentAllocator;
    unboundedStack* theStack;
    long long allocationsOut;   /* allow negatives for bound check */
    long long totalAllocations; /* allow negatives for bound check */
    boolean concurrent;
    omp_lock_t lock;
} unboundedAllocator;

/*-----------------------------------------------------------------------------*/
/*--------------------------------- cbars -------------------------------------*/
/*-----------------------------------------------------------------------------*/

typedef unsigned char cbarHead;

typedef struct cbarReader {
    cbarHead* cbar;
    unsigned char* i;          /* pointer to the first char of the source  */
    unsigned char* x;          /* pointer to the current char in the source */
    unsigned char* f;          /* pointer to the first char immediately after the source ends  */
    unsigned char* lsf;        /* pointer to the last char of a section of the source
                                  made entirely of literal source chars */
    osLong charOffset;         /* the offset in bytes from the beginning of an imaginary
                                  decompressed cbar to the imaginary position
                                  corresponding to x */
    unsigned char xValResidue; /* current char been read */
    unsigned int inCharIndex;  /* an index from 0 to 8 of a bit inside a char */
    unsigned char bitflag;     /* a bit mask for a char with one bit only set to one */
    unsigned int currentIndex; /* the output of the next operation that corresponds to a
                                  bit index in the imaginary decompressed cbar */
    boolean moveforward;       /* indicates that, once xValResidue has been decoded, x
                                  should be moved 1 byte forward */
} cbarReader;

typedef struct generalCbarManager {
    int initialSize;
    int countOut;
    long long memoryUsed;
} generalCbarManager;

typedef struct cbarWriter {
    cbarHead** ptCbar; /* a double pointer to the cbar where data will be
                          written at the end of a write operation. */
    cbarHead* cbar;    /* a single pointer to the cbar where data will be written
                          at the end of a write operation. */
    generalCbarManager* manager;
    cbarHead* outCbar;                 /* the provisional cbar where data will be written during
                                          the write operation */
    unsigned char* shortSequenceStart; /* pointer to the byte where the length
                                          of a contiguous substring of literal
                                          chars will be written. */
    osLong byteOffset;                 /* the offset in bytes from the beginning of an imaginary
                                          decompressed output cbar to the imaginary position
                                          corresponding to the last pushed byte. */
    unsigned char* i;                  /* pointer to the byte where the next byte will be written. */
    unsigned char* max;                /* a pointer to the first char after the allocated size */
    cbarReader reader;                 /* a reader for the input cbar */
} cbarWriter;

/*-----------------------------------------------------------------------------*/
/*--------------------------------- hashMap -----------------------------------*/
/*-----------------------------------------------------------------------------*/

#define noValue null
#define hashMap_baseSize 64

typedef struct hashMap {
    unsigned long nodeBitMap;
    pointer values[hashMap_baseSize];
    unboundedAllocator* allocator;
    int itemsOnThis;
    boolean ownAllocator;
    unsigned int seed;
    char* (*getKey)(pointer);
    int readCounter;
} hashMap;

typedef struct frequencyMatrixEntry {
    char key[maxFrequencyMatrixEntryName];
    double value;
} frequencyMatrixEntry;

/*-----------------------------------------------------------------------------*/
/*-------------------------------- functions ----------------------------------*/
/*-----------------------------------------------------------------------------*/

// Cbar
int cbar_chooseItemIn(cbarHead* cbar);
int cbar_countItems(cbarHead* cbar);
int cbar_countItems_upto2(cbarHead* cbar);
int cbar_compareCbars(cbarHead* cbarA, cbarHead* cbarB);
boolean cbar_inCbar(cbarHead* includedCbar, cbarHead* containerCbar);
boolean cbar_containsItem(cbarHead* cbar, int itemIndex);
boolean cbarWriter_removeItem(cbarWriter* self, int itemIndex);
boolean cbarWriter_addItemGeneral(cbarWriter* self, int itemIndex);
boolean cbarWriter_addItem(cbarWriter* self, int itemIndex);
boolean cbarWriter_subtractCbar(cbarWriter* self, cbarHead* sourceCbar);
boolean cbar_isDisjoint(cbarHead* cbarA, cbarHead* cbarB);
boolean cbarWriter_intersectCbar(cbarWriter* self, cbarHead* sourceCbar);
boolean cbarWriter_addCbar(cbarWriter* self, cbarHead* sourceCbar);
void cbarWriter_cloneFrom(cbarWriter* self, cbarHead* source);
void cbarWriter_set(cbarWriter* self, cbarHead** onPtCbar, generalCbarManager* memoryManager);
boolean generalCbarManager_allReturned(generalCbarManager* self);
int generalCbarManager_countCbarsOut(generalCbarManager* self);
void generalCbarManager_delete(generalCbarManager** self);
generalCbarManager* generalCbarManager_new(int initialSize);
unsigned int cbarReader_currentItem(cbarReader* self);
boolean cbarReader_nextItem(cbarReader* self);
void cbarReader_set(cbarReader* self, cbarHead* onCbar);
void generalCbarManager_returnCbar(generalCbarManager* self, cbarHead** pHead);
cbarHead* generalCbarManager_getCbar(generalCbarManager* self, osUnsignedLong cbarLength);
void cbar_print(cbarHead* cbar);
cbarHeaderCbarLength cbar_getSize(cbarHead* cbar);

// hashMap
void hashMap_delete(hashMap** self);
hashMap* hashMap_new(unboundedAllocator* theAllocator, unsigned int seed, char* (*getKey)(pointer));
void hashMap_startIteration(hashMap* self);
pointer hashMap_next(hashMap* self);
int hashMap_count(hashMap* self);
boolean hashMap_remove(hashMap* self, char* key);
pointer hashMap_get(hashMap* self, char* key);
void hashMap_map(hashMap* self, char* key, pointer value);
// Masked functions use cbars as keys;
char* segment_to_str(segmentHead* segment);
pointer hashMap_get_masked(hashMap* self, char* key);
void hashMap_map_masked(hashMap* self, char* key, pointer value);
