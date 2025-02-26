// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

#include "cbar.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CACHE_LINE 64

#define EXTRA_SIZE_ALLOWED 1.5
#define SMALL_EXTRA_SIZE_ALLOWED 1.1

#define sixBitsCapacity 64
#define fourteenBitsCapacity 16384
#define indicateEmptyMaskAsChar ((unsigned char) 128)   /* frist bit to 1 */
#define firstTwoBitMask ((unsigned char) 192)
#define indicateCountOfContentBytes ((unsigned char) 64)   /* frist bit to 0 second to 1 */

#define copySmallSequence(_dest, _source, _size) \
    { \
        size_t kvari = 0; \
        for (kvari = 0; kvari < (_size); kvari++) { \
            if ((kvari + sizeof(unsigned long long)) < (_size)) { \
                *(unsigned long long *) ((unsigned char *) (_dest) + kvari) = *(unsigned long long *) ((unsigned char *) (_source) + kvari); \
                kvari += sizeof(unsigned long long) - 1; \
            } else { \
                *((unsigned char *) (_dest) + kvari) =  *((unsigned char *) (_source) + kvari); \
            } \
        } \
    }

// TWO_BYTE_SEQUENCE_COUNTER beg

#define sequenceMaxCapacity  fourteenBitsCapacity

#define addLiteralCounterChar(nonNulls, i) \
    *(i) = (unsigned char) ((nonNulls) % sixBitsCapacity); \
    *(i++) |= indicateCountOfContentBytes; \
    *(i++) = (unsigned char) ((nonNulls) / sixBitsCapacity);

#define literalCounterValue(charPt)  \
    ((*(unsigned char*)charPt & ~indicateCountOfContentBytes) + (*(unsigned char*)(charPt + 1) * sixBitsCapacity))

// TWO_BYTE_SEQUENCE_COUNTER end

#define addEmptyBytesCounter(emptyBytes, i) \
    *(i) = (unsigned char) ((emptyBytes) % sixBitsCapacity); \
    *(i++) |= indicateEmptyMaskAsChar; \
    *(i++) = (unsigned char) ((emptyBytes) / sixBitsCapacity);

#define isEmptyCounter(charval)  \
    (charval & indicateEmptyMaskAsChar)

#define emptyCounterValue(charPt)  \
    ((*(unsigned char*)charPt & ~indicateEmptyMaskAsChar) + (*(unsigned char*)(charPt + 1) * sixBitsCapacity))

#define isLiteralCounterChar(charval)  \
    ((charval & indicateCountOfContentBytes) && !(charval & indicateEmptyMaskAsChar))

#define canBeWrtittenAsIsolatedChar(charval)  \
    (((charval) & firstTwoBitMask) == 0)

#define addEmptyBytes(numBytes, i, check) \
    while (numBytes > 0) { \
        if (numBytes < fourteenBitsCapacity) { \
            check; \
            addEmptyBytesCounter((unsigned short) (numBytes), i); \
            numBytes = 0; \
        } else { \
            check; \
            addEmptyBytesCounter((unsigned short) fourteenBitsCapacity - 1, i); \
            numBytes -= fourteenBitsCapacity - 1; \
        } \
    };

// ---------------------

void terminate(int h)
{
    d("+++++++++ T E R M I N A T E D +++++++++\n");
    int *x = null;
    *x = h;
    exit(0);
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*---------------------------------- stack ------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

boolean stack_isFull(stack *self) { return (self->pC == self->pF); }

boolean stack_isEmpty(stack *self) { return (self->pC == self->data); }

memSize stack_memoryUsed(stack *self) { return (sizeof(pointer) * self->size); }

void stack_push(stack *self, pointer val)
{
    *(self->pC++) = val;
}

pointer stack_pull(stack *self)
{
    return *(--self->pC);
}

void stack_finalize(stack *self)
{
    if (self->data != null) {
        free(self->data);
        self->data = null;
    }
}

boolean stack_initialize(stack *self, memSize size)
{
    boolean ok = false;
    self->size = size;
    self->data = (pointer *)malloc(sizeof(pointer) * self->size);
    if (self->data == null) {
        d("malloc returned null.");
        goto done;
    }
    self->pC = self->data;
    self->pF = self->pC + self->size;

    ok = true;
done:
    return ok;
}

void stack_delete(stack **self)
{
    stack_finalize(*self);
    free(*self);
    *self = null;
}

stack *stack_new(memSize size)
{
    stack *self = null;
    self = (stack *)malloc(sizeof(stack));
    if (self != null) {
        if (!stack_initialize(self, size)) {
            stack_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*----------------------------- unbounded stack -------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

memSize unboundedStack_memoryUsed(unboundedStack *self)
{
    memSize memoryUsed = sizeof(stack *) * self->stackArraySize;
    unsigned int k;
    stack **bStack = self->stackArray;
    for (k = 0; k < self->stackArraySize; k++) {
        memoryUsed += stack_memoryUsed(*bStack) + sizeof(stack);
        ++bStack;
    }
    return memoryUsed;
}

boolean unboundedStack_isEmpty(unboundedStack *self)
{
    if (self->currentStackIndex == 0) {
        return stack_isEmpty(self->currentStack);
    }
    return false;
}

void unboundedStack_extend(unboundedStack *self)
{
    ++self->stackArraySize;
    self->largestStackSize *= 2;
    self->stackArray = (stack **)realloc(
        self->stackArray, sizeof(stack *) * self->stackArraySize);
    if (self->stackArray == null) {
        d("realloc returned null.");
        terminate(0);
    }
    *(self->stackArray + (self->stackArraySize - 1)) =
        stack_new(self->largestStackSize);
}

void unboundedStack_push(unboundedStack *self, pointer val)
{
    if (stack_isFull(self->currentStack)) {
        if (self->currentStackIndex == self->stackArraySize - 1) {
            unboundedStack_extend(self);
        }
        ++self->currentStackIndex;
        self->currentStack = *(self->stackArray + self->currentStackIndex);
        unboundedStack_push(self, val);
    } else {
        ++self->pointersIn;
        stack_push(self->currentStack, val);
    }
}

pointer unboundedStack_pull(unboundedStack *self)
{
    if (stack_isEmpty(self->currentStack)) {
        if (self->currentStackIndex == 0) {
            return null;
        }
        --self->currentStackIndex;
        self->currentStack = *(self->stackArray + self->currentStackIndex);
        return unboundedStack_pull(self);
    } else {
        if (--self->pointersIn < 0) {
            d("too many pointers pulled.");
            terminate(0);
        }
        return stack_pull(self->currentStack);
    }
}

void unboundedStack_finalize(unboundedStack *self)
{
    if (self->stackArray != null) {
        unsigned int k;
        stack **bStack = self->stackArray;
        for (k = 0; k < self->stackArraySize; k++) {
            stack_delete(bStack);
            ++bStack;
        }
        free(self->stackArray);
        self->stackArray = null;
    }
}

boolean unboundedStack_initialize(unboundedStack *self, memSize initialSize)
{
    boolean ok = false;
    self->largestStackSize = initialSize;
    self->stackArraySize = 1;
    self->stackArray = (stack **)malloc(sizeof(stack *) * self->stackArraySize);
    if (self->stackArray == null) {
        d("malloc returned null.");
        goto done;
    }
    self->currentStackIndex = 0;
    *self->stackArray = stack_new(initialSize);
    self->currentStack = *self->stackArray;
    self->pointersIn = 0;
    ok = true;
done:
    return ok;
}

void unboundedStack_delete(unboundedStack **self)
{
    unboundedStack_finalize(*self);
    free(*self);
    *self = null;
}

unboundedStack *unboundedStack_new(memSize initialSize)
{
    unboundedStack *self = null;
    self = (unboundedStack *)malloc(sizeof(unboundedStack));
    if (self != null) {
        if (!unboundedStack_initialize(self, initialSize)) {
            unboundedStack_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-------------------------------- allocator ----------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

memSize allocator_memoryUsed(allocator *self)
{
    return self->byteSize * self->size;
}

boolean allocator_isFull(allocator *self) { return (self->pC == self->pF); }

void *allocator_getMemory(allocator *self)
{
    void *result;
    result = self->pC;
    self->pC += self->byteSize;
    return result;
}

void allocator_finalize(allocator *self)
{
    if (self->data != null) {
        free(self->data);
        self->data = null;
    }
}

boolean allocator_initialize(allocator *self, memSize size, memSize byteSize)
{
    boolean ok = false;
    self->size = size;
    self->byteSize = byteSize;
    if (self->byteSize % 8 != 0) {
        d("byteSize is not 8 byte allignment compatible");
        terminate(0);
    }
    self->data = null;
    (void)posix_memalign((void **)&self->data, 32, self->byteSize * self->size);
    if ((long)self->data % 32 != 0) {
        d("Memory is not 32 byte alligned");
        terminate(0);
    }
    if (self->data == null) {
        d("malloc returned null.");
        goto done;
    }
    self->pI = (char *)self->data;
    self->pC = (char *)self->data;
    self->pF = self->pC + self->size * self->byteSize;

    ok = true;
done:
    return ok;
}

void allocator_delete(allocator **self)
{
    allocator_finalize(*self);
    free(*self);
    *self = null;
}

allocator *allocator_new(memSize size, memSize byteSize)
{
    allocator *self = null;
    self = (allocator *)malloc(sizeof(allocator));
    if (self != null) {
        if (!allocator_initialize(self, size, byteSize)) {
            allocator_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*----------------------------- unboundedAllocator ----------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

memSize unboundedAllocator_memoryUsed(unboundedAllocator *self)
{
    if (self->concurrent) omp_set_lock(&self->lock);
    memSize memoryUsed = sizeof(allocator *) * self->allocatorArraySize;
    unsigned int k;
    allocator **anAllocator = self->AllocatorArray;
    for (k = 0; k < self->allocatorArraySize; k++) {
        memoryUsed += allocator_memoryUsed(*anAllocator) + sizeof(allocator);
        ++anAllocator;
    }
    memoryUsed +=
        unboundedStack_memoryUsed(self->theStack) + sizeof(unboundedStack);
    if (self->concurrent) omp_unset_lock(&self->lock);
    return memoryUsed;
}

boolean unboundedAllocator_allReturned(unboundedAllocator *self)
{
    return (self->allocationsOut == 0);
}

void unboundedAllocator_extend(unboundedAllocator *self)
{
    ++self->allocatorArraySize;
    self->largestAllocatorSize *= 2;
    self->AllocatorArray = (allocator **)realloc(
        self->AllocatorArray, sizeof(allocator *) * self->allocatorArraySize);
    if (self->AllocatorArray == null) {
        d("realloc returned null.");
        terminate(0);
    }
    *(self->AllocatorArray + (self->allocatorArraySize - 1)) =
        allocator_new(self->largestAllocatorSize, self->byteSize);
}

void unboundedAllocator_returnMemory(unboundedAllocator *self, void **pMemory)
{
    if (self->concurrent) omp_set_lock(&self->lock);
    if (--self->allocationsOut < 0) {
        d("too many memory areas returned.");
        terminate(0);
    }
    unboundedStack_push(self->theStack, (pointer)*pMemory);
    *pMemory = null;
    if (self->concurrent) omp_unset_lock(&self->lock);
}

void *unboundedAllocator_getMemory(unboundedAllocator *self)
{
    void *retVal;
    if (self->concurrent) omp_set_lock(&self->lock);
    ++self->allocationsOut;
    if (!unboundedStack_isEmpty(self->theStack)) {
        retVal = (void *)unboundedStack_pull(self->theStack);
        if (self->concurrent) omp_unset_lock(&self->lock);
        return retVal;
    }
    if (allocator_isFull(self->currentAllocator)) {
        unboundedAllocator_extend(self);
        self->currentAllocator =
            *(self->AllocatorArray + self->allocatorArraySize - 1);
    }
    ++self->totalAllocations;
    retVal = allocator_getMemory(self->currentAllocator);
    if (self->concurrent) omp_unset_lock(&self->lock);
    return retVal;
}

void unboundedAllocator_finalize(unboundedAllocator *self)
{
    if (self->AllocatorArray != null) {
        unsigned int k;
        allocator **anAllocator = self->AllocatorArray;
        for (k = 0; k < self->allocatorArraySize; k++) {
            allocator_delete(anAllocator);
            ++anAllocator;
        }
        free(self->AllocatorArray);
        self->AllocatorArray = null;
    }

    if (self->theStack != null) {
        unboundedStack_delete(&self->theStack);
    }

    if (self->concurrent) omp_destroy_lock(&self->lock);
}

boolean unboundedAllocator_initialize(
    unboundedAllocator *self, memSize initialSize, memSize byteSize,
    boolean concurrent)
{
    boolean ok = false;
    self->byteSize = byteSize;
    self->largestAllocatorSize = initialSize;
    self->allocatorArraySize = 1;
    self->AllocatorArray =
        (allocator **)malloc(sizeof(allocator *) * self->allocatorArraySize);
    if (self->AllocatorArray == null) {
        d("malloc returned null.");
        goto done;
    }
    *self->AllocatorArray = allocator_new(initialSize, self->byteSize);
    self->currentAllocator = *self->AllocatorArray;
    self->theStack = unboundedStack_new(initialSize);
    self->allocationsOut = 0;
    self->totalAllocations = 0;
    self->concurrent = concurrent;
    if (self->concurrent) omp_init_lock(&self->lock);
    ok = true;
done:
    return ok;
}

void unboundedAllocator_delete(unboundedAllocator **self)
{
    unboundedAllocator_finalize(*self);
    free(*self);
    *self = null;
}

unboundedAllocator *unboundedAllocator_new(
    memSize initialSize, memSize byteSize, boolean concurrent)
{
    unboundedAllocator *self = null;
    self = (unboundedAllocator *)malloc(sizeof(unboundedAllocator));
    if (self != null) {
        if (!unboundedAllocator_initialize(
                self, initialSize, byteSize, concurrent)) {
            unboundedAllocator_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*---------------------------------- cbar -------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

cbarHeaderCbarLength cbar_getSize(cbarHead * cbar) {
    if (cbar == null) { return 0; }
    return *(cbarHeaderCbarLength *) ((char *) cbar + cbarHeaderCbarLength_Offset);
}

void cbar_setSize(cbarHead * cbar, cbarHeaderCbarLength size) {
    *(cbarHeaderCbarLength *) ((char *) cbar + cbarHeaderCbarLength_Offset) = size;
}

cbarHeaderCbarMaxLength cbar_getMaxSize(cbarHead * cbar) {
    if (cbar == null) { return 0; }
    return *(cbarHeaderCbarMaxLength *) ((char *) cbar + cbarHeaderCbarMaxLength_Offset);
}

void cbar_setMaxSize(cbarHead * cbar, cbarHeaderCbarMaxLength maxSize) {
    *(cbarHeaderCbarMaxLength *) ((char *) cbar + cbarHeaderCbarMaxLength_Offset) = maxSize;
}

cbarHeaderLastByteOffset cbar_getLastByteOffset(cbarHead * cbar) {
    if (cbar == null) { return 0; }
    return *(cbarHeaderLastByteOffset *) ((char *) cbar + cbarHeaderLastByteOffset_Offset);
}

void cbar_setLastByteOffset(cbarHead * cbar, cbarHeaderLastByteOffset lastByteOffset) {
    *(cbarHeaderLastByteOffset *) ((char *) cbar + cbarHeaderLastByteOffset_Offset) = lastByteOffset;
}

cbarHeaderLastSequenceLength cbar_getLastSequenceLength(cbarHead * cbar) {
    if (cbar == null) { return 0; }
    return *(cbarHeaderLastSequenceLength *) ((char *) cbar + cbarHeaderLastSequenceLength_Offset);
}

/* corresponds to length + 1 rather than length */
void cbar_setLastSequenceLength(cbarHead * cbar, cbarHeaderLastSequenceLength lastSequenceLength) {
    *(cbarHeaderLastSequenceLength *) ((char *) cbar + cbarHeaderLastSequenceLength_Offset) = lastSequenceLength;
}

cbarHeaderFirstAuxInt cbar_getFirstAuxInt(cbarHead * cbar) {
    if (cbar == null) { return 0; }
    return *(cbarHeaderFirstAuxInt *) ((char *) cbar + cbarHeaderFirstAuxInt_Offset);
}

void cbar_setFirstAuxInt(cbarHead * cbar, cbarHeaderFirstAuxInt auxInt) {
    *(cbarHeaderFirstAuxInt *) ((char *) cbar + cbarHeaderFirstAuxInt_Offset) = auxInt;
}

void cbar_print(cbarHead * cbar) {
    osUnsignedLong k;
    osUnsignedLong size = *((osUnsignedLong *) cbar);
    unsigned char * j = (unsigned char *) cbar + cbarHeaderSize;
    printf("cbar size %llu:", size);
    for (k = cbarHeaderSize; k < size; ++k) {
        printf("%d,", *(j++));
    }
    printf("\n\n");
}

void cbar_ensureLength(cbarHead ** cbar, osUnsignedLong newSize, generalCbarManager * manager, cbarHeaderCbarLength length) {
    if (*cbar == null) {
        d("null cbar");
        terminate(0);
    }

    {
        osUnsignedLong maxLength = cbar_getMaxSize(*cbar);
        cbarHead * replacement;

        if (newSize < maxLength) {
            d("invalid extended zize");
            terminate(0);
        } else if (newSize == maxLength) {
            return;
        }

        replacement = generalCbarManager_getCbar(manager, newSize);

        memcpy(replacement, *cbar, (size_t) length);

        cbar_setMaxSize(replacement, newSize);

        generalCbarManager_returnCbar(manager, cbar);
        *cbar = replacement;
    }
}

/*------------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * ----------------------------------------------------------------------------*/

void cbarReader_reset(cbarReader * self) {
    self->i = self->cbar;
    self->f = self->i + cbar_getSize(self->cbar);;

    if (self->cbar !=null) {
        self->x = self->cbar + cbarHeaderSize;
    } else {
        self->x = null;
    }

    self->lsf = self->x;

    self->charOffset = 0;
    self->xValResidue = 0;
    self->inCharIndex = 0;
    self->currentIndex = 0;
    self->bitflag = 0;
    self->moveforward = false;
}

void cbarReader_set(cbarReader * self, cbarHead * onCbar) {
    self->cbar = onCbar;
    cbarReader_reset(self);
}

boolean cbarReader_nextItem(cbarReader * self) {
    if (self->cbar == null) { return false; }
    unsigned char charval;

    if (self->xValResidue != 0) {
        while (self->bitflag != 0) {
            if (self->xValResidue & self->bitflag) {
                self->currentIndex = 8 * self->charOffset + self->inCharIndex;
                ++self->inCharIndex;
                if (self->xValResidue <= (2 * self->bitflag - 1)) {
                    self->xValResidue = 0;
                }
                self->bitflag <<= 1;
                return true;
            }
            ++self->inCharIndex;
            self->bitflag <<= 1;
        }
        self->xValResidue = 0;
    }

    if (self->moveforward)  {
        ++self->x;
        ++self->charOffset;
        self->moveforward = false;
    }

    while (self->x < self->lsf) {
        self->xValResidue = *self->x;
        self->inCharIndex = 0;
        self->bitflag = 1;
        self->moveforward = true;
        // prefetch(addr, read:[0] / write:1, cache persistance: 0 (low) - [3] (high)
        __builtin_prefetch((const char *)self->x + CACHE_LINE, 1);
        __builtin_prefetch((const char *)self->x + 2 * CACHE_LINE, 1);
        __builtin_prefetch((const char *)self->x + 3 * CACHE_LINE, 1);

        return cbarReader_nextItem(self);
    }

    while (self->x < self->f) {
        charval = *(self->x);
        if (isLiteralCounterChar(charval)) {
            unsigned int numberOfChars = literalCounterValue(self->x);
            self->x += 2;
            if (numberOfChars == 0) {
                d("inconsistent compression, non-null char counter is 0");
                terminate(0);
            }
            self->lsf = self->x + numberOfChars;

            __builtin_prefetch((const char *)self->lsf, 1);

            if (self->lsf > self->f) {
                d("inconsistent reading out of scope");
                terminate(0);
            }
            return cbarReader_nextItem(self);
        } else if (isEmptyCounter(charval)) {
            self->charOffset += emptyCounterValue(self->x);
            self->x += 2;
        } else if (canBeWrtittenAsIsolatedChar(charval)) {
           self->xValResidue = charval;
           self->inCharIndex = 0;
           self->bitflag = 1;
           self->moveforward = true;
           return cbarReader_nextItem(self);
        } else {
            d("inconsistent compression, unrecognized token");
            terminate(0);
        }
    }
    return false;
}

#define cbarReated_inASequence(readervar) \
    ((readervar)->x < (readervar)->lsf)

boolean cbarReader_nextByte(cbarReader * self) {
    unsigned char charval;
    if (self->cbar == null) { return false; }

restart:
    if (self->moveforward)  {
        ++self->x;
        ++self->charOffset;
        self->moveforward = false;
    }

    if (cbarReated_inASequence(self)) {
        self->moveforward = true;
        // prefetch(addr, read:[0] / write:1, cache persistance: 0 (low) - [3] (high)
        __builtin_prefetch((const char *)self->x, 1);
        __builtin_prefetch((const char *)self->x + CACHE_LINE, 1);
        __builtin_prefetch((const char *)self->x + 2 * CACHE_LINE, 1);
        __builtin_prefetch((const char *)self->x + 3 * CACHE_LINE, 1);
        if (*self->x == 0) {
            goto restart;
        } else {
            return true;
        }
    }

inloop:
    if (self->x < self->f) {
        charval = *(self->x);

        if (isLiteralCounterChar(charval)) {
            unsigned int numberOfChars = literalCounterValue(self->x);
            self->x += 2;
            if (numberOfChars == 0) {
                d("inconsistent compression, non-null char counter is 0");
                terminate(0);
            }
            self->lsf = self->x + numberOfChars;

            __builtin_prefetch((const char *)self->lsf, 1);

            if (self->lsf > self->f) {
                d("inconsistent reading out of scope");
                terminate(0);
            }
            goto restart;
        } else if (isEmptyCounter(charval)) {
            self->charOffset += emptyCounterValue(self->x);
            self->x += 2;
            goto inloop;
        } else if (canBeWrtittenAsIsolatedChar(charval)) {
           self->moveforward = true;
           if (charval == 0) {
                goto restart;
            } else {
                return true;
            }
        } else {
            d("inconsistent compression, unrecognized token");
            terminate(0);
        }
    }
    return false;
}

unsigned int cbarReader_currentItem(cbarReader * self) {
    return self->currentIndex;
}

osLong cbarReader_currentByteOffset(cbarReader * self) {
    return self->charOffset;
}

unsigned int cbarReader_currentByte(cbarReader * self) {
    return *(self->x);
}

void cbarReader_setAndExecuteOnEachItem(cbarReader * self, cbarHead * onCbar, void (*fnc)(int index, cbarHead * onCbar, void * data), void * data) {
    self->cbar = onCbar;
    if (self->cbar !=null) {
        cbarReader_reset(self);
        while (cbarReader_nextItem(self)) {
            fnc(cbarReader_currentItem(self), onCbar, data);
        }
    }
}

/*------------------------------------------------------------------------------
 * -----------------------------------------------------------------------------
 * ----------------------------------------------------------------------------*/

boolean generalCbarManager_initialize(generalCbarManager * self, int initialSize) {
    (void)initialSize;
    self->countOut = 0;
    self->initialSize = 0;
    self->memoryUsed = 0;
    return true;
}

void generalCbarManager_finalize(generalCbarManager * self) {
    (void)self;
}

generalCbarManager * generalCbarManager_new(int initialSize) {
    generalCbarManager * self = null;
    self = (generalCbarManager *) malloc(sizeof(generalCbarManager));
    if (self != null) {
        if (!generalCbarManager_initialize(self, initialSize)) {
            generalCbarManager_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

void generalCbarManager_delete(generalCbarManager ** self) {
    generalCbarManager_finalize(*self);
    free(*self);
    *self = null;
}

long long generalCbarManager_memoryUsed(generalCbarManager * self) {
    return self->memoryUsed;
}

cbarHead * generalCbarManager_getCbar(generalCbarManager * self, osUnsignedLong cbarLength) {

    cbarHead * result = null;
    (void)posix_memalign((void **) &result, 32, (size_t) cbarLength);

    if (result == null) {
        d("out of memory for %llu bytes", cbarLength);
        terminate(0);
    }

    cbar_setSize(result, 0);
    cbar_setMaxSize(result, cbarLength);
    cbar_setLastByteOffset(result, -1);
    cbar_setLastSequenceLength(result, 0);
    cbar_setFirstAuxInt(result, -1);

    #pragma omp atomic update
    self->memoryUsed += cbarLength;
    #pragma omp atomic update
    ++self->countOut;
    return result;
}

void generalCbarManager_returnCbar(generalCbarManager * self, cbarHead ** pHead) {
    if (*pHead != null)  {
        #pragma omp atomic update
        self->memoryUsed -= cbar_getMaxSize(*pHead);
        free(*pHead);
        *pHead = null;
        #pragma omp atomic update
        --self->countOut;
    }
}

int generalCbarManager_countCbarsOut(generalCbarManager * self) {
    return self->countOut;
}

boolean generalCbarManager_allReturned(generalCbarManager * self) {
    return (self->countOut == 0);
}

void cbarWriter_set(cbarWriter * self,  cbarHead ** onPtCbar, generalCbarManager * memoryManager) {
    self->ptCbar = onPtCbar;
    self->cbar = *self->ptCbar;
    self->manager = memoryManager;
    self->outCbar = null;
}

void cbarWriter_internalIni(cbarWriter * self, osUnsignedLong length) {
    self->outCbar = generalCbarManager_getCbar(self->manager, length);
    if (self->outCbar == null) {
        d("out of memory");
        terminate(0);
    }
    self->byteOffset = -1;
    self->max = self->outCbar + length;
    self->shortSequenceStart = (unsigned char *) self->outCbar + cbarHeaderSize;
    self->i = self->shortSequenceStart;
}

void cbarWriter_cloneFrom(cbarWriter * self, cbarHead * source) {
    if (source != null) {
        boolean needNewCbar = false;
        osUnsignedLong sourceLength = cbar_getSize(source);
        osUnsignedLong selfMaxLength = cbar_getMaxSize(self->cbar);
        if (sourceLength <= 0) { d("invalid cbar length 0"); terminate(0); }

        needNewCbar = (self->cbar == null)
                || (selfMaxLength < sourceLength)
                || (selfMaxLength > EXTRA_SIZE_ALLOWED * sourceLength);

        if (needNewCbar) {
            generalCbarManager_returnCbar(self->manager, self->ptCbar);
            *self->ptCbar = generalCbarManager_getCbar(self->manager, sourceLength);
            self->cbar = *self->ptCbar;
        }

        memcpy(self->cbar, source, (size_t) sourceLength);
        if (needNewCbar) {
            cbar_setMaxSize(self->cbar, sourceLength);
        } else {
            cbar_setMaxSize(self->cbar, selfMaxLength);
        }
    }
}

void cbarWriter_manageExtension(cbarWriter * self, osUnsignedLong ensureExtra) {
    boolean same = (self->outCbar == self->cbar);
    osLong length =  self->i - self->outCbar;
    osLong gapToSequenceStart = self->shortSequenceStart - self->outCbar;

    if (gapToSequenceStart < 0) {
        d("gapToSequenceStart");
        terminate(0);
    }

    cbar_ensureLength(&self->outCbar, max(EXTRA_SIZE_ALLOWED * length, length + ensureExtra), self->manager, length);

    self->max = self->outCbar + cbar_getMaxSize(self->outCbar);

    if (self->shortSequenceStart != null) {
        self->shortSequenceStart = gapToSequenceStart + self->outCbar;
    }

    self->i = (osUnsignedLong) length + self->outCbar;

    if (same) {
        self->cbar = self->outCbar;
        *self->ptCbar = self->cbar;
    }
}

#define cbarWriter_ensureTwoBytes(awriter) \
    if ((awriter)->i + 1 >= (awriter)->max) { \
        cbarWriter_manageExtension(awriter, 2); \
    }

void cbarWriter_closeSequenceIfNeeded(cbarWriter * self, boolean * countingPt, osUnsignedLong emptyBytes, boolean forceClose) {
    unsigned int substringLength = 0;

    if (*countingPt) {
        substringLength = (self->i - 1 - (self->shortSequenceStart + 1));
        if (substringLength >= sequenceMaxCapacity) {
            d("state corrupted %d", substringLength);
            terminate(0);
        } else if (substringLength == sequenceMaxCapacity - 1) {
            forceClose = true;
        }
    }

    if ((emptyBytes > 0) || forceClose) {
        if (*countingPt) {
            addLiteralCounterChar(substringLength, self->shortSequenceStart);
            *countingPt = false;
        }
        if (emptyBytes > 0) {
            addEmptyBytes(emptyBytes, self->i, cbarWriter_ensureTwoBytes(self));
        }
        self->shortSequenceStart = self->i;
    }
}

#define cbarWriter_isCounting(self) \
    ((self)->i != (self)->shortSequenceStart)


void cbarWriter_pushLiteralSequence(cbarWriter * self, osLong byteOffset, unsigned char * sequence, cbarHeaderLastSequenceLength sequenceLength) {
    osLong shift = byteOffset - self->byteOffset;

    if (shift < 0) {
        d("shift < 0");
        terminate(0);
    }

    if (sequenceLength <= 0) {
        d("sequenceLength <= 0");
        terminate(0);
    }

    if ((shift > 1) && (shift <= 4)) {
        unsigned int zero = 0;
        cbarWriter_pushLiteralSequence(self, byteOffset - shift, (unsigned char *) &zero, shift - 1);
        shift = 0;
    }

    {
        boolean counting = cbarWriter_isCounting(self);
        boolean isolatedChar = ((sequenceLength == 1) && canBeWrtittenAsIsolatedChar(*sequence));
        cbarHeaderLastSequenceLength effectiveSequenceLength = sequenceLength;

        if ((shift > 1) || counting) {
            cbarWriter_closeSequenceIfNeeded(self, &counting, (shift > 1)? shift - 1 : 0, false);
        }

        if (!counting && !isolatedChar) {
            self->shortSequenceStart = self->i;
            self->i += 2;
            counting = true;
        }

        if (counting) {
            effectiveSequenceLength = min(sequenceMaxCapacity - 1 - (self->i - 1 - (self->shortSequenceStart + 1)), sequenceLength);
        }

        if (self->i + effectiveSequenceLength > self->max) {
            cbarWriter_manageExtension(self, effectiveSequenceLength);
        }

        if (effectiveSequenceLength == 1) {
            *self->i = *sequence;
        } else {
            copySmallSequence(self->i, sequence, (size_t)effectiveSequenceLength);
        }
        self->i += effectiveSequenceLength;

        if (!counting) {
            self->shortSequenceStart = self->i;
        }
        self->byteOffset = byteOffset + (effectiveSequenceLength - 1);

        if (effectiveSequenceLength != sequenceLength) {
            cbarWriter_pushLiteralSequence(self, self->byteOffset + 1, sequence + effectiveSequenceLength, sequenceLength - effectiveSequenceLength);
        }
    }
}

void cbarWriter_pushByte(cbarWriter * self, osLong byteOffset, unsigned char byte) {
    cbarWriter_pushLiteralSequence(self, byteOffset, &byte, 1);
}

void cbarWriter_close(cbarWriter * self) {
    boolean counting = cbarWriter_isCounting(self);
    boolean needsCopy = true;
    cbarHeaderLastSequenceLength lastSequenceLength = 0;

    if (self->i > self->max) {
        d("exceeds max limit");
        terminate(0);
    }

    if (counting) {
      lastSequenceLength = (cbarHeaderLastSequenceLength) (self->i - 1- (self->shortSequenceStart + 1));
    }

    if ((lastSequenceLength < 0) || (lastSequenceLength  >= sequenceMaxCapacity)) {
        d("lastSequenceLength");
        terminate(0);
    }
    cbar_setLastSequenceLength(self->outCbar, lastSequenceLength);
    if (counting) {
        cbarWriter_closeSequenceIfNeeded(self, &counting, 0, true);
    }

    {
        osUnsignedLong length =  self->i - self->outCbar;
        if (length <= 0) { d("invalid cbar length 0"); terminate(0); }

        if (length == cbarHeaderSize) {
            if (*self->ptCbar != self->outCbar) {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
                generalCbarManager_returnCbar(self->manager, &self->outCbar);
            } else {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
                self->outCbar = null;
            }
            self->cbar = null;
            *self->ptCbar = null;
            return;
        }

        if (cbar_getMaxSize(self->cbar) < EXTRA_SIZE_ALLOWED * length) {
            needsCopy = false;
        }

        if (needsCopy) {
            if (*self->ptCbar != self->outCbar) {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
            }
            self->cbar = generalCbarManager_getCbar(self->manager, length);
            *self->ptCbar =  self->cbar ;
            memcpy(self->cbar, self->outCbar, (size_t) length);
            cbar_setMaxSize(self->cbar, length);
            generalCbarManager_returnCbar(self->manager, &self->outCbar);
            self->outCbar = null;
        } else {
            if (self->cbar != self->outCbar) {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
                *self->ptCbar = self->outCbar;
                self->cbar = *self->ptCbar;
            }
        }

        cbar_setSize(self->cbar, length);
    }

    cbar_setLastByteOffset(self->cbar, self->byteOffset);
}

boolean cbarWriter_addCbar(cbarWriter * self, cbarHead * sourceCbar) {
    if (sourceCbar == null) {
        return false;
    }

    if (self->cbar == null) {
        cbarWriter_cloneFrom(self, sourceCbar);
        return true;
    }

    {
        boolean writing = (cbar_getSize(self->cbar) < cbar_getSize(sourceCbar));
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        cbarHeaderLastSequenceLength numberOfCharsA = 0;
        cbarHeaderLastSequenceLength numberOfCharsB = 0;
        boolean readA;
        boolean readB;
        boolean retVal = false;
        osUnsignedLong length = 0;
        unsigned char addition;
        unsigned long long additionLL;
        short k;

startpoint:
        if (writing) {
            length = max(cbar_getSize(self->cbar), cbar_getSize(sourceCbar)) * EXTRA_SIZE_ALLOWED;
            cbarWriter_internalIni(self, length);

        }

        cbarReader_set(&self->reader, self->cbar);
        cbarReader_set(&readerB, sourceCbar);

        AisFinished = !cbarReader_nextByte(&self->reader);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!(AisFinished && BisFinished)) {
            readA = !AisFinished && (BisFinished || (self->reader.charOffset <= readerB.charOffset));
            readB = !BisFinished && (AisFinished || (readerB.charOffset <= self->reader.charOffset));

            if (readA && !readB) {
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                if (!BisFinished) {
                    numberOfCharsA = min(numberOfCharsA, readerB.charOffset - self->reader.charOffset);
                }

                if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, numberOfCharsA);
                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
            } else if (readB && !readA) {
                retVal = true;
                if (!writing) {
                    writing = true;
                    goto startpoint;
                }

                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                if (!AisFinished) {
                    numberOfCharsB = min(numberOfCharsB,  self->reader.charOffset - readerB.charOffset);
                }

                if (writing) cbarWriter_pushLiteralSequence(self, readerB.charOffset, readerB.x, numberOfCharsB);

                readerB.x += numberOfCharsB;
                readerB.charOffset += numberOfCharsB;
                readerB.moveforward = false;

                BisFinished = !cbarReader_nextByte(&readerB);

            } else if (readB && readA) {
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                numberOfCharsA = min(numberOfCharsA, numberOfCharsB);
                numberOfCharsB = numberOfCharsA;

                if ((numberOfCharsA > 1) || writing) {
                    for (k = 0; k < numberOfCharsA; ++k) {
                        if ((k + (short)sizeof(additionLL)) < numberOfCharsA) {
                            additionLL = (*(typeof(additionLL) *)(self->reader.x + k) | *(typeof(additionLL) *)(readerB.x + k));
                            if (!retVal) {
                                if (*(typeof(additionLL) *)(self->reader.x + k) != additionLL) {
                                    retVal = true;
                                };
                            }
                            *(typeof(additionLL) *)(self->reader.x + k) = additionLL;
                            k += sizeof(additionLL) - 1;
                        } else {
                            addition = (*(self->reader.x + k) | *(readerB.x + k));
                            if (!retVal) {
                                if (*(self->reader.x + k) != addition) {
                                    retVal = true;
                                };
                            }
                            *(self->reader.x + k) = addition;
                        }
                    }
                } else {
                    addition = (*(self->reader.x) | *(readerB.x));
                    if (*(self->reader.x) != addition) {
                        retVal = true;
                        if (!writing) {
                            if (!canBeWrtittenAsIsolatedChar(addition)) {
                                writing = true;
                                goto startpoint;
                            }
                        }
                    };
                    *(self->reader.x) = addition;
                }

                if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, numberOfCharsA);

                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                readerB.x += numberOfCharsB;
                readerB.charOffset += numberOfCharsB;
                readerB.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
                BisFinished = !cbarReader_nextByte(&readerB);
            }

            if (BisFinished && (!retVal || !writing)) {
                if (writing) {
                    generalCbarManager_returnCbar(self->manager, &self->outCbar);
                }
                return retVal;
            }
        }

        if (writing) {
            cbarWriter_close(self);
        }
        self->outCbar = null;

        return retVal;
    }
}

boolean cbarWriter_intersectCbar(cbarWriter * self, cbarHead * sourceCbar) {
    if (self->cbar == null) { return false; }
    if (sourceCbar == null) {
        generalCbarManager_returnCbar(self->manager, self->ptCbar);
        self->cbar = null;
        return true;
    }

    {
        boolean writing = (cbar_getSize(self->cbar) > cbar_getSize(sourceCbar));
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        boolean readA;
        boolean readB;
        boolean retVal = false;
        boolean content = false;
        unsigned char intersection;
        unsigned long long intersectionLL;
        cbarHeaderLastSequenceLength numberOfCharsA = 0;
        cbarHeaderLastSequenceLength numberOfCharsB = 0;
        osUnsignedLong length = 0;
        short k;

startpoint:
        if (writing) {
            length = SMALL_EXTRA_SIZE_ALLOWED * cbar_getSize(self->cbar);
            cbarWriter_internalIni(self, length);
        }

        cbarReader_set(&self->reader, self->cbar);
        cbarReader_set(&readerB, sourceCbar);

        AisFinished = !cbarReader_nextByte(&self->reader);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!(AisFinished || BisFinished)) {
            readA = (self->reader.charOffset <= readerB.charOffset);
            readB = (readerB.charOffset <= self->reader.charOffset);

            if (readA && !readB) {
                retVal = true;
                if (!writing) {
                    writing = true;
                    goto startpoint;
                }
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                if (!BisFinished) {
                    numberOfCharsA = min(numberOfCharsA, readerB.charOffset - self->reader.charOffset);
                }

                /* nothing to push */
                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
            } else if (readB && !readA) {
                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                if (!AisFinished) {
                    numberOfCharsB = min(numberOfCharsB,  self->reader.charOffset - readerB.charOffset);
                }

                /* nothing to push */
                readerB.x += numberOfCharsB;
                readerB.charOffset += numberOfCharsB;
                readerB.moveforward = false;

                BisFinished = !cbarReader_nextByte(&readerB);
            } else if (readB && readA) {
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                numberOfCharsA = min(numberOfCharsA, numberOfCharsB);

                for (k = 0; k < numberOfCharsA; ++k) {
                    if ((k + (short)sizeof(intersectionLL)) < numberOfCharsA) {
                        intersectionLL = (*(typeof(intersectionLL) *)(self->reader.x + k) &  *(typeof(intersectionLL) *)(readerB.x + k));
                        if (!retVal) {
                            if (*(typeof(intersectionLL) *)(self->reader.x + k) != intersectionLL) {
                                retVal = true;
                                if (!writing) {
                                    writing = true;
                                    goto startpoint;
                                }
                            };
                        }
                        if (intersectionLL == 0) {
                            numberOfCharsA = k + sizeof(intersectionLL);
                            break;
                        } else {
                            content = true;
                        }
                        *(typeof(intersectionLL) *)(self->reader.x + k) = intersectionLL;
                        k += sizeof(intersectionLL) - 1;
                    } else {
                        intersection = (*(self->reader.x + k) & *(readerB.x + k));
                        if (!retVal) {
                            if (*(self->reader.x + k) != intersection) {
                                retVal = true;
                                if (!writing) {
                                    writing = true;
                                    goto startpoint;
                                }
                            };
                        }
                        if (intersection == 0) {
                            numberOfCharsA = k + 1;
                            break;
                        } else {
                            content = true;
                        }
                        *(self->reader.x + k) = intersection;
                    }
                }
                if (k > 0) {
                    if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, k);
                }

                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                readerB.x += numberOfCharsA;
                readerB.charOffset += numberOfCharsA;
                readerB.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
                BisFinished = !cbarReader_nextByte(&readerB);
            }
        }
        if (!AisFinished) {
            retVal = true;
            if (!writing) {
                writing = true;
                goto startpoint;
            }
        }

        if (!retVal) {
            if (writing) {
                generalCbarManager_returnCbar(self->manager, &self->outCbar);
            }
            return false;
        }

        if (content) {
            cbarWriter_close(self);
            self->outCbar = null;
        } else {
            if (self->i > self->max) {
                d("exceeds max limit");
                terminate(0);
            }
            if (*self->ptCbar != self->outCbar) {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
                generalCbarManager_returnCbar(self->manager, &self->outCbar);
            } else {
                generalCbarManager_returnCbar(self->manager, self->ptCbar);
                self->outCbar = null;
            }
            self->cbar = null;
        }

        return retVal;
    }
}


boolean cbar_isDisjoint(cbarHead * cbarA, cbarHead * cbarB) {
    if ((cbarA == NULL) || (cbarB == NULL)) { return true; }
    if (cbarA == cbarB) { return false; }

    {
        cbarReader readerA;
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        boolean readA;
        boolean readB;
        unsigned char intersection;

        cbarReader_set(&readerA, cbarA);
        cbarReader_set(&readerB, cbarB);

        AisFinished = !cbarReader_nextByte(&readerA);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!(AisFinished || BisFinished)) {
            readA = (readerA.charOffset <= readerB.charOffset);
            readB = (readerB.charOffset <= readerA.charOffset);

            if (readA && !readB) {
                AisFinished = !cbarReader_nextByte(&readerA);
            } else if (readB && !readA) {
                BisFinished = !cbarReader_nextByte(&readerB);
            } else if (readB && readA) {
                intersection = (*(readerA.x) & *(readerB.x));
                if (intersection != 0) {
                    return false;
                }
                AisFinished = !cbarReader_nextByte(&readerA);
                BisFinished = !cbarReader_nextByte(&readerB);
            }
        }
        return true;
    }
}


boolean cbarWriter_subtractCbar(cbarWriter * self, cbarHead * sourceCbar) {
    if (self->cbar == null) { return false; }
    if (sourceCbar == null) { return false; }

    {
        boolean writing = false;
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        boolean readA;
        boolean readB;
        boolean retVal = false;
        boolean content = false;
        unsigned char subtraction;
        unsigned long long subtractionLL;
        cbarHeaderLastSequenceLength numberOfCharsA = 0;
        cbarHeaderLastSequenceLength numberOfCharsB = 0;
        osUnsignedLong length = 0;
        short k;

startpoint:
        if (writing) {
            length = SMALL_EXTRA_SIZE_ALLOWED * cbar_getSize(self->cbar);
            cbarWriter_internalIni(self, length);
        }

        cbarReader_set(&self->reader, self->cbar);
        cbarReader_set(&readerB, sourceCbar);

        AisFinished = !cbarReader_nextByte(&self->reader);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!AisFinished) {
            readA = !AisFinished && (BisFinished || (self->reader.charOffset <= readerB.charOffset));
            readB = !BisFinished && (AisFinished || (readerB.charOffset <= self->reader.charOffset));

            if (readA && !readB) {
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                if (!BisFinished) {
                    numberOfCharsA = min(numberOfCharsA, readerB.charOffset - self->reader.charOffset);
                }

                if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, numberOfCharsA);
                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
                content = true;
            } else if (readB && !readA) {
                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                if (!AisFinished) {
                    numberOfCharsB = min(numberOfCharsB,  self->reader.charOffset - readerB.charOffset);
                }
                /* nothing to push */
                readerB.x += numberOfCharsB;
                readerB.charOffset += numberOfCharsB;
                readerB.moveforward = false;

                BisFinished = !cbarReader_nextByte(&readerB);
            } else if (readB && readA) {
                numberOfCharsA = max(self->reader.lsf - self->reader.x, 1);
                numberOfCharsB = max(readerB.lsf - readerB.x, 1);
                numberOfCharsA = min(numberOfCharsA, numberOfCharsB);

                for (k = 0; k < numberOfCharsA; ++k) {
                    if ((k + (short)sizeof(subtractionLL)) < numberOfCharsA) {
                        subtractionLL = (*(typeof(subtractionLL) *)(self->reader.x + k) &  ~*(typeof(subtractionLL) *)(readerB.x + k));
                        if (!retVal) {
                            if (*(typeof(subtractionLL) *)(self->reader.x + k) != subtractionLL) {
                                retVal = true;
                                if (!writing) {
                                    writing = true;
                                    goto startpoint;
                                }
                            };
                        }
                        if (subtractionLL == 0) {
                            numberOfCharsA = k + sizeof(subtractionLL);
                            break;
                        } else {
                            content = true;
                        }
                        *(typeof(subtractionLL) *)(self->reader.x + k) = subtractionLL;
                        k += sizeof(subtractionLL) - 1;
                    } else {
                        subtraction = (*(self->reader.x + k) & ~*(readerB.x + k));
                        if (!retVal) {
                            if (*(self->reader.x + k) != subtraction) {
                                retVal = true;
                                if (!writing) {
                                    writing = true;
                                    goto startpoint;
                                }
                            };
                        }
                        if (subtraction == 0) {
                            numberOfCharsA = k + 1;
                            break;
                        } else {
                            content = true;
                        }
                        *(self->reader.x + k) = subtraction;
                    }
                }
                if (k > 0) {
                    if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, k);
                }

                self->reader.x += numberOfCharsA;
                self->reader.charOffset += numberOfCharsA;
                self->reader.moveforward = false;

                readerB.x += numberOfCharsA;
                readerB.charOffset += numberOfCharsA;
                readerB.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
                BisFinished = !cbarReader_nextByte(&readerB);
            }

            if (AisFinished && !writing) {
                return false;
            }

            if (BisFinished  && !retVal) {
                if (writing) {
                    generalCbarManager_returnCbar(self->manager, &self->outCbar);
                }
                return false;
            }
        }

        if (content) {
            cbarWriter_close(self);
            self->outCbar = null;
        } else {
            if (self->i > self->max) {
                d("exceeds max limit");
                terminate(0);
            }
            generalCbarManager_returnCbar(self->manager, &self->outCbar);
            generalCbarManager_returnCbar(self->manager, self->ptCbar);
            self->cbar = null;
        }

        return retVal;
    }
}

boolean cbarWriter_addItem(cbarWriter * self, int itemIndex) {

    osLong charOffsetB = itemIndex / 8;
    cbarHeaderLastByteOffset lastByteOffset = 0;
    cbarHeaderCbarLength length = 0;
    cbarHeaderCbarMaxLength maxLength = 0;


    if (self->cbar == null) {
        return cbarWriter_addItemGeneral(self, itemIndex);
    } else {
        lastByteOffset = cbar_getLastByteOffset(self->cbar);
        if (lastByteOffset > charOffsetB) {
            return cbarWriter_addItemGeneral(self, itemIndex);
        }
        length = cbar_getSize(self->cbar);
        maxLength = cbar_getMaxSize(self->cbar);
        if (maxLength < length + 5) {
            cbar_ensureLength(self->ptCbar, max(EXTRA_SIZE_ALLOWED * length, length + 5), self->manager, length);
            self->cbar = *self->ptCbar;
        }
    }

    {
        unsigned char byteB =  ((osUnsignedLong) 1) <<  (itemIndex % 8);
        boolean retVal = false;
        unsigned char addition = 0;
        cbarHeaderLastSequenceLength lastSequenceLength = 0;

        self->outCbar = self->cbar;
        self->byteOffset = lastByteOffset;
        self->max = self->outCbar + maxLength;
        self->i = self->outCbar + length;
        self->shortSequenceStart = self->i;

        lastSequenceLength = cbar_getLastSequenceLength(self->cbar);
        if (lastSequenceLength > 0) {
          self->shortSequenceStart = self->i - lastSequenceLength - 2;
        }

        if (lastByteOffset == charOffsetB) {
            if (self->shortSequenceStart == self->i) {
                --self->shortSequenceStart;
            }
            --self->i;

            addition = (*(self->i) | byteB);
            if (*(self->i) != addition) { retVal = true; };  /* else return without push and close */
        } else {
            retVal = true;
            addition = byteB;
        }

        cbarWriter_pushByte(self, charOffsetB, addition);

        cbarWriter_close(self);
        self->outCbar = null;

        return retVal;
    }
}

boolean cbarWriter_addItemGeneral(cbarWriter * self, int itemIndex) {
    boolean writing = false;
    osLong charOffsetB = itemIndex / 8;
    unsigned char byteB =  ((osUnsignedLong) 1) <<  (itemIndex % 8);
    cbarHeaderLastSequenceLength numberOfChars = 0;
    boolean AisFinished;
    boolean BisFinished;
    boolean readA;
    boolean readB;
    boolean retVal = false;
    osUnsignedLong length = 0;
    unsigned char addition;

startpoint:
    if (self->cbar == null) {
        length = cbarHeaderSize + 4;
        writing = true;
    } else {
        length = cbar_getSize(self->cbar) + 4;
    }
    if (writing) {
        cbarWriter_internalIni(self, length);
    }

    cbarReader_set(&self->reader, self->cbar);

    AisFinished = !cbarReader_nextByte(&self->reader);
    BisFinished = false;

    while (!(AisFinished && BisFinished)) {
        readA = !AisFinished && (BisFinished || (self->reader.charOffset <= charOffsetB));
        readB = !BisFinished && (AisFinished || (charOffsetB <= self->reader.charOffset));

        if (readA && !readB) {
            if (!self->reader.moveforward) {
                d("no move forward");
                terminate(0);
            }

            numberOfChars = max(self->reader.lsf - self->reader.x, 1);
            if (!BisFinished) {
                numberOfChars = min(numberOfChars, charOffsetB - self->reader.charOffset);
            }

            if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, numberOfChars);
            self->reader.x += numberOfChars;
            self->reader.charOffset += numberOfChars;
            self->reader.moveforward = false;

            AisFinished = !cbarReader_nextByte(&self->reader);
        } else if (readB && !readA) {
            retVal = true;
            if (!writing) {
                writing = true;
                goto startpoint;
            }

            if (writing) cbarWriter_pushByte(self, charOffsetB, byteB);

            BisFinished = true;
        } else if (readB && readA) {
            addition = (*(self->reader.x) | byteB);
            if (*(self->reader.x) != addition) {
                retVal = true;
            };

            if (canBeWrtittenAsIsolatedChar(addition) || cbarReated_inASequence(&self->reader)) {
                *(self->reader.x) = addition;
                if (writing) generalCbarManager_returnCbar(self->manager, &self->outCbar);
                return retVal;
            } else if (!writing) {
                writing = true;
                goto startpoint;
            } else {
                cbarWriter_pushByte(self, self->reader.charOffset, addition);
            }
            AisFinished = !cbarReader_nextByte(&self->reader);
            BisFinished = true;
        }

        if (BisFinished && !retVal) {
            if (writing) generalCbarManager_returnCbar(self->manager, &self->outCbar);
            return false;
        }
    }
    if (writing) {
        cbarWriter_close(self);
    }
    self->outCbar = null;

    return retVal;
}

boolean cbarWriter_removeItem(cbarWriter * self, int itemIndex) {
    if (self->cbar == null) { return false; }

    {
        boolean writing = false;
        osLong charOffsetB = itemIndex / 8;
        unsigned char byteB =  ((osUnsignedLong) 1) <<  (itemIndex % 8);
        cbarHeaderLastSequenceLength numberOfChars = 0;
        boolean AisFinished;
        boolean BisFinished;
        boolean readA;
        boolean readB;
        boolean retVal = false;
        boolean content = false;
        unsigned char subtraction;
        osUnsignedLong length = 0;
startpoint:

        if (writing) {
            length = cbar_getSize(self->cbar) + 4;
            cbarWriter_internalIni(self, length);
        }

        cbarReader_set(&self->reader, self->cbar);

        AisFinished = !cbarReader_nextByte(&self->reader);
        BisFinished = false;

        while (!AisFinished) {
            readA = !AisFinished && (BisFinished || (self->reader.charOffset <= charOffsetB));
            readB = !BisFinished && (AisFinished || (charOffsetB <= self->reader.charOffset));

            if (readA && !readB) {
                numberOfChars = max(self->reader.lsf - self->reader.x, 1);
                if (!BisFinished) {
                    numberOfChars = min(numberOfChars, charOffsetB - self->reader.charOffset);
                }

                if (writing) cbarWriter_pushLiteralSequence(self, self->reader.charOffset, self->reader.x, numberOfChars);
                self->reader.x += numberOfChars;
                self->reader.charOffset += numberOfChars;
                self->reader.moveforward = false;

                AisFinished = !cbarReader_nextByte(&self->reader);
                content = true;
            } else if (readB && !readA) {
                BisFinished = true;
            } else if (readB && readA) {
                subtraction = (*(self->reader.x) & ~byteB);
                if (*(self->reader.x) != subtraction) {
                    retVal = true;
                }
                if (subtraction == 0) {
                    if (!writing) {
                        writing = true;
                        goto startpoint;
                    }
                } else {
                    if (canBeWrtittenAsIsolatedChar(subtraction) || cbarReated_inASequence(&self->reader)) {
                         *(self->reader.x) = subtraction;
                         if (writing) generalCbarManager_returnCbar(self->manager, &self->outCbar);
                         return retVal;
                    } else if (!writing) {
                         writing = true;
                         goto startpoint;
                    }
                    cbarWriter_pushByte(self, self->reader.charOffset, subtraction);
                    content = true;
                }
                AisFinished = !cbarReader_nextByte(&self->reader);
                BisFinished = true;
            }

            if (BisFinished && !retVal) {
                if (writing) generalCbarManager_returnCbar(self->manager, &self->outCbar);
                return false;
            }
        }

        if (content) {
            if (writing) {
                cbarWriter_close(self);
            }
            self->outCbar = null;
        } else {
            if (self->i > self->max) {
                d("exceeds max limit");
                terminate(0);
            }
            generalCbarManager_returnCbar(self->manager, &self->outCbar);
            generalCbarManager_returnCbar(self->manager, self->ptCbar);
            self->cbar = null;
        }

        return retVal;
    }
}

boolean cbar_containsItem(cbarHead * cbar, int itemIndex) {
    if (cbar == null) { return false; }

    {
        osLong charOffsetB = itemIndex / 8;
        unsigned char byteB =  ((osUnsignedLong) 1) <<  (itemIndex % 8);
        cbarReader readerA;

        boolean AisFinished;
        boolean readA;
        boolean readB;
        cbarHeaderLastSequenceLength numberOfChars = 0;

        cbarReader_set(&readerA, cbar);

        AisFinished = !cbarReader_nextByte(&readerA);
        while (!AisFinished) {
            readA = !AisFinished && (readerA.charOffset <= charOffsetB);
            readB = (AisFinished || (charOffsetB <= readerA.charOffset));

            if (readA && !readB) {
                numberOfChars = max(readerA.lsf - readerA.x, 1);
                numberOfChars = min(numberOfChars, charOffsetB - readerA.charOffset);

                /* nothing to push */
                readerA.x += numberOfChars;
                readerA.charOffset += numberOfChars;
                readerA.moveforward = false;

                AisFinished = !cbarReader_nextByte(&readerA);
            } else if (readB && !readA) {
                return false;
            } else if (readB && readA) {
                return (*(readerA.x) == (*(readerA.x) | byteB));
            }
        }

        return false;
    }
}

boolean cbar_inCbar(cbarHead * includedCbar, cbarHead * containerCbar) {
    if (includedCbar == null) { return true; }
    if (containerCbar == null) { return false; }

    {
        cbarReader readerA;
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        unsigned char addition;
        boolean readA;
        boolean readB;
        cbarHeaderLastSequenceLength numberOfChars = 0;

        cbarReader_set(&readerA, containerCbar);
        cbarReader_set(&readerB, includedCbar);

        AisFinished = !cbarReader_nextByte(&readerA);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!(AisFinished || BisFinished)) {
            readA = (readerA.charOffset <= readerB.charOffset);
            readB = (readerB.charOffset <= readerA.charOffset);

            if (readA && !readB) {
                numberOfChars = max(readerA.lsf - readerA.x, 1);
                if (!BisFinished) {
                    numberOfChars = min(numberOfChars, readerB.charOffset - readerA.charOffset);
                }

                /* nothing to push */
                readerA.x += numberOfChars;
                readerA.charOffset += numberOfChars;
                readerA.moveforward = false;

                AisFinished = !cbarReader_nextByte(&readerA);
            } else if (readB && !readA) {
                return false;
            } else if (readB && readA) {
                addition = (*(readerA.x) | *(readerB.x));
                if (addition != *(readerA.x)) {
                    return false;
                }
                AisFinished = !cbarReader_nextByte(&readerA);
                BisFinished = !cbarReader_nextByte(&readerB);
            }
        }
        if (AisFinished && !BisFinished) { return false; }
        return true;
    }
}

int cbar_compareCbars(cbarHead * cbarA, cbarHead * cbarB) {
    if ((cbarA == NULL) && (cbarB == NULL)) { return 0; }
    if (cbarA == NULL) { return 1; }
    if (cbarB == NULL) { return -1; }
    if (cbarA == cbarB) { return 0; }

    {
        cbarReader readerA;
        cbarReader readerB;
        boolean AisFinished;
        boolean BisFinished;
        int difference;
        boolean readA;
        boolean readB;

        cbarReader_set(&readerA, cbarA);
        cbarReader_set(&readerB, cbarB);

        AisFinished = !cbarReader_nextByte(&readerA);
        BisFinished = !cbarReader_nextByte(&readerB);

        while (!(AisFinished || BisFinished)) {
            readA = (readerA.charOffset <= readerB.charOffset);
            readB = (readerB.charOffset <= readerA.charOffset);

            if (readA && !readB) {
                return -1;
            } else if (readB && !readA) {
                return 1;
            } else if (readB && readA) {
                difference = (int)*(readerB.x) - (int)*(readerA.x);
                if (difference > 0) {
                    return 1;
                } else if (difference < 0) {
                    return -1;
                }
                AisFinished = !cbarReader_nextByte(&readerA);
                BisFinished = !cbarReader_nextByte(&readerB);
            }
        }
        if (AisFinished && !BisFinished) { return 1; }
        if (!AisFinished && BisFinished) { return -1; }
        return 0;
    }
}

int cbar_countItems(cbarHead * cbar) {
    int count = 0;
    if (cbar == null) { return 0; }
    {
        cbarReader reader;
        cbarReader_set(&reader, cbar);
        while (cbarReader_nextItem(&reader)) {
            ++count;
        }
    }
    if (count == 0) { d("count should not be null on non-null cbar"); terminate(0); }
    return count;
}

int cbar_countItems_upto2(cbarHead * cbar) {
    int count = 0;
    if (cbar == null) { return 0; }
    {
        cbarReader reader;
        cbarReader_set(&reader, cbar);
        while (cbarReader_nextItem(&reader) && count < 2) {
            ++count;
        }
    }
    if (count == 0) { d("count should not be null on non-null cbar"); terminate(0); }
    return count;
}

int cbar_chooseItemIn(cbarHead * cbar) {
    int count = 0;
    int total = 0;
    int pick;
    if (cbar == null) { return 0; }
    {
        cbarReader reader;
        total = cbar_countItems(cbar);
        pick = rand() % total;

        cbarReader_set(&reader, cbar);
        while (cbarReader_nextItem(&reader)) {
            if (count++ == pick) {
                return cbarReader_currentItem(&reader);
            }
        }
    }
    d("nothing picked");
    terminate(0);
    return 0;
}

/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/
/*--------------------------------- hashMap -----------------------------------*/
/*-----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------*/

void hashMap_finalize(hashMap * self) {
    if (self->nodeBitMap != 0) {
        int k;
        for (k = 0; k < hashMap_baseSize; ++k) {
            if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
                if (self->values[k] != noValue) {
                    hashMap_finalize(((hashMap *) self->values[k]));
                    unboundedAllocator_returnMemory(self->allocator, &self->values[k]);
                    self->values[k] = noValue;
                }
            }
        }
        self->nodeBitMap = 0;
    }
    if ((self->allocator != null) && (self->ownAllocator)) {
        unboundedAllocator_delete(&self->allocator);
    }
}

boolean hashMap_initialize(hashMap * self, unboundedAllocator * theAllocator, unsigned int seed, char * (*getKey)(pointer)) {
    boolean ok = false;
    self->seed = seed;
    self->itemsOnThis = 0;
    self->nodeBitMap = 0;
    if (theAllocator == null) {
        self->ownAllocator = true;
        self->allocator = unboundedAllocator_new(hashMap_baseSize, sizeof (hashMap), true /*?*/);
        if (self->allocator == null) {
            d("out of memory");
            terminate(0);
            goto done;
        }
    } else {
        self->ownAllocator = false;
        self->allocator = theAllocator;
    }
    self->getKey = getKey;
    self->readCounter = 0;
    {
        int k;
        for (k = 0; k < hashMap_baseSize; ++k) {
            self->values[k] = noValue;
        }
    }

    ok = true;
done:
    return ok;
}

void hashMap_delete(hashMap ** self) {
    hashMap_finalize(*self);
    free(*self);
    *self = null;
}

hashMap * hashMap_new(unboundedAllocator * theAllocator, unsigned int seed, char * (*getKey)(pointer)) {
    hashMap * self = null;
    self = (hashMap *) malloc(sizeof (hashMap));
    if (self != null) {
        if (!hashMap_initialize(self, theAllocator, seed, getKey)) {
            hashMap_finalize(self);
            d("init error.");
        }
    } else {
        d("malloc returned null.");
    }
    return self;
}

long long hashMap_memoryUsed(hashMap * self) {
    int k;
    long long memory = 0;
    for (k = 0; k < hashMap_baseSize; ++k) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
            memory += sizeof (hashMap) + hashMap_memoryUsed((hashMap *) self->values[k]);
        }
    }
    return memory;
}

void hashMap_startIteration(hashMap * self) {
    int k;
    for (k = 0; k < hashMap_baseSize; ++k) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
            hashMap_startIteration((hashMap *) self->values[k]);
        }
    }
    self->readCounter = 0;
}

pointer hashMap_next(hashMap * self) {
    int k;
    pointer retVal;
    for (k = self->readCounter; k < hashMap_baseSize; ++k) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
            retVal = hashMap_next((hashMap *) self->values[k]);
            if (retVal != noValue) {
                return retVal;
            }
            self->readCounter = k + 1;
        } else {
            retVal = self->values[k];
            self->readCounter = k + 1;
            if (retVal != noValue) {
                return retVal;
            }
        }
    }
    return noValue;
}

int hashMap_count(hashMap * self) {
    int k;
    int count = self->itemsOnThis;
    if (self->nodeBitMap != 0) {
        for (k = 0; k < hashMap_baseSize; ++k) {
            if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
                count += hashMap_count((hashMap *) self->values[k]);
            }
        }
    }
    return count;
}

int hashMap_countNodes(hashMap * self) {
    int k;
    int count = 1;
    if (self->nodeBitMap != 0) {
        for (k = 0; k < hashMap_baseSize; ++k) {
            if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
                count += hashMap_countNodes((hashMap *) self->values[k]);
            }
        }
    }
    return count;
}

int hashMap_countLeaves(hashMap * self) {
    int k;
    int count = (self->nodeBitMap == 0) ? 1 : 0;
    if (self->nodeBitMap != 0) {
        for (k = 0; k < hashMap_baseSize; ++k) {
            if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << k))) {
                count += hashMap_countLeaves((hashMap *) self->values[k]);
            }
        }
    }
    return count;
}

unsigned int hashMap_getHash(hashMap * self, char * key, unsigned int keyLength) {
    unsigned int hash = 0;
    unsigned int i;
    // http://en.wikipedia.org/wiki/Jenkins_hash_function
    for (i = 0; i < keyLength; ++i) {
        hash += key[i], hash += (hash << 10) + self->seed, hash ^= (hash >> 6);
    }
    hash += (hash << 3), hash ^= (hash >> 11), hash += (hash << 15);
    return hash % hashMap_baseSize;
}

boolean hashMap_remove(hashMap * self, char * key) { /* true if something is removed */
    unsigned int hash = hashMap_getHash(self, key, strlen(key));
    pointer value = self->values[hash];
    if (value != noValue) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << hash))) {
            return hashMap_remove((hashMap *) value, key);
        } else {
            char * (*getKey)(pointer) = self->getKey;
            if (strcmp(getKey(value), key) != 0) {
                return false;
            }
        }
        self->values[hash] = noValue;
        --self->itemsOnThis;
        return true;
    }
    return false;
}

pointer hashMap_get(hashMap * self, char * key) {
    unsigned int hash = hashMap_getHash(self, key, strlen(key));
    pointer value = self->values[hash];
    if (value != noValue) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << hash))) {
            return hashMap_get((hashMap *) value, key);
        } else {
            char * (*getKey)(pointer) = self->getKey;
            if (strcmp(getKey(value), key) != 0) {
                return noValue;
            }
        }
    }
    return value;
}

void hashMap_map(hashMap * self, char * key, pointer value) {
    unsigned int hash = hashMap_getHash(self, key, strlen(key));

    {
        char * (*getKey)(pointer) = self->getKey;
        if (strcmp(getKey(value), key) != 0) {
            d("value key pair invalid %s != %s \n", key, getKey(value));
            terminate(0);
        }
    }

    pointer currentValue = self->values[hash];
    if (currentValue == value) {
        return;
    }
    if (currentValue == noValue) {
        self->values[hash] = value;
        ++self->itemsOnThis;
    } else {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long) 1) << hash))) {
            hashMap_map((hashMap *) currentValue, key, value);
            return;
        } else {
            hashMap * newHashMap;
            char * (*getKey)(pointer) = self->getKey;
            char * currentKey = getKey(currentValue);
            if (strcmp(currentKey, key) == 0) {
                d("repeated key with different value pairs");
                terminate(0); /* 2019 */
                return;
            }

            newHashMap = (hashMap*) unboundedAllocator_getMemory(self->allocator);
            hashMap_initialize(newHashMap, self->allocator, (int) 1 + self->seed, self->getKey);

            hashMap_map((hashMap*) newHashMap, key, value);
            hashMap_map((hashMap*) newHashMap, currentKey, currentValue);

            self->nodeBitMap |= (((unsigned long) 1) << hash);
            self->values[hash] = (pointer) newHashMap;
            --self->itemsOnThis;
        }
    }
}

// ------------------
// Masked functions use cbars as keys.
// - Information about size is ignored (it can differ for cbars representing the same data)

char* segment_to_str(segmentHead* segment)
{
    return (char*)segment;
}

int memcmp_masked(void* s1, void* s2, size_t n)
{
    int r = memcmp(s1, s2, cbarHeaderCbarMaxLength_Offset);
    if (r != 0) return r;
    return memcmp(
        (char*)s1 + cbarHeaderLastByteOffset_Offset,  //
        (char*)s2 + cbarHeaderLastByteOffset_Offset,  //
        n - cbarHeaderLastByteOffset_Offset);
}

unsigned int hashMap_getHash_masked(hashMap* self, char* key, unsigned int keyLength)
{
    unsigned int hash = 0;
    unsigned int i;
    // http://en.wikipedia.org/wiki/Jenkins_hash_function
    for (i = 0; i < cbarHeaderCbarMaxLength_Offset; ++i) {
        hash += key[i], hash += (hash << 10) + self->seed, hash ^= (hash >> 6);
    }
    /* Skip cbarHeaderCbarMaxLength bytes. They can be different between equal cbars. */
    for (i = cbarHeaderLastByteOffset_Offset; i < keyLength; ++i) {
        hash += key[i], hash += (hash << 10) + self->seed, hash ^= (hash >> 6);
    }
    hash += (hash << 3), hash ^= (hash >> 11), hash += (hash << 15);
    return hash % hashMap_baseSize;
}

pointer hashMap_get_masked(hashMap* self, char* key)
{
    unsigned int hash = hashMap_getHash_masked(self, key, *(cbarHeaderCbarLength*)key);
    pointer value = self->values[hash];
    if (value != noValue) {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long)1) << hash))) {
            return hashMap_get_masked((hashMap*)value, key);
        } else {
            char* (*getKey)(pointer) = self->getKey;
            if (memcmp_masked(getKey(value), key, *(cbarHeaderCbarLength*)key) != 0) {
                return noValue;
            }
        }
    }
    return value;
}

void hashMap_map_masked(hashMap* self, char* key, pointer value)
{
    unsigned int hash = hashMap_getHash_masked(self, key, *(cbarHeaderCbarLength*)key);

    { /* ----------------------------------------------- */
        char* (*getKey)(pointer) = self->getKey;
        if (memcmp_masked(getKey(value), key, *(cbarHeaderCbarLength*)key) != 0) {
            d("value key pair invalid %s != %s \n", key, getKey(value));
            terminate(0);
        }
    }

    pointer currentValue = self->values[hash];
    if (currentValue == value) {
        return;
    }
    if (currentValue == noValue) {
        self->values[hash] = value;
        ++self->itemsOnThis;
    } else {
        if (self->nodeBitMap == (self->nodeBitMap | (((unsigned long)1) << hash))) {
            hashMap_map_masked((hashMap*)currentValue, key, value);
            return;
        } else {
            hashMap* newHashMap;
            char* (*getKey)(pointer) = self->getKey;
            char* currentKey = getKey(currentValue);
            if (memcmp_masked(currentKey, key, *(cbarHeaderCbarLength*)key) == 0) {
                d("repeated key with different value pairs");
                terminate(0); /* 2019 */
                return;
            }

            newHashMap = (hashMap*)unboundedAllocator_getMemory(self->allocator);
            hashMap_initialize(newHashMap, self->allocator, (int)1 + self->seed, self->getKey);
            hashMap_map_masked((hashMap*)newHashMap, key, value);
            hashMap_map_masked((hashMap*)newHashMap, currentKey, currentValue);

            self->nodeBitMap |= (((unsigned long)1) << hash);
            self->values[hash] = (pointer)newHashMap;
            --self->itemsOnThis;
        }
    }
}
