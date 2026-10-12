# cython: language_level=3
"""C-level static asserts on critical type widths (D2-09, PORT-03).

Compilation IS the assertion: a violated width invariant fails the
pyximport build with the _Static_assert message. hts_pos_t and psam_off_t
are the offset ABI contract (htslib is compiled with _FILE_OFFSET_BITS 64;
pysam's libcport publishes the matching 64-bit alias), and any toolchain
where either shrinks below 8 bytes would silently truncate offsets above
2 GiB. check() exists only so a Python-level test can force the import
from tests/compile_test.py.
"""

from pysam.libcport cimport psam_off_t

cdef extern from *:
    """
    #include "htslib/hts.h"
    _Static_assert(sizeof(hts_pos_t) == 8, "hts_pos_t must be 64-bit");
    _Static_assert(sizeof(long long) >= 8, "64-bit scalar expected on LLP64");
    _Static_assert(sizeof(psam_off_t) == 8,
                   "psam_off_t must match htslib's 64-bit LFS off_t");
    """


def check():
    return True
