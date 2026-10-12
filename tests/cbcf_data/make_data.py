"""Windows test-data generator for tests/cbcf_data (D2-06, Phase 2).

Mirrors every rule of this directory's Makefile using pysam's own
dispatch APIs, so the fixtures can be produced on Windows without make
or any external bgzip/tabix/bcftools binary (D2-05).  The Makefile
remains the authoritative specification on POSIX — tests/TestUtils.py
dispatches by platform and only the win32 branch loads this module.

The Makefile's VCF list is every *.vcf except example_empty.vcf (its
.vcf.gz/.bcf are not prerequisites of all.stamp and no test consumes
them).  Per .vcf the chain is: bgzip (.vcf.gz), tabix -p vcf (.tbi),
bcftools index -f (.csi), bcftools view -O b (.bcf) and its index
(.bcf.csi).  Committed .vcf inputs are read-only.  No subprocess, no
shell, no network.
"""

import glob
import os

import pysam
import pysam.bcftools


def generate(directory):
    """Create every all.stamp prerequisite of the Makefile under directory."""
    def p(name):
        return os.path.join(directory, name)

    for vcf_file in sorted(glob.glob(p("*.vcf"))):
        stem = os.path.splitext(os.path.basename(vcf_file))[0]
        if stem == "example_empty":
            continue

        gz = p(stem + ".vcf.gz")
        pysam.tabix_compress(vcf_file, gz, force=True)           # bgzip
        pysam.tabix_index(gz, preset="vcf", force=True)          # .tbi
        pysam.bcftools.index("-f", gz, catch_stdout=False)       # .csi

        bcf = p(stem + ".bcf")
        pysam.bcftools.view("-O", "b", gz, "-o", bcf, catch_stdout=False)
        pysam.bcftools.index("-f", bcf, catch_stdout=False)      # .bcf.csi

    # all.stamp (idempotency marker for make_data_files)
    with open(p("all.stamp"), "wb"):
        pass
