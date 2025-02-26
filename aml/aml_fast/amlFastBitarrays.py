# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import ctypes
import functools
import numpy as np

from .amlCompiledLibrary import ffi
from .amlCompiledLibrary import lib as caml


class bitarray:
    __bitarray_out = 0
    gsm = None

    @classmethod
    def init(cls):
        if cls.gsm == None:
            cls.gsm = caml.createGenSegMgr()
        else:
            Exception("Redefining General Segment Manager for bitarrays not allowed")

    def __init__(self, values=None, gsm=None):
        if gsm == None:
            self.gsm = bitarray.gsm
        else:
            self.gsm = gsm

        self._segment_handle = ffi.new("void **")
        if values is not None:
            self.add(values)

        bitarray.__bitarray_out += 1

    # Destructor
    def __del__(self):
        caml.bitarray_delete(self._segment_handle, self.gsm)
        bitarray.__bitarray_out -= 1

    def __eq__(self, other):
        return bool(
            caml.bitarray_compare(self._segment_handle[0], other._segment_handle[0])
        )

    def __hash__(self):
        return hash(frozenset(self))

    def __repr__(self):
        return "bitarray(" + list(self.__unpack()).__repr__() + ")"

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return caml.bitarray_length(self._segment_handle[0])

    def len_upto2(self):
        return caml.bitarray_length_upto2(self._segment_handle[0])

    def __bool__(self):
        return bool(self._segment_handle[0] != ffi.NULL)

    def __iter__(self):
        return iter(self.__unpack())

    def __getstate__(self):
        handles = [self._segment_handle[0]]
        length_buffer = caml.segment_getAllSegmentsBufferLength(handles, 1)
        buffer = np.empty([length_buffer], dtype=np.byte)
        buffer_ptr = ffi.cast("char *", buffer.ctypes.data)
        caml.segment_getAllSegmentsBuffer(buffer_ptr, handles, 1)
        return buffer

    def __setstate__(self, state):
        self.gms = bitarray.gsm
        self._segment_handle = ffi.new("void **")
        handles = [self._segment_handle]
        buffer_ptr = ffi.cast("char *", state.ctypes.data)
        caml.segment_buildFromBuffer(buffer_ptr, handles, self.gsm)

    # Add an item
    def add(self, values):
        if isinstance(values, int):
            caml.bitarray_addItem(self._segment_handle, values, self.gsm)
        elif isinstance(values, (list, set, frozenset, tuple, bitarray)):
            caml.bitarray_addItems(
                self._segment_handle, list(values), len(values), self.gsm
            )
        elif isinstance(values, bitarray):
            caml.bitarray_clone(
                self._segment_handle, values._segment_handle[0], self.gsm
            )
        else:
            raise TypeError("Wrong value initialisation for bitarray")

    # Remove an item
    def remove(self, value):
        caml.bitarray_removeItem(self._segment_handle, value, self.gsm)

    # Union: a | b
    def __or__(self, other):
        new_bitarray = self.copy()
        caml.bitarray_add(
            new_bitarray._segment_handle, other._segment_handle[0], self.gsm
        )
        return new_bitarray

    # Intersection: a & b
    def __and__(self, other):
        new_bitarray = self.copy()
        caml.bitarray_intersect(
            new_bitarray._segment_handle, other._segment_handle[0], self.gsm
        )
        return new_bitarray

    # Subtraction: a - b
    def __sub__(self, other):
        new_bitarray = self.copy()
        caml.bitarray_subtract(
            new_bitarray._segment_handle, other._segment_handle[0], self.gsm
        )
        return new_bitarray

    # In-place union: a |= b (same as a += b)
    def __ior__(self, other):
        caml.bitarray_add(self._segment_handle, other._segment_handle[0], self.gsm)
        return self

    # In-place intersection: a &= b
    def __iand__(self, other):
        caml.bitarray_intersect(
            self._segment_handle, other._segment_handle[0], self.gsm
        )
        return self

    # In-place subtraction: a -= b
    def __isub__(self, other):
        caml.bitarray_subtract(self._segment_handle, other._segment_handle[0], self.gsm)
        return self

    # Return True if the item is in the bitarray: v in a
    def __contains__(self, item):
        return bool(caml.bitarray_contains(self._segment_handle[0], item))

    def issubset(self, other):
        return bool(
            caml.bitarray_issubset(self._segment_handle[0], other._segment_handle[0])
        )

    def isdisjoint(self, other):
        return bool(
            caml.bitarray_isdisjoint(self._segment_handle[0], other._segment_handle[0])
        )

    # Checks if semgemnt is in segment: a < b
    def __lt__(self, other):
        return self.issubset(other) and self != other

    # Checks if semgemnt is in segment: a <= b
    def __le__(self, other):
        return self.issubset(other)

    def copy(self):
        new_bitarray = bitarray(gsm=self.gsm)
        caml.bitarray_clone(
            new_bitarray._segment_handle, self._segment_handle[0], self.gsm
        )
        return new_bitarray

    # Return a set representation of the bitarray (Slow to compute)
    def __unpack(self):
        len_ba = len(self)
        ret = ffi.new("int []", [0] * len_ba)
        caml.bitarray_unpack(ret, self._segment_handle[0])
        return ret

    @classmethod
    def howManyAreOut(cls):
        import gc
        gc.collect()
        return caml.bitarray_howManyAreOut(cls.gsm)

    @classmethod
    def checkLeaks(cls):
        assert (
            caml.bitarray_howManyAreOut(cls.gsm) <= cls.__bitarray_out
        ), f"{caml.bitarray_howManyAreOut(cls.gsm)} not <= {cls.__bitarray_out}"
