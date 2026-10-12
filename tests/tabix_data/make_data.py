"""Windows test-data generator for tests/tabix_data (D2-06, Phase 2).

Mirrors every rule of this directory's Makefile using pysam's own APIs,
so the fixtures can be produced on Windows without make or any external
bgzip/tabix binary (D2-05).  The Makefile remains the authoritative
specification on POSIX — tests/TestUtils.py dispatches by platform and
only the win32 branch loads this module.

Committed .gz inputs are read-only and never regenerated; the two .gz
files the Makefile derives (example.bed.gz, fivecolumns.bed.gz) come
from their committed plain-text sources via tabix_compress (the %.gz
rule uses bgzip).  Every tabix preset matches the Makefile's -p flag
(gff2/gff3/gtf all use the 'gff' preset).  No subprocess, no shell,
no network.
"""

import os

import pysam


# target (relative name) -> tabix preset; exactly the Makefile's
# DERIVED_FILES .tbi entries plus the two bgzip %.gz rules.
_BGZIP = (
    "example.bed.gz",
    "fivecolumns.bed.gz",
)

_INDEX = (
    ("empty.bed.gz", "bed"),
    ("example.bed.gz", "bed"),
    ("example.gff2.gz", "gff"),
    ("example.gff3.gz", "gff"),
    ("example.gtf.gz", "gff"),
    ("example.sam.gz", "sam"),
    ("example.vcf.gz", "vcf"),
    ("example_badcomments.bed.gz", "bed"),
    ("example_badcomments.gtf.gz", "gff"),
    ("example_badcomments.sam.gz", "sam"),
    ("example_badcomments.vcf.gz", "vcf"),
    ("example_comments.bed.gz", "bed"),
    ("example_comments.gtf.gz", "gff"),
    ("example_comments.sam.gz", "sam"),
    ("example_comments.vcf.gz", "vcf"),
    ("example_large.bed.gz", "bed"),
    ("fivecolumns.bed.gz", "bed"),
)


def generate(directory):
    """Create every all.stamp prerequisite of the Makefile under directory."""
    def p(name):
        return os.path.join(directory, name)

    # %.gz: % (bgzip -c $< > $@)
    for gz in _BGZIP:
        src = os.path.splitext(gz)[0]
        pysam.tabix_compress(p(src), p(gz), force=True)

    # tabix -f -p <preset> for every derived .tbi
    for gz, preset in _INDEX:
        pysam.tabix_index(p(gz), preset=preset, force=True)

    # all.stamp (idempotency marker for make_data_files)
    with open(p("all.stamp"), "wb"):
        pass
