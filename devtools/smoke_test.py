"""Acceptance smoke gate for pysam on Windows (D-04).

Standalone script (no pytest): imports pysam, generates a BAM from the
committed test data, verifies the produced bytes and the htslib read path,
and dispatches one samtools and one bcftools command. Exits nonzero on any
failure. Steps are individually named so a CI failure log points at the
broken capability (designed for reuse as the Phase 4 CI smoke gate).

Every direct open() call in this script uses an explicit binary mode:
text-mode I/O silently corrupts BAM/BGZF data on Windows (project
blocking anti-pattern).
"""

import os
import sys
import tempfile

import pysam
import pysam.bcftools  # not re-exported by pysam/__init__.py (upstream convention)


def _step(message):
    print("[smoke] %s" % message)


def main():
    # Resolve the repo root from the script location so the committed test
    # data is found regardless of the invocation cwd.
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datadir = os.path.join(repo, "tests", "pysam_data")
    # A SAM input with a real header: the bundled htslib rejects headerless
    # SAM at the first mapped record ("no SQ lines present"), and the old
    # choice ex1.sam.gz is headerless by design.
    sam_path = os.path.join(datadir, "test_mapped_unmapped.sam")
    vcf_path = os.path.join(datadir, "ex1.vcf.gz")

    with tempfile.TemporaryDirectory() as tmp:
        # Step 1: samtools dispatch -- generate a BAM from the committed
        # test data (exercises the _pysam_dispatch plumbing).
        # catch_stdout=False matters: with the default capture the
        # dispatcher appends its own "-o <tempfile>" AFTER the user's args
        # (pysam/libcutils.pyx), which silently shadows the "-o bam" pair
        # and the BAM bytes are returned instead of written to `bam`.
        # Disabling the capture lets samtools' own -o write the file.
        _step("1/4 samtools view -b: generate BAM from test_mapped_unmapped.sam")
        bam = os.path.join(tmp, "ex1.bam")
        pysam.samtools.view("-b", "-o", bam, sam_path, catch_stdout=False)

        # Step 2: byte-level verification of the produced file. A BAM file
        # is BGZF-compressed, so the on-disk magic is the gzip/BGZF header
        # (1f 8b 08 + FEXTRA flag with the "BC" subfield); the raw
        # b"BAM\x01" magic only exists in the decompressed payload, which
        # step 3 validates by opening the file with htslib itself.
        _step("2/4 verify BGZF magic bytes")
        with open(bam, "rb") as fh:
            head = fh.read(18)
        assert head[:4] == b"\x1f\x8b\x08\x04", \
            "not a gzip/BGZF file: %r" % (head[:4],)
        assert head[12:14] == b"BC", \
            "gzip file but not BGZF (no BC extra subfield): %r" % (head,)

        # Step 3: read the BAM back through the htslib bindings.
        _step("3/4 AlignmentFile fetch (until_eof=True)")
        with pysam.AlignmentFile(bam, "rb") as alignment:
            count = sum(1 for _ in alignment.fetch(until_eof=True))
        assert count > 0, "no alignments read from %s" % (bam,)
        print("[smoke]     %d alignments read" % count)

    # Step 4: bcftools dispatch on the committed VCF test data (exercises
    # the catch-stdout plumbing).
    _step("4/4 bcftools view -H: ex1.vcf.gz")
    output = pysam.bcftools.view("-H", vcf_path)
    assert output is not None, "bcftools view returned None"
    assert len(output) > 0, "bcftools view returned empty output"
    print("[smoke]     %d vcf lines" % len(output))

    print("smoke OK")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:
        sys.stderr.write("smoke FAILED: %r\n" % (exc,))
        rc = 1
    sys.exit(rc)
