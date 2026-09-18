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


def _step(message):
    print("[smoke] %s" % message)


def main():
    # Resolve the repo root from the script location so the committed test
    # data is found regardless of the invocation cwd.
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datadir = os.path.join(repo, "tests", "pysam_data")
    sam_path = os.path.join(datadir, "ex1.sam.gz")
    vcf_path = os.path.join(datadir, "ex1.vcf.gz")

    with tempfile.TemporaryDirectory() as tmp:
        # Step 1: samtools dispatch -- generate a BAM from the committed
        # gzipped SAM test data (exercises the _pysam_dispatch plumbing).
        _step("1/4 samtools view -b: generate BAM from ex1.sam.gz")
        bam = os.path.join(tmp, "ex1.bam")
        pysam.samtools.view("-b", "-o", bam, sam_path)

        # Step 2: byte-level verification of the produced file.
        _step("2/4 verify BAM magic bytes")
        with open(bam, "rb") as fh:
            magic = fh.read(4)
        assert magic == b"BAM\x01", "not a BAM/BGZF file: %r" % (magic,)

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
