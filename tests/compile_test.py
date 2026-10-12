'''
compile_test.py - check pyximport functionality with pysam
==========================================================

test script for checking if compilation against
pysam and tabix works.
'''

# clean up previous compilation
import os
import platform
import sys
import pytest
import pysam
from TestUtils import make_data_files, BAM_DATADIR, CBCF_DATADIR, TABIX_DATADIR

# PEP 660 editable installs import pysam through a MetaPathFinder, which
# Cython's file-based .pxd search cannot see. Append the repo root so the
# `from pysam.* cimport ...` lines in _compile_test.pyx/_compile_sizes.pyx
# resolve when pyximport compiles them. Appended (not inserted) so an
# explicitly configured PYTHONPATH build tree keeps module precedence.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setUpModule():
    make_data_files(BAM_DATADIR)
    make_data_files(CBCF_DATADIR)
    make_data_files(TABIX_DATADIR)


# D2-09 (PORT-03): per-platform expected object sizes for
# TestBinaryCompatibility. The table is consulted by the three test methods
# so the assertions stay active on LLP64 Windows instead of being skipped.
#
# No value diverges today: none of these Cython extension structs contains
# a C `long` (they are PyObject header + pointer + int/int64_t/bint
# compositions, and int64_t is fixed-width on every ABI we target), so the
# LP64 and LLP64 layouts agree. If a future field change introduces a
# `long`, add the divergent nt value with the LLP64 cause as a comment
# (long fields are 4-byte on nt vs 8-byte on posix).
EXPECTED_SIZES = {
    # LP64 (Linux/macOS x86_64/aarch64, long = 8): the literals previously
    # hardcoded in the three test methods, unchanged.
    "posix": {
        "alignment_file": 120,
        "alignment_header": 24,
        "aligned_segment": 72,
        "gz_iterator": 80,
        "tabix_file_iterator": 96,
        "variant_file": 120,
        "variant_header": 32,
    },
    # LLP64 (Windows x86_64, long = 4): measured on MSYS2 UCRT64 x86_64
    # (plan 02-02); identical to posix for the struct-composition reason
    # given above.
    "nt": {
        "alignment_file": 120,
        "alignment_header": 24,
        "aligned_segment": 72,
        "gz_iterator": 80,
        "tabix_file_iterator": 96,
        "variant_file": 120,
        "variant_header": 32,
    },
}


try:
    os.unlink('tests/_compile_test.c')
    os.unlink('tests/_compile_test.pyxbldc')
    os.unlink('tests/_compile_sizes.c')
    os.unlink('tests/_compile_sizes.pyxbldc')
except OSError:
    pass

NO_PYXIMPORT = False
try:
    import tempfile

    import pyximport
    # pyximport's default build dir (~/.pyxbld) is only absolute when
    # os.path.expanduser() can see a Windows profile env var; under an
    # MSYS2 login shell USERPROFILE/HOMEPATH may be absent, which makes
    # the default a *relative* "~" directory. A relative .pyd path cannot
    # be loaded by the Windows extension loader (LOAD_WITH_ALTERED_
    # SEARCH_PATH resolves relative names against the application dir,
    # not the cwd), so pin an absolute build dir unconditionally.
    pyximport.install(
        build_in_temp=False,
        build_dir=os.path.join(tempfile.gettempdir(), "pysam-pyxbld"))
    import _compile_test
    import _compile_sizes
except Exception:
    NO_PYXIMPORT = True


@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")
def test_bam():

    input_filename = os.path.join(BAM_DATADIR, "ex1.bam")
    nread = _compile_test.testCountBAM(
        pysam.Samfile(input_filename))
    assert nread == 3270


@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")
def test_gtf():

    input_filename = os.path.join(TABIX_DATADIR, "example.gtf.gz")

    nread = _compile_test.testCountGTF(
        pysam.Tabixfile(input_filename))
    assert nread == 237


@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")
def test_compile_sizes_static_asserts():
    # D2-09: compilation of _compile_sizes is itself the assertion -- a
    # violated width invariant fails the pyximport build with the
    # _Static_assert message. check() proves the module imported cleanly.
    assert _compile_sizes.check() is True


@pytest.mark.skipif(platform.machine() not in ('aarch64', 'arm64', 'AMD64', 'x86_64'), reason="different scalar sizes")
class TestBinaryCompatibility:
    def test_alignments(self):
        fp = pysam.AlignmentFile(os.path.join(BAM_DATADIR, "ex1.bam"))
        hdr = pysam.AlignmentHeader()
        aln = pysam.AlignedSegment()

        sizes = EXPECTED_SIZES[os.name]
        assert fp.__sizeof__() == sizes["alignment_file"]
        assert hdr.__sizeof__() == sizes["alignment_header"]
        assert aln.__sizeof__() == sizes["aligned_segment"]

    def test_tabix(self):
        gzit = pysam.GZIterator(os.path.join(TABIX_DATADIR, "example.gtf.gz"))

        with open(os.path.join(TABIX_DATADIR, "example.gtf.gz")) as fp:
            tfit = pysam.tabix_file_iterator(fp, pysam.asTuple())

        sizes = EXPECTED_SIZES[os.name]
        assert gzit.__sizeof__() == sizes["gz_iterator"]
        assert tfit.__sizeof__() == sizes["tabix_file_iterator"]

    def test_variants(self):
        fp = pysam.VariantFile(os.path.join(CBCF_DATADIR, "example_vcf43.vcf"))
        hdr = pysam.VariantHeader()

        sizes = EXPECTED_SIZES[os.name]
        assert fp.__sizeof__() == sizes["variant_file"]
        assert hdr.__sizeof__() == sizes["variant_header"]
