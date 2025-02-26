// Algebraic AI - 2025
// Go to github.com/Algebraic-AI for full license details.

void* bitarray_new();

void bitarray_delete(void** segment, void* theGeneralSegmentManager);

int bitarray_howManyAreOut(void* theGeneralSegmentManager);

void bitarray_clone(
    void** new_segment, void* segment, void* theGeneralSegmentManager);

int bitarray_length(void* segment);

int bitarray_length_upto2(void* segment);

int bitarray_compare(void* segmentA, void* segmentB);

int bitarray_contains(void* segment, int item);

int bitarray_isdisjoint(void* segmentA, void* segmentB);

int bitarray_issubset(void* segment, void* container);

void bitarray_unpack(int ret[], void* segment);

void bitarray_addItem(void** segment, int item, void* theGeneralSegmentManager);

void bitarray_addItems(
    void** segment, int items[], int items_len, void* theGeneralSegmentManager);

void bitarray_removeItem(
    void** segment, int item, void* theGeneralSegmentManager);

void bitarray_add(
    void** segmentA, void* segmentB, void* theGeneralSegmentManager);

void bitarray_intersect(
    void** segmentA, void* segmentB, void* theGeneralSegmentManager);

void bitarray_subtract(
    void** segmentA, void* segmentB, void* theGeneralSegmentManager);
