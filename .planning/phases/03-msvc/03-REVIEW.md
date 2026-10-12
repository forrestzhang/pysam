---
phase: 03-msvc
reviewed: 2026-10-12T17:06:57Z
depth: standard
files_reviewed: 39
files_reviewed_list:
  - .gitignore
  - bcftools/abuf.c
  - bcftools/abuf.c.pysam.c
  - bcftools/bcftools.pysam.c
  - bcftools/hex.h
  - bcftools/variantkey.h
  - bcftools/vcfgtcheck.c
  - bcftools/vcfgtcheck.c.pysam.c
  - bcftools/version.c
  - bcftools/version.c.pysam.c
  - devtools/msvc-build.md
  - devtools/msvc_compile_probe.py
  - htslib/hts_internal.h
  - htslib/htslib/hts_defs.h
  - import/pysam.c
  - pysam/htslib_util.h
  - pysam/libcutils.pyx
  - samtools/bam_cat.c.pysam.c
  - samtools/bam_reheader.c.pysam.c
  - samtools/coverage.c
  - samtools/coverage.c.pysam.c
  - samtools/samtools.pysam.c
  - setup.py
  - tests/PortabilityRegression_test.py
  - tests/_compile_sizes.pyx
  - win32/bcftools_exports.def
  - win32/chtslib_exports.def
  - win32/config.h.msvc
  - win32/msvc/dirent.h
  - win32/msvc/msvc_compat.h
  - win32/msvc/pthread.h
  - win32/msvc/pthread_win32.c
  - win32/msvc/shim_selftest.c
  - win32/msvc/strings.h
  - win32/msvc/sys/time.h
  - win32/msvc/unistd.h
  - win32/samtools_exports.def
  - vendor/HASHES.txt
  - vendor/README.md
findings:
  critical: 0
  warning: 4
  info: 9
  total: 13
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-12T17:06:57Z
**Depth:** standard (with targeted deep cross-checks against htslib/samtools/bcftools/vendor consumers)
**Files Reviewed:** 39
**Status:** issues_found

## Summary

Phase 3 (BUILD-02, MSVC build system) reviewed at standard depth with cross-file
verification of the claims the implementation rests on. No Critical findings.
The load-bearing architecture checks **pass**:

- **D-20 lockstep verified byte-exact.** `defined(_WIN32) && !defined(_MSC_VER)`
  appears exactly once in each of `import/pysam.c`, `samtools/samtools.pysam.c`,
  `bcftools/bcftools.pysam.c`; regenerating both twins from the template with
  `sed 's/@pysam@/.../g'` produces byte-identical files. The `_MSC_VER` optind=0
  addition (vendored GNU getopt reinitialize idiom; verified against
  `win32/getopt.c:535` `if (optind == 0 || !__getopt_initialized)`) is present in
  all three. The C-fix twins (`abuf.c`, `version.c`, `vcfgtcheck.c`, `coverage.c`)
  carry identical `_MSC_VER`/`#else`-verbatim hunks in both copies.
- **Zero-regression red line holds.** `hts_defs.h`'s new dllimport consumer arm
  is `#elif defined(_MSC_VER)` — MinGW/POSIX preprocessor output is unchanged.
  `pysam/htslib_util.h`'s dllimport guard likewise falls through to the verbatim
  plain declaration. The mingw link arm keeps GNU flags verbatim; the D-17
  implib-path rederivation emits the identical `-Wl,--out-implib,pysam/...`
  string for the canonical UCRT64 inplace build (and fixes the previously
  divergent non-inplace emission/probe paths). The `msvc_*` module-graph
  variables are empty lists on every non-MSVC platform.
- **Shim macro-collision audit passes.** `msvc_compat.h` is wholly `#ifdef
  _MSC_VER`-gated; the five drop-in headers forward on `__GNUC__`. The risky
  `read/write/close` macros from the `unistd.h` drop-in cannot mangle
  `fp->backend->read(...)` member calls: `htslib/hfile.c` includes `<unistd.h>`
  at line 545, after every backend member-call site (194–525), and
  `multipart.c` (member call at :98) never includes `<unistd.h>`. Verified
  against current sources — but see WR-02 (this safety rests on include order,
  and the forwarder gate breaks clang-cl).
- **MSVC_LIBHTS_OBJS mirror verified.** 52 TUs (27 core + 11 cram + 14
  htscodecs); every path resolves case-exact against the htslib tree and
  `htslib/Makefile` (including `cram/mFILE.o`). Vendor globs match
  vendor/README.md claims (zlib 15, bzip2 7 library TUs — CLI `bzip2.c` pruned,
  regex 4, xz exclusions present on disk and filtered by `_xz_tool_tus`).
- **Export surfaces match consumers.** `samtools_exports.def`/`bcftools_exports.def`
  list exactly the six dispatch symbols `libcutils.pyx` cimports.
  `chtslib_exports.def`'s zlib set (`gzopen/gzdopen/gzread/gzclose/crc32/compress`)
  is a superset of what the tool twins actually call (grep: `gzclose`, `gzopen`,
  `crc32`, `gzdopen` only). `seq_nt16_str/table/int` and `hts_verbose` are
  HTSLIB_EXPORT-annotated in `hts.h`/`hts_log.h`, so the dllimport consumer arm
  covers them; `pysam_seq_comp_table` is .def-exported as DATA with the matching
  dllimport guard in `htslib_util.h` — the function-only symbols
  (`aux_type2size`, `pysam_bam_update`) correctly need no dllimport. No private
  symbol (getopt family) is exported.
- **Provenance manifests are internally consistent.** `vendor/HASHES.txt` hashes
  equal the README table; musl is explicitly flagged "NOT cross-checked — no
  upstream checksum published", not silently trusted.

The four Warnings are: an unchecked `malloc` in the coverage VLA-to-heap port,
a forwarder-gate inconsistency that breaks the documented clang-cl fallback, an
`X_OK` constant whose value contradicts both POSIX and its own comment, and a
POSIX behavior delta in `_collect` that the in-code comment overclaims as
"identical bytes either way".

## Critical Issues

None found.

## Warnings

### WR-01: VLA-to-heap port of `print_hist` never checks `malloc` failure

**File:** `samtools/coverage.c:236` (twin `samtools/coverage.c.pysam.c:238`)
**Issue:** The `_MSC_VER` arm replaces `double hist_data[hist_size]` with
`double *hist_data = malloc(hist_size * sizeof(double));` but the result is
never NULL-checked before the write loop at line 242 (`hist_data[i] = ...`).
On allocation failure this is a NULL-pointer write inside `samtools coverage`
dispatch. The POSIX VLA would also crash on failure, but a heap NULL deref is
trivially avoidable and this is a pysam-introduced code path (upstream has no
check because upstream has no malloc here). Note there are no early returns
between malloc (236) and free (310), so the leak side is correct; only the
NULL check is missing.
**Fix:**
```c
#if defined(_MSC_VER)
    double *hist_data = malloc(hist_size * sizeof(double));
    if (!hist_data) {
        print_error("coverage", "out of memory allocating histogram");
        return;
    }
#else
    double hist_data[hist_size];
#endif
```
(Apply identically to `samtools/coverage.c.pysam.c` to keep the twins in
lockstep.)

### WR-02: Drop-in headers' `__GNUC__` forwarder gate diverges from `msvc_compat.h`'s `_MSC_VER` gate — breaks the documented clang-cl fallback

**File:** `win32/msvc/pthread.h:34`, `win32/msvc/dirent.h:18`, `win32/msvc/strings.h:15`, `win32/msvc/sys/time.h:17`, `win32/msvc/unistd.h:20`
**Issue:** `msvc_compat.h:23` keys its entire body on `#ifdef _MSC_VER`, but the
five drop-in headers forward to the system headers on `#if defined(__GNUC__)`.
clang-cl — the fallback toolchain SC-3 evaluated and explicitly kept as a
future option (cl.exe-first decision, commits b3b479a7/f20d5813) — defines
**both** `_MSC_VER` and `__GNUC__`. Under clang-cl reaching the MSVC module
graph, every drop-in would take the forwarder arm and `#include_next
<pthread.h>` / `<dirent.h>` / `<unistd.h>` into headers that do not exist in
an MSVC/clang-cl environment — a hard compile failure with a confusing
diagnostic. The sentinel (`shim_selftest.c` under UCRT64 gcc) cannot catch this
because plain GCC defines only `__GNUC__`. The two gates should agree.
**Fix:** In all five drop-in headers change the forwarder to
```c
#if defined(__GNUC__) && !defined(_MSC_VER)
#include_next <pthread.h>   /* per-header name */
#else
```
This preserves the UCRT64 sentinel exactly (gcc defines no `_MSC_VER`) and
makes the headers take the MSVC arm under clang-cl, matching `msvc_compat.h`'s
discipline. Re-run the sentinel (`gcc -fsyntax-only -I win32/msvc
win32/msvc/shim_selftest.c`) to prove no UCRT64 change.

### WR-03: `X_OK` mapped to `6` — contradicts both POSIX and its own comment

**File:** `win32/msvc/msvc_compat.h:158-163`
**Issue:** The block defines `F_OK 0 / X_OK 6 / W_OK 2 / R_OK 4` and the comment
claims "Values are the POSIX iostream convention" and that `_access` treats
X_OK as "existence-and-not-write-protected". Neither is accurate: POSIX X_OK is
`1`, and MSVC `_access` mode `6` means *read AND write permitted*. A future
caller doing `access(dir, X_OK)` (the pattern the comment itself anticipates
for cram_io's ref-cache probe — though the current trees only use `R_OK`, at
`htslib/hts.c:4647` and `htslib/cram/cram_io.c:2275`) would get inverted
semantics: a read-only cache directory fails the probe under this shim but
succeeds under POSIX. Unused today, but it is a shipped compat constant with a
misleading justification.
**Fix:** Either map to the semantics the comment describes —
```c
#define X_OK 0   /* existence; no faithful Windows execute check (documented approximation) */
```
— or keep `6` but rewrite the comment to state plainly "X_OK degrades to
read+write under _access; no caller in the bundled trees uses X_OK".

### WR-04: `_collect` UTF-8 rework changes dispatch return type on non-UTF-8-locale POSIX interpreters; in-code comment overclaims "identical bytes either way"

**File:** `pysam/libcutils.pyx:450-475`
**Issue:** The strict-first UTF-8 decode with bytes fallback is a good fix for
the WR-01 mojibake class, and for UTF-8-locale interpreters (the norm since
PEP 538 locale coercion) behavior is unchanged. But on an interpreter running
an explicit non-UTF-8 locale (e.g. `LANG=en_US.ISO-8859-1`), the old code read
the capture file through the locale codec: latin-1 decodes *any* byte string,
so binary dispatch output (e.g. `samtools view` BAM capture) previously came
back as mojibake **str**; now it comes back as **bytes** (and invalid-UTF-8
text likewise flips str→bytes). That return-type change propagates to
`pysam/utils.py:71-103` (`splitlines()`/parser calls). It is a deliberate
improvement (the old str was destroyed data), but the comment at lines 460-461
("well-formed UTF-8 text ... decodes to str with identical bytes either way")
is only true for UTF-8-locale interpreters, and the project's stated red line
is "POSIX behavior must be unchanged". The delta should be acknowledged, not
papered over, and consumer behavior on the bytes path re-confirmed once.
**Fix:** Amend the comment to state the actual contract, e.g.:
"`identical' holds for UTF-8-locale interpreters (PEP 538 coercion makes this
the default); on explicit non-UTF-8 locales binary output now returns bytes
where the locale codec previously returned lossy str — intentional (that str
was destroyed data), consumers handle bytes (pre-WR-01 path)." If the
03-05 suite reconciliation did not exercise a non-UTF-8-locale cell, add one
(`LC_ALL=en_US.ISO-8859-1` + binary capture) to the fork CI matrix.

## Info

### IN-01: Stray double semicolons in the `_MSC_VER` arms of `abuf.c`

**File:** `bcftools/abuf.c:624,670` (twins `bcftools/abuf.c.pysam.c:626,672`)
**Issue:** `uint8_t *dst = buf->tmp2 + num_size*i*(star_allele+1);;` — the
MSVC-only arms carry a duplicated `;` (legal empty statement, cosmetic). Both
twins match, so lockstep is intact.
**Fix:** Drop the extra semicolon in all four sites (two files) in one commit.

### IN-02: `opendir`/`readdir` errno mapping is coarse

**File:** `win32/msvc/pthread_win32.c:350-353,364-366`
**Issue:** Every `FindFirstFileA` failure is reported as `ENOENT`, including
access-denied (`ERROR_ACCESS_DENIED` → should be `EACCES`) and invalid-name
cases; `readdir` returns NULL on `FindNextFileA` failure without setting errno.
No bundled MSVC consumer is live today (the dirent drop-in exists for
`vcfplugin.c`/`vcfannotate.c`, and plugins are disabled in
`win32/config.h.msvc`), so impact is latent.
**Fix:** `switch (GetLastError())` in the `INVALID_HANDLE_VALUE` path: map
`ERROR_ACCESS_DENIED`→`EACCES`, `ERROR_PATH_NOT_FOUND`/`ERROR_NO_MORE_FILES`
context as appropriate; set `errno` in `readdir` on non-`ERROR_NO_MORE_FILES`
failures.

### IN-03: `gettimeofday` `tv_sec` is 32-bit `long` — year-2038 truncation

**File:** `win32/msvc/pthread_win32.c:291`
**Issue:** `tv->tv_sec = (long)(since_1970 / 10000000ULL)` truncates past
2038 on LLP64 (`long` is 32-bit). This matches the winsock `struct timeval`
the shim shares its `_TIMEVAL_DEFINED` guard with, so it is consistent with
the substrate; every bundled caller computes relative deadlines. Documented
deviation territory, recorded here for completeness.
**Fix:** None required now; optionally note the 2038 bound in the header
comment of `sys/time.h`.

### IN-04: `pthread_cond_timedwait` with negative `tv_sec` waits ~49 days instead of timing out

**File:** `win32/msvc/pthread_win32.c:183-189`
**Issue:** `(ULONGLONG)abstime->tv_sec` of a negative value becomes huge; the
`0xFFFFFFFE` cap then degrades to a near-INFINITE wait, where POSIX returns
`ETIMEDOUT` immediately. All bundled callers pass `now + delta`, so this is
unreachable today, but the cap comment only documents the far-future case.
**Fix:** Before the cast: `if (abstime->tv_sec < 0) return ETIMEDOUT;` (with
the mutex re-acquire semantics SleepConditionVariableCS-failure already has —
returning without sleeping is correct here since the mutex was never released).

### IN-05: vendor/README.md's "proven" probe section still instructs copying `-D hidden=` lines the final design rejected

**File:** `vendor/README.md:204-212,216-218`
**Issue:** The historical 03-02 probe command lines include `-D hidden=` and
the section says "Plan 03-03's include wiring should copy these verbatim" —
but the 03-04 decision recorded later in the same file (lines 137-142) and in
setup.py deliberately does NOT define `hidden` (collision with htslib locals
like `textutils.c:246`; the qualifier was dropped from `tre.h` instead).
Following the "copy verbatim" instruction would reintroduce the collision.
**Fix:** Add a one-line note above the probe section: "Historical 03-02
commands; the `-D hidden=` flag was superseded by the tre.h compat edit (see
above) — the module graph in setup.py is authoritative."

### IN-06: Test docstring describes the superseded "replacement" decode; implementation is strict-first with bytes fallback

**File:** `tests/PortabilityRegression_test.py:265-267`
**Issue:** `TestDispatchOutputEncoding`'s class docstring says the expected
capture path is "an explicit binary read plus UTF-8 decode with replacement";
`libcutils._collect` was changed (03-05) to strict-first decode with a raw-bytes
fallback. The test itself is correct and passes either way; only the prose is
stale, which matters because this docstring is the regression's intent record.
**Fix:** Update to "binary read plus strict UTF-8 decode, falling back to raw
bytes for non-UTF-8 (binary) captures".

### IN-07: `config.h.msvc` SIMD keys are inert for the dedicated AVX2/AVX512 codec TUs under cl

**File:** `win32/config.h.msvc:19-22,39-46`
**Issue:** `HAVE_AVX2`/`HAVE_AVX512` are defined, but
`htslib/htscodecs/htscodecs/rANS_static32x16pr_avx2.c:36` gates its
implementation on `defined(__x86_64__) && defined(HAVE_AVX2)` — and cl does not
predefine `__x86_64__` (that is a GCC/Clang macro; MSVC defines `_M_X64`). So
those TUs compile their `#else` fallback arms; the pre-baked config advertises
SIMD capability the compiler gate silently disables. Correctness is preserved
(scalar fallbacks; the SC-2 suite passing CRAM round-trips is consistent with
this), but the file's curation claim ("x86 SIMD capability ... meaningful and
portable under cl") overstates what the keys achieve, and the TUs are dead
weight on the MSVC graph.
**Fix:** Either add a comment in `config.h.msvc` that the per-TU `__x86_64__`
gate keeps the avx2/avx512 TUs on their scalar `#else` under cl (keys retained
for the dispatch-side `#if defined(HAVE_AVX2)` sites in
`rANS_static4x16pr.c:983+`), or drop the two keys and confirm the dispatch
sites degrade cleanly.

### IN-08: `HTSLIB_MODE=separate` with an MSVC interpreter fails late and confusingly

**File:** `setup.py:897-901`
**Issue:** The MSVC short-circuit (`htslib_objects = []`) only guards
`HTSLIB_MODE == 'shared'`. With `HTSLIB_MODE=separate` on an MSVC python,
`htslib_objects` stays `['htslib/libhts.a']` (line 877) while
`prebuild_libchtslib` returns before ever building `libhts.a` on the MSVC arm
(line 1161-1166) — the failure surfaces as LNK1181 "cannot open input file
htslib/libhts.a" far from the misconfiguration.
**Fix:** Fail fast at the gate: `if IS_MSVC_PYTHON and HTSLIB_MODE not in
("shared",): sys.exit("pysam: MSVC builds support HTSLIB_MODE=shared only")`
(or explicitly support `separate` by compiling the mirror sources into each
extension — the current default `shared` is the only tested path).

### IN-09: msvc-build.md states "win-amd64 CPython 3.13+" as the prerequisite

**File:** `devtools/msvc-build.md:21`
**Issue:** The prerequisites section phrases the interpreter requirement as
"A win-amd64 CPython 3.13+". setup.py itself is kept 3.9-compatible (the
PEP 701 backslash-escape fix at `setup.py:298-306` exists precisely for the
3.9–3.11 CI cells), and Phase 4 (CI-02) will need MSVC wheels for the matrix
versions — the "3.13+" phrasing reads as a version floor it is not.
**Fix:** Reword to "A win-amd64 CPython (python.org or conda; this machine
uses Miniconda 3.13.5) — any version the wheel matrix targets".

---

_Reviewed: 2026-10-12T17:06:57Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
