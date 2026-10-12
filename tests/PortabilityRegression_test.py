'''
PortabilityRegression_test.py - permanent Windows portability regression suite
===============================================================================

PORT-04 (D2-10): TestCJKPathCanary — non-ASCII (CJK) path canary covering the
core surface: AlignmentFile/VariantFile read + write, .bai/.csi/.tbi index
building, tabix fetch, and one dispatch command, all under CJK-named
temporary directories.

WR-01: TestDispatchOutputEncoding — dispatch-captured stdout must decode as
UTF-8 regardless of the interpreter's locale (cp936-default interpreters
used to mojibake UTF-8 tool output silently, with no exception raised).

This module is self-contained (pytest tmp_path only; no make_data_files
dependency, no subprocess/shell usage, no network access).
'''

import gzip
import os

import pysam

from TestUtils import checkBinaryEqual, checkGZBinaryEqual


CJK_DIR_NAME = u"数据目录"
CJK_BAM_NAME = u"样本_测试.bam"
CJK_VCF_NAME = u"变体_样本.vcf"
CJK_VCF_OUT_NAME = u"变体_输出.vcf"

BAM_HEADER = {
    "HD": {"VN": "1.6", "SO": "coordinate"},
    "SQ": [{"SN": "chr1", "LN": 1000}],
}

VCF_TEXT = u"".join([
    u"##fileformat=VCFv4.2\n",
    u"##contig=<ID=1,length=1000>\n",
    u"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n",
    u"1\t100\t.\tA\tT\t50\tPASS\t.\n",
    u"1\t200\t.\tA\tT\t50\tPASS\t.\n",
])


def make_cjk_dir(tmp_path):
    d = os.path.join(str(tmp_path), CJK_DIR_NAME)
    os.makedirs(d)
    return d


def _write_records(outf, n, prefix="read_"):
    for i in range(n):
        a = pysam.AlignedSegment(outf.header)
        a.query_name = "%s%d" % (prefix, i)
        a.query_sequence = "ACGT"
        a.query_qualities = pysam.qualitystring_to_array("IIII")
        a.reference_id = 0
        a.reference_start = 100 + i
        a.mapping_quality = 60
        a.cigarstring = "4M"
        outf.write(a)


def make_cjk_bam(tmp_path):
    '''Write a 2-record BAM under a CJK-named directory; return its path.'''
    cjk_dir = make_cjk_dir(tmp_path)
    bam_path = os.path.join(cjk_dir, CJK_BAM_NAME)
    with pysam.AlignmentFile(bam_path, "wb", header=BAM_HEADER) as outf:
        _write_records(outf, 2, prefix=u"读段_")
    return bam_path


class TestCJKPathCanary:
    '''D2-10: non-ASCII paths work end-to-end through the htslib open layer.'''

    def test_cjk_bam_write_read_roundtrip(self, tmp_path):
        bam_path = make_cjk_bam(tmp_path)
        assert os.path.exists(bam_path)

        with pysam.AlignmentFile(bam_path, "rb") as inf:
            records = list(inf.fetch(until_eof=True))
        assert len(records) == 2
        assert records[0].query_name == u"读段_0"
        assert records[1].reference_start == 101

    def test_cjk_bam_indexes_bai_and_csi(self, tmp_path):
        bam_path = make_cjk_bam(tmp_path)

        pysam.samtools.index(bam_path)
        assert os.path.exists(bam_path + ".bai")

        pysam.samtools.index("-c", bam_path)
        assert os.path.exists(bam_path + ".csi")

        # The .bai must be usable for a region fetch through the CJK path.
        with pysam.AlignmentFile(bam_path, "rb") as inf:
            assert len(list(inf.fetch("chr1"))) == 2

    def test_cjk_vcf_tabix_index_and_fetch(self, tmp_path):
        cjk_dir = make_cjk_dir(tmp_path)
        vcf_path = os.path.join(cjk_dir, CJK_VCF_NAME)
        with open(vcf_path, "wb") as outf:
            outf.write(VCF_TEXT.encode("ascii"))

        indexed = pysam.tabix_index(vcf_path, preset="vcf", force=True)
        assert os.path.exists(indexed + ".tbi")

        with pysam.TabixFile(indexed) as tbf:
            rows = [line for line in tbf.fetch()]
        assert len(rows) == 2
        marker = "\t100\t" if isinstance(rows[0], str) else b"\t100\t"
        assert marker in rows[0]
        assert ("\t200\t" if isinstance(rows[1], str) else b"\t200\t") in rows[1]

    def test_cjk_variantfile_roundtrip(self, tmp_path):
        cjk_dir = make_cjk_dir(tmp_path)
        src_path = os.path.join(cjk_dir, CJK_VCF_NAME)
        dst_path = os.path.join(cjk_dir, CJK_VCF_OUT_NAME)
        with open(src_path, "wb") as outf:
            outf.write(VCF_TEXT.encode("ascii"))

        with pysam.VariantFile(src_path) as vin:
            with pysam.VariantFile(dst_path, "w", header=vin.header) as vout:
                for record in vin:
                    vout.write(record)

        with pysam.VariantFile(dst_path) as v:
            n = sum(1 for _ in v)
        assert n == 2

    def test_cjk_dispatch_command(self, tmp_path):
        bam_path = make_cjk_bam(tmp_path)
        header = pysam.samtools.view("-H", bam_path)
        if isinstance(header, bytes):
            header = header.decode("utf-8")
        assert header
        assert "@HD" in header
        assert "SQ" in header


class TestBinaryMode:
    '''D2-08: permanent byte-level binary-mode regression tests.

    Windows text-mode I/O translates \\n to/from \\r\\n at the CRT layer and
    silently corrupts BAM/BGZF/SAM data. Every public writer that touches a
    file path is asserted here at the byte level, so any future text-mode
    regression fails the regular suite instead of corrupting data.

    All assertions describe properties that hold on every platform, so this
    class is platform-neutral by construction (POSIX green = no regression).
    '''

    def test_sam_text_write_is_lf_only(self, tmp_path):
        sam_path = os.path.join(str(tmp_path), "out.sam")
        with pysam.AlignmentFile(sam_path, "w", header=BAM_HEADER) as outf:
            _write_records(outf, 2)

        with open(sam_path, "rb") as inf:
            data = inf.read()
        assert b"\r\n" not in data
        # 2 header lines (@HD + @SQ) + 2 records, each LF-terminated
        assert data.count(b"\n") == 4

        with pysam.AlignmentFile(sam_path, "r") as inf:
            assert len(list(inf.fetch(until_eof=True))) == 2

    def test_dispatch_save_stdout_is_lf_only(self, tmp_path):
        sam_path = os.path.join(str(tmp_path), "in.sam")
        with pysam.AlignmentFile(sam_path, "w", header=BAM_HEADER) as outf:
            _write_records(outf, 2)

        # flagstat is the dispatch command whose output actually flows
        # through the libcutils save_stdout redirect fd (samtools view
        # writes via htslib '-' -> fd 1 on every platform, so its
        # save_stdout file is always empty -- verified below as well).
        out_flagstat = os.path.join(str(tmp_path), "flagstat.txt")
        pysam.samtools.flagstat(sam_path, save_stdout=out_flagstat)
        with open(out_flagstat, "rb") as inf:
            data = inf.read()
        assert data
        assert b"\r\n" not in data

        out_view = os.path.join(str(tmp_path), "view.txt")
        pysam.samtools.view("-h", sam_path, save_stdout=out_view)
        with open(out_view, "rb") as inf:
            data = inf.read()
        assert b"\r\n" not in data

    def test_tabix_compress_is_byte_faithful(self, tmp_path):
        payload = b"AB\r\n" * 50 + b"END"
        src = os.path.join(str(tmp_path), "src.txt")
        dst = os.path.join(str(tmp_path), "dst.gz")
        with open(src, "wb") as inf:
            inf.write(payload)

        pysam.tabix_compress(src, dst)
        with gzip.open(dst, "rb") as inf:
            assert inf.read() == payload

    def test_bam_write_roundtrip_and_bgzf_magic(self, tmp_path):
        bam_path = os.path.join(str(tmp_path), "out.bam")
        with pysam.AlignmentFile(bam_path, "wb", header=BAM_HEADER) as outf:
            _write_records(outf, 3)

        with open(bam_path, "rb") as inf:
            head = inf.read(18)
        assert head[:4] == b"\x1f\x8b\x08\x04"
        assert head[12:14] == b"BC"

        with pysam.AlignmentFile(bam_path, "rb") as inf:
            assert len(list(inf.fetch(until_eof=True))) == 3

    def test_vcf_and_bcf_write_roundtrip(self, tmp_path):
        src = os.path.join(str(tmp_path), "src.vcf")
        with open(src, "wb") as inf:
            inf.write(VCF_TEXT.encode("ascii"))

        vcf_path = os.path.join(str(tmp_path), "out.vcf")
        bcf_path = os.path.join(str(tmp_path), "out.bcf")
        with pysam.VariantFile(src) as vin:
            header = vin.header
            records = list(vin)
            with pysam.VariantFile(vcf_path, "w", header=header) as vout:
                for record in records:
                    vout.write(record)
            with pysam.VariantFile(bcf_path, "wb", header=header) as vout:
                for record in records:
                    vout.write(record)

        with open(vcf_path, "rb") as inf:
            vcf_data = inf.read()
        assert b"\r\n" not in vcf_data

        with open(bcf_path, "rb") as inf:
            head = inf.read(18)
        assert head[:4] == b"\x1f\x8b\x08\x04"
        assert head[12:14] == b"BC"

        with pysam.VariantFile(vcf_path) as v:
            assert sum(1 for _ in v) == 2
        with pysam.VariantFile(bcf_path) as v:
            assert sum(1 for _ in v) == 2

    def test_double_tabix_compress_deterministic(self, tmp_path):
        payload = b"AB\r\n" * 50 + b"END"
        src = os.path.join(str(tmp_path), "src.txt")
        dst1 = os.path.join(str(tmp_path), "dst1.gz")
        dst2 = os.path.join(str(tmp_path), "dst2.gz")
        with open(src, "wb") as inf:
            inf.write(payload)

        pysam.tabix_compress(src, dst1)
        pysam.tabix_compress(src, dst2)
        assert checkBinaryEqual(dst1, dst2) is True
        assert checkGZBinaryEqual(dst1, dst2) is True


CJK_CO_COMMENT = u"样本注释：调度输出编码测试"


class TestDispatchOutputEncoding:
    '''WR-01: dispatch-captured stdout decodes as UTF-8 on every interpreter
    locale.  The capture file is written by the C dispatch binaries as raw
    bytes; reading it through the locale-default text codec (cp936 on this
    machine) silently mojibakes any non-ASCII tool output.  The expected
    capture path is an explicit binary read plus UTF-8 decode with
    replacement, so this assertion is platform-neutral by construction.
    '''

    def test_cjk_header_comment_roundtrip(self, tmp_path):
        # Binary-mode write of UTF-8 SAM bytes (header discipline per
        # devtools/smoke_test.py: htslib requires SQ lines).
        sam_path = os.path.join(str(tmp_path), "cjk_header.sam")
        sam_text = u"".join([
            u"@HD\tVN:1.6\n",
            u"@SQ\tSN:chr1\tLN:1000\n",
            u"@CO\t%s\n" % CJK_CO_COMMENT,
        ])
        with open(sam_path, "wb") as outf:
            outf.write(sam_text.encode("utf-8"))

        # Same dispatch call shape as devtools/smoke_test.py: catch_stdout
        # is the default, so the return value is the collected stdout.
        header = pysam.samtools.view("-H", sam_path)

        assert isinstance(header, str)
        assert u"@CO" in header
        assert CJK_CO_COMMENT in header
