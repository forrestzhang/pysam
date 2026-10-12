"""Windows test-data generator for tests/pysam_data (D2-06, Phase 2).

Mirrors every rule of this directory's Makefile using pysam's own dispatch
APIs and the Python standard library, so the test data can be produced on
Windows without make or any external samtools/bcftools/bgzip/tabix binary
(D2-05).  The Makefile remains the authoritative specification on POSIX —
tests/TestUtils.py dispatches by platform and only the win32 branch loads
this module.

Committed inputs (ex1.sam.gz, ex1.fa, *.sam, ...) are read-only and never
regenerated.  Every raw open() uses binary mode; --no-PG is passed
unconditionally (the Makefile's NO_PG probe) so generated headers stay
deterministic.  No subprocess, no shell, no network.

Rule-by-rule mapping (Makefile line -> generator step):
  %.fa.fai: %.fa                      faidx dispatch
  ex1.bam (explicit -t rule)          view --no-PG -bo ex1.bam -t ex1.fa.fai ex1.sam.gz
  %.bam.bai: %.bam                    index dispatch
  ex2.sam.gz                          view --no-PG -h ex1.bam | stdlib gzip
  %.sam: %.sam.gz                     stdlib gunzip
  with_md.sam.gz / with_md.bam        calmd --no-PG --output-fmt BAM stdout capture
  uncompressed.bam                    view --no-PG -bu -o
  %.bam: %.sam (generic *.sam glob)  view --no-PG -bo
  %.cram: %.sam                       view --no-PG -C -o -T ex1.fa
  %.cram.crai: %.cram                 index dispatch
  example_unmapped_reads_no_sq.bam    empty tmp.list -t rule
  example_bai.bam                     copy + index + bai rename
  ex1_csi.bam                         copy + index -c
  explicit_index.bam / .cram          copy
  empty.bam                           grep ^@ header + AlignmentFile zero-record write
  ex1.pileup.gz                       mpileup -f ex1.fa ex1.bam | stdlib gzip
  ex2_truncated.bam                   truncate(len - 512)
  ex2_corrupt.bam                     gunzip + append corrupt record + tabix_compress
  %.fq.gz: %.fq                       stdlib gzip (NOT bgzip)
  %.fa.gz: %.fa                       tabix_compress (bgzip) + faidx (.fai/.gzi)
  all.stamp                           plain binary touch (idempotency marker)
"""

import glob
import gzip
import os
import shutil
import sys

import pysam


# The corrupt read appended to ex2_corrupt.bam (Makefile:
# printf '\37\0\0\0\1\0\0\0' - block_size 31 < sizeof(bam_core_t fields)).
_CORRUPT_RECORD = b'\x1f\x00\x00\x00\x01\x00\x00\x00'

# .sam stems handled by their own explicit rules; the generic %.bam: %.sam
# loop must not rebuild them differently (ex1.bam needs -t ex1.fa.fai; ex2
# and with_md are products of their own chains above; the no_sq rule needs
# an empty -t list).
_EXPLICIT_SAM_RULES = frozenset(("ex1", "ex2", "with_md",
                                  "example_unmapped_reads_no_sq"))


def _gunzip(src, dst):
    with gzip.open(src, "rb") as inf, open(dst, "wb") as out:
        shutil.copyfileobj(inf, out)


def _as_bytes(dispatch_output):
    """Dispatch stdout comes back as str (text output) or bytes (binary
    output whose text-mode read raised UnicodeDecodeError in the collector);
    normalise to bytes for the binary-mode writers below."""
    if isinstance(dispatch_output, str):
        return dispatch_output.encode("utf-8")
    return dispatch_output


def _gzip_file(src, dst):
    with open(src, "rb") as inf, gzip.open(dst, "wb") as out:
        shutil.copyfileobj(inf, out)


def generate(directory):
    """Create every all.stamp prerequisite of the Makefile under directory."""
    def p(name):
        return os.path.join(directory, name)

    # ex1.fa.fai - tab-separated reference list for the -t flag below.
    pysam.samtools.faidx(p("ex1.fa"), catch_stdout=False)

    # ex1.bam: ex1.sam.gz is a headerless SAM (no @SQ lines), so the
    # reference dictionary comes from -t ex1.fa.fai.
    pysam.samtools.view("--no-PG", "-bo", p("ex1.bam"), "-t", p("ex1.fa.fai"),
                        p("ex1.sam.gz"), catch_stdout=False)
    # ex1.bam.bai (Makefile builds it as a prerequisite of ex2.sam.gz).
    pysam.samtools.index(p("ex1.bam"), catch_stdout=False)

    # ex2.sam.gz: ex2.sam - as ex1.sam, but with header.
    sam_text = _as_bytes(pysam.samtools.view("--no-PG", "-h", p("ex1.bam"),
                                             raw=True, catch_stdout=True))
    with gzip.open(p("ex2.sam.gz"), "wb") as out:
        out.write(sam_text)

    # ex1.sam / ex2.sam (%.sam: %.sam.gz).
    _gunzip(p("ex1.sam.gz"), p("ex1.sam"))
    _gunzip(p("ex2.sam.gz"), p("ex2.sam"))

    # ex2.bam + ex2.bam.bai (generic %.bam: %.sam rule).
    pysam.samtools.view("--no-PG", "-bo", p("ex2.bam"), p("ex2.sam"),
                        catch_stdout=False)
    pysam.samtools.index(p("ex2.bam"), catch_stdout=False)

    # with_md.sam.gz (calmd BAM output) and with_md.bam.  On POSIX
    # with_md.bam reaches view -bo through the gunzipped with_md.sam
    # intermediate; both files carry the same calmd records, so the
    # captured BAM bytes serve both (consumers read them, they never
    # byte-compare the pair).
    with_md_bam = pysam.samtools.calmd("--no-PG", "--output-fmt", "BAM",
                                       p("ex2.bam"), p("ex1.fa"),
                                       raw=True, catch_stdout=True)
    with open(p("with_md.sam.gz"), "wb") as out:
        out.write(with_md_bam)
    with open(p("with_md.bam"), "wb") as out:
        out.write(with_md_bam)
    pysam.samtools.index(p("with_md.bam"), catch_stdout=False)

    # uncompressed.bam (%.bam rule variant with -bu).
    pysam.samtools.view("--no-PG", "-bu", "-o", p("uncompressed.bam"),
                        p("ex2.sam"), catch_stdout=False)

    # Generic %.bam: %.sam + %.bam.bai:%.bam over every *.sam present
    # (the Makefile's $(wildcard *.sam) evaluated at parse time plus the
    # generated ex1.sam/ex2.sam, which it reaches through explicit rules;
    # rg_with_tab.bam, example_dash_in_chr.bam and
    # example_reverse_complement.bam all fall out of this loop).
    for sam_file in sorted(glob.glob(p("*.sam"))):
        stem = os.path.splitext(os.path.basename(sam_file))[0]
        if stem in _EXPLICIT_SAM_RULES:
            continue
        pysam.samtools.view("--no-PG", "-bo", p(stem + ".bam"), sam_file,
                            catch_stdout=False)
        pysam.samtools.index(p(stem + ".bam"), catch_stdout=False)

    # CRAM fixtures ($(CRAM) = ex1.cram ex2.cram ex3.cram) + .crai indexes.
    # -T ex1.fa supplies both the reference and the @SQ dictionary for the
    # headerless ex1.sam (samtools view populates the header from -T).
    for name in ("ex1", "ex2", "ex3"):
        pysam.samtools.view("--no-PG", "-C", "-o", p(name + ".cram"),
                            "-T", p("ex1.fa"), p(name + ".sam"),
                            catch_stdout=False)
        pysam.samtools.index(p(name + ".cram"), catch_stdout=False)

    # example_unmapped_reads_no_sq.bam: headerless SAM indexed against an
    # empty -t list so the BAM carries no @SQ dictionary at all.
    tmp_list = p("tmp.list")
    with open(tmp_list, "wb"):
        pass
    try:
        pysam.samtools.view("--no-PG", "-bo",
                            p("example_unmapped_reads_no_sq.bam"),
                            "-t", tmp_list,
                            p("example_unmapped_reads_no_sq.sam"),
                            catch_stdout=False)
    finally:
        os.remove(tmp_list)

    # example_bai.bam: copy of ex1.bam whose .bai is renamed example_bai.bai.
    shutil.copyfile(p("ex1.bam"), p("example_bai.bam"))
    pysam.samtools.index(p("example_bai.bam"), catch_stdout=False)
    os.replace(p("example_bai.bam.bai"), p("example_bai.bai"))

    # ex1_csi.bam: copy of ex1.bam with a .csi index.
    shutil.copyfile(p("ex1.bam"), p("ex1_csi.bam"))
    pysam.samtools.index("-c", p("ex1_csi.bam"), catch_stdout=False)

    # explicit_index.bam / explicit_index.cram: tests index these themselves.
    shutil.copyfile(p("ex1.bam"), p("explicit_index.bam"))
    shutil.copyfile(p("ex1.cram"), p("explicit_index.cram"))

    # empty.bam: the @ header lines of ex2.sam written as a zero-record BAM
    # (Makefile: grep "^@" ex2.sam | samtools view --no-PG -bo empty.bam -).
    header_lines = []
    with open(p("ex2.sam"), "rb") as inf:
        for line in inf:
            if line.startswith(b"@"):
                header_lines.append(line)
    tmp_header = p("tmp.empty_header.sam")
    with open(tmp_header, "wb") as out:
        out.writelines(header_lines)
    try:
        with pysam.AlignmentFile(tmp_header, "r") as source:
            header = source.header
        with pysam.AlignmentFile(p("empty.bam"), "wb", header=header):
            pass
    finally:
        os.remove(tmp_header)
    pysam.samtools.index(p("empty.bam"), catch_stdout=False)

    # ex1.pileup.gz: mpileup text through stdlib gzip.
    pileup_text = _as_bytes(pysam.samtools.mpileup("-f", p("ex1.fa"),
                                                   p("ex1.bam"),
                                                   raw=True, catch_stdout=True))
    with gzip.open(p("ex1.pileup.gz"), "wb") as out:
        out.write(pileup_text)

    # ex2_truncated.bam: ex2.bam minus the last 512 bytes (dd rule).
    with open(p("ex2.bam"), "rb") as inf:
        bam_data = inf.read()
    with open(p("ex2_truncated.bam"), "wb") as out:
        out.write(bam_data[:-512])

    # ex2_corrupt.bam: decompressed ex2.bam plus a read whose block_size is
    # smaller than the fixed core fields, re-BGZFed via tabix_compress
    # (consumers read this file and expect the iterator to fail; BGZF block
    # boundaries may differ from bgzip(1), which nothing byte-compares).
    tmp_raw = p("tmp.ex2_corrupt.raw")
    with gzip.open(p("ex2.bam"), "rb") as inf, open(tmp_raw, "wb") as out:
        shutil.copyfileobj(inf, out)
        out.write(_CORRUPT_RECORD)
    try:
        pysam.tabix_compress(tmp_raw, p("ex2_corrupt.bam"))
    finally:
        os.remove(tmp_raw)

    # faidx_empty_seq.fq.gz: plain gzip (the %.fq.gz rule is NOT bgzip).
    _gzip_file(p("faidx_empty_seq.fq"), p("faidx_empty_seq.fq.gz"))

    # ex1.fa.gz: bgzip via tabix_compress, then faidx for .fai/.gzi.
    pysam.tabix_compress(p("ex1.fa"), p("ex1.fa.gz"))
    pysam.samtools.faidx(p("ex1.fa.gz"), catch_stdout=False)

    # all.stamp (idempotency marker for make_data_files).
    with open(p("all.stamp"), "wb"):
        pass

    if "--verbose" in sys.argv:
        print("pysam_data generated in {}".format(directory), file=sys.stderr)
