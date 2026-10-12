'''
PortabilityRegression_test.py - permanent Windows portability regression suite
===============================================================================

PORT-04 (D2-10): TestCJKPathCanary — non-ASCII (CJK) path canary covering the
core surface: AlignmentFile/VariantFile read + write, .bai/.csi/.tbi index
building, tabix fetch, and one dispatch command, all under CJK-named
temporary directories.

This module is self-contained (pytest tmp_path only; no make_data_files
dependency, no subprocess/shell usage, no network access).
'''

import os

import pysam


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


def make_cjk_bam(tmp_path):
    '''Write a 2-record BAM under a CJK-named directory; return its path.'''
    cjk_dir = make_cjk_dir(tmp_path)
    bam_path = os.path.join(cjk_dir, CJK_BAM_NAME)
    with pysam.AlignmentFile(bam_path, "wb", header=BAM_HEADER) as outf:
        for i in range(2):
            a = pysam.AlignedSegment(outf.header)
            a.query_name = u"读段_%d" % i
            a.query_sequence = "ACGT"
            a.query_qualities = pysam.qualitystring_to_array("IIII")
            a.reference_id = 0
            a.reference_start = 100 + i
            a.mapping_quality = 60
            a.cigarstring = "4M"
            outf.write(a)
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
