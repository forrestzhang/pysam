---
phase: 01-mingw-w64
reviewed: 2026-10-12T10:27:21Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - pysam/libcutils.pyx
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 01: Code Review Report (Incremental Re-review)

**Reviewed:** 2026-10-12T10:27:21Z
**Depth:** standard
**Files Reviewed:** 1 (`pysam/libcutils.pyx`, current state)
**Status:** issues_found

## Summary

Incremental re-review under the #4682 stale-verification refresh. Phase 1's
original 13-file scope was reviewed at `dcf0a94c`; since then exactly one of
those files changed — `pysam/libcutils.pyx`, at `dc40dd29` (Phase 2 libcport
rewiring: posix cimports → `pysam.libcport` mappings, `/dev/null` →
`os.devnull`, `c_open` split into `c_open2`/`c_open3`). This report replaces
the original 01-REVIEW.md; that report's findings were all triaged in
01-REVIEW-DISPOSITION.md, which persists independently.

**Hard-constraint verification (the delta):**

- **Zero POSIX regression — holds.** `libcport.pxd:85-99` maps every POSIX
  name as an identity macro (`psam_dup`→`dup`, `psam_open2`→`open(path,flags)`,
  `psam_open3`→`open(path,flags,mode)`); `os.devnull` is byte-identical to the
  old `/dev/null` literal on POSIX; `SEEK_SET/CUR/END` moved from
  `posix.unistd` to `libc.stdio` carry the same 0/1/2 values from the same
  compiler headers; call-site arities map correctly (the 3-arg `save_stdout`
  site uses `c_open3`, the 2-arg devnull sites use `c_open2`). Nothing else in
  the function bodies changed.
- **Prior CR-02 is RESOLVED by the current code.** The original 01-REVIEW's
  CR-02 ("`save_stdout` redirect uses C `open()` without `O_BINARY`") — still
  marked `open` in 01-REVIEW-DISPOSITION.md — is fixed: line 359 routes through
  `psam_open3` → `psam_wopen` → `_wopen(wpath, flags | _O_BINARY, ...)`
  (`libcport.pxd:64-65`). Verified against the generated
  `pysam/libcutils.c` (psam_wopen block embedded at lines 1448-1477, no
  `posix/fcntl.h` remains). This review therefore does not re-report CR-02;
  the ledger will flag its row accordingly.
- **Bonus fix from the same rewiring:** `_wopen` via `MultiByteToWideChar`
  (CP_UTF8) makes non-ASCII `save_stdout`/temp paths work on ANSI-code-page
  Windows (e.g. a tempdir under a non-ASCII username, or this cp936-locale
  machine) — narrow `_open` would previously have misread the UTF-8 bytes.
- **Text-mode constraint on remaining raw-fd paths:** the three C-level open
  sites are binary-forced via libcport; `tempfile.mkstemp()` fds are binary on
  Windows (audited in 02-PORT02-AUDIT.md:61); fd 1 was empirically confirmed
  binary-safe under `python.exe` when redirected (`sys.stdout.buffer.write`
  of `b'A\nB\rC'` round-trips byte-identically), so the `catch_stdout=None`
  (`c_dup(STDOUT_FILENO)`) and `catch_stdout=False` paths do not hit CRT
  newline translation in realistic use.

Findings below are in the **current file state**. Two are latent defects
inherited verbatim from upstream base `4c8486b1` (verified by `git show`);
they are not port regressions but are real defects in the file as it stands.
WR-01 extends and partially contradicts the Phase-2 PORT-02 audit's
disposition of this same code (cross-reference noted inline). Consistent with
02-REVIEW.md IN-01 (`psam_open2` mode-0 caveat): neither `c_open2` call site
here passes `O_CREAT`, so that info finding does not trigger from this file.

## Narrative Findings (AI reviewer)

### Warnings

### WR-01: `_collect` decodes captured stdout/stderr with the Windows ANSI code page — mojibake passes silently and binary can skip the `"rb"` fallback

**File:** `pysam/libcutils.pyx:450-461` (call sites `:463` stderr, `:467` stdout)
**Issue:** `_collect` first opens the capture file in text mode
(`open(fn, "r")`), falling back to `"rb"` only on `UnicodeDecodeError`. Two
Windows-only problems:

1. **Default decode is the ANSI code page** (`locale.getpreferredencoding()`
   — cp936 on this machine, cp1252 typically), while samtools/bcftools emit
   bytes in UTF-8 (or raw). On POSIX the same line decodes with the UTF-8
   locale and matches. Dense code pages like GBK decode most byte pairs
   *successfully but wrongly*, so non-ASCII stderr (e.g. a non-ASCII filename
   echoed in an error message) never raises and is returned as mojibake with
   no fallback. This affects every dispatch call's `out_stderr` plus
   `out_stdout` for every method without an explicit `-o` mapping (all
   `samtools` methods except view/mpileup/depad/calmd, and `bcftools`
   head/index/roh/stats).
2. **Narrow binary-corruption window:** binary stdout content that happens to
   fully decode under the code page skips the fallback and is returned as
   lossy text. NUL-containing formats (BAM headers) reliably trip the decode
   error, but DEFLATE/BGZF streams can be NUL-free, in which case Python-level
   universal-newline translation (`\r\n`/`\r` → `\n`, applied on both
   platforms) silently drops bytes from what the caller expects to be raw
   output.

Cross-reference: `02-PORT02-AUDIT.md:45` dispositioned `:453` as
"Intentional text — reads a stderr *message string*, not binary data". That
reasoning covers only the stderr call site (`:463`), not the stdout call site
(`:467`), and assumes the decode always fails loudly for non-text — which
dense ANSI code pages break. No 02-REVIEW.md finding covers this; recorded
here as the still-open item.

Note this is *not* the CRT text-mode antipattern (Python text mode translates
newlines identically on POSIX); it is an encoding-default deviation plus a
fallback that is exception-gated rather than content-gated.
**Fix:** Read binary always, then decide:

```python
def _collect(fn):
    with open(fn, "rb") as inf:
        out = inf.read()
    finally cleanup unchanged
    if this is the stderr/stdout message path:
        try:
            return out.decode("utf-8", ERROR_HANDLER)
        except UnicodeDecodeError:
            return out
```

or minimally pin the text attempt to UTF-8 (`open(fn, "r",
encoding="utf-8")`) so Windows behaves like the POSIX locales the upstream
code was written against.

### WR-02: `parse_region` crashes with `IndexError` on single-coordinate region strings (`"chr1:100"`)

**File:** `pysam/libcutils.pyx:285-286`
**Issue:**

```python
parts = coord.split("-")
rstart = int(parts[0]) - 1
if len(parts) >= 1:      # vacuously true — split() always yields >= 1 part
    rstop = int(parts[1])  # IndexError for "chr1:100"
```

`split("-")` guarantees at least one element, so `>= 1` is always true and
`parts[1]` is out of range for any one-coordinate region — a SAM-spec-legal
open-ended form. Every region-accepting API (`fetch(region=...)`, `count`,
`pileup`) crashes instead of defaulting `rstop` to `MAX_POS`. Inherited
verbatim from upstream base `4c8486b1` (line 278 there); **not a port
regression**, but a real crash in the current file.
**Fix:** `if len(parts) >= 2: rstop = int(parts[1])` — the `rstop = MAX_POS`
default at `:267` then supplies the open end.

### Info

### IN-01: `calmd` mapping appends an empty-string argv entry to the dispatch call

**File:** `pysam/libcutils.pyx:370, 389`
**Issue:** `"calmd": ""` exists only to trigger the `stdout_f_bytes` /
`pysam_stdout_fn` path, but the shared code then runs
`"".format(stdout_f).split(" ")` → `[""]` (verified), appending an empty
positional argument to the samtools `calmd` command line. Works today because
the bundled getopt treats `""` benignly; latent and non-obvious. Inherited
from upstream (identical at base `4c8486b1:382`).
**Fix:** Guard the extend: `if stdout_option: args.extend(stdout_option.format(stdout_f).split(" "))`.

### IN-02: dead imports/cimports

**File:** `pysam/libcutils.pyx:2, 4, 5, 8, 9, 14, 19, 20, 21`
**Issue:** `types`, `string`, `re`, `io`, `contextmanager`,
`PY_MAJOR_VERSION`, `PY_MINOR_VERSION`, `INT32_MAX`, `fprintf`, `stderr`,
`fflush`, `c_stdout` are all unused (grep-verified; the `stderr` at `:20` is
`libc.stdio`'s, never written to). All inherited from upstream's import
block.
**Fix:** Remove. Caveat: if this file is periodically re-synced with upstream
pysam, dropping them creates merge friction — acceptable to leave with a
comment, but then say so explicitly.

### IN-03: `c_open2(os.devnull)` return value not checked

**File:** `pysam/libcutils.pyx:390, 397`
**Issue:** If the null-device open fails, `stdout_h = -1` flows into
`samtools_set_stdout` / `bcftools_set_stdout` and every dispatch write fails
with a confusing downstream error instead of an early `OSError`. Exotic on
both platforms (`/dev/null`/`nul` are near-always openable). Inherited from
upstream.
**Fix:** Mirror the `:360-361` check: `if stdout_h == -1: raise OSError_from_errno("Could not open null device")`.

---

_Reviewed: 2026-10-12T10:27:21Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
