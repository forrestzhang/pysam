---
phase: 02-portability-tests
reviewed: 2026-10-12T08:46:46Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - bcftools/bcftools.pysam.c
  - htslib/hfile.c
  - htslib/hts.c
  - pysam/libchtslib.pxd
  - pysam/libchtslib.pyx
  - pysam/libcport.pxd
  - pysam/libctabix.pyx
  - pysam/libcutils.pyx
  - samtools/samtools.pysam.c
  - tests/AlignmentFile_test.py
  - tests/PileupTestUtils.py
  - tests/PortabilityRegression_test.py
  - tests/StreamFiledescriptors_test.py
  - tests/TestUtils.py
  - tests/_compile_sizes.pyx
  - tests/_compile_sizes.pyxbld
  - tests/cbcf_data/make_data.py
  - tests/compile_test.py
  - tests/conftest.py
  - tests/pysam_data/make_data.py
  - tests/samtools_test.py
  - tests/tabix_data/make_data.py
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-12T08:46:46Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Reviewed the full diff since `7efe1dee` across the C shims (hfile.c, hts.c), the
new `pysam/libcport.pxd` platform-mapping layer, the dispatch Cython modules,
the two generated `.pysam.c` exit-interception files, and the Windows test
infrastructure (conftest platform split, data generators, in-process oracles).

The C-layer core is solid and respects the hard constraints:

- **POSIX byte-identity holds.** `hfile.c hopen_fd`'s `#else` keeps
  `int fd = open(filename, hfile_oflags(mode), 0666);` unchanged;
  `hts.c idx_stat_exists`'s `#else` is the original `stat(fn, &sbuf) == 0`
  expression relocated into a static function; the `.pysam.c` POSIX branches
  keep `setjmp/longjmp` verbatim; `libcport.pxd` POSIX names are identity
  aliases; `conftest.py`'s POSIX httpserver branch is upstream's fixture
  verbatim, and `os.pathsep` evaluates to `":"` on POSIX (verified against
  upstream `4c8486b1` and `htslib/hts.h:44-51` for the `;` claim).
- **No text-mode regression.** `hfile_oflags` already ORs `O_BINARY`
  (hfile.c:829-831) so the `_wopen` path is binary; `psam_wopen` forces
  `_O_BINARY` and masks `pmode` to `_S_IREAD|_S_IWRITE` (the documented-safe
  MSVC `_open` practice); the new `TestBinaryMode` suite pins this at the byte
  level on every platform.
- The `psam_wopen`/`idx_stat_exists` shims use the two-call
  `MultiByteToWideChar` pattern with correct `errno` handling (EINVAL/ENOMEM)
  and no buffer truncation in the conversion itself.

The findings are concentrated in **generation consistency and test validity**,
not in the shipped C code: the Windows longjmp fix will be silently reverted by
the next template regeneration; the win32 `check_statement` oracle and the
`_compile_sizes` "compile-is-the-assertion" mechanism are both tautology-shaped
or defeated by a blanket `except`; and the `_WIN32` dispatch fix cannot compile
under the planned Phase 3 MSVC toolchain.

## Warnings

### WR-01: Windows longjmp fix not propagated to the `import/pysam.c` template — regeneration silently reverts it

**File:** `import/pysam.c:59-83` (cross-file: `samtools/samtools.pysam.c:59-105`, `bcftools/bcftools.pysam.c:59-105`, `devtools/import.py:132-134`)
**Issue:** The tracked `samtools.pysam.c` / `bcftools.pysam.c` gained `_WIN32`
branches using `__builtin_setjmp`/`__builtin_longjmp` with a `void *jmpbuf[5]`
buffer (the STATUS_BAD_STACK crash fix), but the template those files are
generated from was not updated: `import/pysam.c` still contains only the plain
`static jmp_buf @pysam@_jmpbuf;` / `setjmp` / `longjmp` forms. `devtools/import.py`
regenerates both files purely by `@pysam@` substitution
(`outf.write(re.sub("@pysam@", basename, inf.read()))`), so the next upstream
import run silently produces `.pysam.c` files without the Windows fix — the
interpreter-crashing exit interception returns with no diff warning the author.
This is exactly the generation-consistency signal this review was asked to check.
**Fix:** Apply the identical `#ifdef _WIN32` blocks to `import/pysam.c` so the
template remains the single source of truth:
```c
#ifdef _WIN32
static void *@pysam@_jmpbuf[5];
#else
static jmp_buf @pysam@_jmpbuf;
#endif
```
(and the matching `#ifdef` in `@pysam@_dispatch`/`@pysam@_exit`).

### WR-02: win32 `check_statement` oracle is a tautology — both sides run the same dispatch

**File:** `tests/samtools_test.py:196-218`
**Issue:** On win32 the "samtools side" target files are produced by
`pysam_method(*samtools_parts, raw=True, catch_stdout=redirect)` — the exact
same `pysam.samtools.*` dispatch function, running the same bundled samtools C
code, as the "pysam side" at lines 230-233. The only differences between the
two runs are the output filename prefix (`samtools_*` vs `pysam_*`) and the
`catch_stdout` flag for `-o` commands. Every `checkBinaryEqual`/slurp
comparison in `TestSamtools`/`TestBcftools` on Windows therefore compares a
deterministic function's output against itself: a bundled-samtools regression
on Windows makes both sides identically wrong and the suite stays green. This
violates the phase's own rule that tests must not compare two sides drawn from
the same dispatch path with no independent expectation. (POSIX is unaffected —
the `else` branch keeps the external binary, and CI ubuntu/macOS do install
samtools/bcftools.)
**Fix:** Give the win32 branch an independent expectation, e.g. compare the
dispatch output against committed golden fixture files (per platform) for the
deterministic statements, or derive expected values via the object API
(`pysam.AlignmentFile`/`VariantFile`) instead of a second dispatch run. At
minimum, rename/mark the win32 path so the green result is not reported as an
oracle pass.

### WR-03: `_compile_sizes` static asserts are swallowed by the blanket `except Exception` — a violated invariant skips instead of failing

**File:** `tests/compile_test.py:76-97` (assertion consumer at 116-121)
**Issue:** The D2-09 design states "compilation IS the assertion — a violated
width invariant fails the pyximport build". But `import _compile_sizes` sits
inside the same `try: ... except Exception: NO_PYXIMPORT = True` block as the
`pyximport` availability probe. If `_Static_assert(sizeof(psam_off_t) == 8)`
(or the hts_pos_t check) fires, the build fails, the `except` converts it to
`NO_PYXIMPORT = True`, and `test_compile_sizes_static_asserts` — and also
`test_bam` and `test_gtf`, which are unrelated to sizes — silently skip with
reason "no pyximport". The mechanism can never fail a run; it can only skip.
It also means on any toolchain lacking `_Static_assert` (older MSVC C mode in
the Phase 3 plan) the entire compile-test coverage disappears silently.
**Fix:** Import `_compile_sizes` in its own try/except that records a distinct
failure flag and assert on it:
```python
try:
    import pyximport
    pyximport.install(...)
    import _compile_test
except Exception:
    NO_PYXIMPORT = True

COMPILE_SIZES_FAILED = None
if not NO_PYXIMPORT:
    try:
        import _compile_sizes
    except Exception as e:
        COMPILE_SIZES_FAILED = e

def test_compile_sizes_static_asserts():
    assert COMPILE_SIZES_FAILED is None, \
        "width invariant violated: %s" % COMPILE_SIZES_FAILED
    assert _compile_sizes.check() is True
```

### WR-04: PileupTestUtils oracle comments are false and two builders became token-identical

**File:** `tests/PileupTestUtils.py:33-39, 57-65, 105-124`
**Issue:** Two problems. (1) The comments claim "The external-binary oracle
for these builders now lives in the fork CI ubuntu job", but the rewrite is
platform-unconditional: on every job, ubuntu included, `build_*_with_samtoolspipe`
now calls `pysam.samtools.mpileup` — nothing in the repo invokes an external
samtools for these builders anymore (the ubuntu CI job runs this same code).
What survives is dispatch-mpileup vs the Cython `inf.pileup()` engine, which is
a real cross-implementation comparison, but the "external oracle still exists
somewhere" claim is inaccurate and will mislead future maintainers.
(2) `build_query_bases_with_samtoolspipe` (lines 57-61) and
`build_query_bases_with_samtoolspysam` (lines 64-65) are now token-identical
functions under different names; any future assertion comparing them is
vacuous by construction, and the bench pair
`test_build_query_bases_from_bam_with_samtoolspipe` vs
`..._with_samtoolspysam` no longer measures two different things.
**Fix:** Correct the comments to state the actual oracle (in-process dispatch
vs pysam pileup engine, all platforms). For the POSIX side, where CI does
install samtools, consider gating the builders on platform to restore the
external-binary comparison where it is actually available; otherwise delete
one of the two identical `build_query_bases_*` builders.

### WR-05: `_WIN32` branch uses GCC-only builtins — will not compile under the planned Phase 3 MSVC toolchain

**File:** `samtools/samtools.pysam.c:84-104`, `bcftools/bcftools.pysam.c:84-103`
**Issue:** The new `#ifdef _WIN32` branches call `__builtin_setjmp` /
`__builtin_longjmp`, which exist only under GCC (and clang in GNU mode).
The project's stated hard decision is that wheels ship MSVC-built (CLAUDE.md
关键决策 1; Phase 3 = MSVC build system), and neither MSVC nor clang-cl
defines/ supports `__builtin_*` — on those compilers `_WIN32` is defined and
the code takes the builtin branch and fails to compile. The fix works today
under MinGW/UCRT64 but is a known landmine for the phase the roadmap
explicitly sequences next.
**Fix:** Gate on the compiler, not just the OS, and add an MSVC-appropriate
path (or a `#error` that fails loudly with a pointer to the decision):
```c
#if defined(_WIN32) && defined(__GNUC__)
static void *samtools_jmpbuf[5];
#define PSAM_SETJMP(buf) __builtin_setjmp(buf)
#define PSAM_LONGJMP(buf) __builtin_longjmp(buf, 1)
#elif defined(_WIN32)
#error "MSVC dispatch exit interception not yet ported (Phase 3, D2 decision)"
#else
static jmp_buf samtools_jmpbuf;
...
#endif
```

## Info

### IN-01: `psam_open2` + `O_CREAT` would create a mode-0 file on Windows

**File:** `pysam/libcport.pxd:75-76`
**Issue:** `psam_open2(path, flags)` maps to `psam_wopen(path, flags, 0)`, so
`mode & (_S_IREAD|_S_IWRITE)` is 0. A future caller passing `O_CREAT` through
the 2-arg form creates an unreadable/unwritable file on Windows (the POSIX
2-arg `open` with `O_CREAT` is similarly indeterminate). No current call site
does this (`c_open2` is used only for `os.devnull` / `O_RDONLY`).
**Fix:** Document the constraint next to the macro, or make `psam_open2` mask
out `_O_CREAT` defensively.

### IN-02: "long paths are never truncated" comments overclaim for `_wopen`/`_wstat`

**File:** `htslib/hfile.c:684-685`, `htslib/hts.c:4769-4770`
**Issue:** The dynamically sized `MultiByteToWideChar` buffer avoids
conversion truncation, but `_wopen`/`_wstat` remain subject to the normal
MAX_PATH ceiling unless the process opts into long paths or the path carries a
`\\?\` prefix. Paths longer than the OS limit still fail despite the comment.
**Fix:** Reword to "the conversion buffer is dynamically sized, so the name is
never truncated in conversion" and note the OS path-length caveat.

### IN-03: `_build_httpd` duplicates `_httpd`'s classes verbatim

**File:** `tests/conftest.py:12-57`
**Issue:** The win32 server constructor duplicates `QuietHTTPServer` /
`QuietRequestHandler` from `_httpd` line for line. The duplication is a
deliberate trade to keep the POSIX child-process path token-identical to
upstream, but it is 25 lines of copy-paste that must now be edited in pairs.
**Fix:** Acceptable as-is given the zero-regression constraint; if ever
relaxed, have `_httpd` construct via `_build_httpd` (the child-process target
only needs the returned server object).

### IN-04: `TestLogging.check` closes the handler only on the success path

**File:** `tests/AlignmentFile_test.py:1754-1775`
**Issue:** The `FileHandler` close added for win32 unlink hygiene runs after
`bam.pileup()` without `try/finally`. If `pileup()` raises, the handler stays
open, and `teardown_method`'s `os.unlink('log.txt')` then fails on win32 with
WinError 32, masking the original error.
**Fix:** Wrap the pileup block in `try:/finally:` and do the
`removeHandler`/`close` in the `finally`.

### IN-05: StreamFiledescriptors echo child re-emits CRLF on Windows

**File:** `tests/StreamFiledescriptors_test.py:52-60`
**Issue:** The `sys.executable -c` consumer writes through `sys.stdout`
(`TextIOWrapper`, `newline=None`), which translates `\n` to `os.linesep`
(`\r\n`) on Windows — unlike the `head -n200` it replaces, the child is not a
byte-faithful echo on win32. Harmless today because the test only counts
records and htslib tolerates CRLF SAM, but the comment ("echoes exactly 200
lines") should not be read as byte-faithfulness.
**Fix:** Open a byte-exact echo if that ever matters:
`sys.stdout.buffer.write(line.encode())`, or adjust the comment.

### IN-06: tabix generator builds `example.gtf.gz.tbi`, which the Makefile does not list

**File:** `tests/tabix_data/make_data.py:29-47`
**Issue:** The docstring says the `_INDEX` tuple is "exactly the Makefile's
DERIVED_FILES .tbi entries", but it additionally indexes `example.gtf.gz`,
which `tests/tabix_data/Makefile` (lines 3-19) does not build (POSIX tests
create it lazily). Harmless superset, but the "exactly" claim is off by one
entry and the two lists will drift silently if the Makefile changes.
**Fix:** Either drop `example.gtf.gz` from `_INDEX` or fix the docstring to
say "DERIVED_FILES plus example.gtf.gz".

---

_Reviewed: 2026-10-12T08:46:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
