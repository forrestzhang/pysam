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
    /* Negative-array-size typedefs, the pre-C11 portable static assert:
       _Static_assert is a C11 keyword that MSVC only accepts under an
       explicit /std switch (setup.py passes /std:c11; pyximport builds
       with stock distutils flags), so the keyword form would fail the
       pyximport compile on MSVC for a purely syntactic reason.  The
       typedef form asserts the identical invariant on every toolchain
       and puts the reason in the failing symbol name. */
    typedef char psam_static_assert_hts_pos_t_must_be_64_bit[
        (sizeof(hts_pos_t) == 8) ? 1 : -1];
    typedef char psam_static_assert_64_bit_scalar_expected_on_LLP64[
        (sizeof(long long) >= 8) ? 1 : -1];
    typedef char psam_static_assert_psam_off_t_must_match_64_bit_LFS[
        (sizeof(psam_off_t) == 8) ? 1 : -1];
    """


def check():
    return True
