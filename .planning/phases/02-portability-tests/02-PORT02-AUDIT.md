# PORT-02 Binary-Mode Call-Site Audit (D2-08)

**One-time audit — closure evidence, not inventory.** Every raw file-open
call site in the Cython layer and the C shim layer is enumerated, its
binary-mode status recorded, and every site that was neither guarded nor
binary-safe has been FIXED (not just listed). Per D2-08 this checklist pairs
with the permanent byte-level regression suite in
`tests/PortabilityRegression_test.py` (`TestBinaryMode`), so any future
text-mode regression fails the regular suite instead of silently corrupting
BAM/BGZF data.

- **Audited at:** plan 02-02 Task 2, branch `win`, commit 51a6f00f (shims) + this task
- **Environment:** MSYS2 UCRT64, ACP 936 (the corruption-prone configuration)
- **Scope:** `pysam/*.pyx`, `pysam/*.pxd`, `pysam/htslib_util.c`,
  `pysam/dynamic_libs.c`, `pysam/conftest_cstd.c`, plus the vendored htslib
  open layer as an already-safe pointer.

## Grep commands used (run from repo root)

```bash
# 1. libcport-mapped raw fd opens (the only raw fd opens in the Cython layer)
grep -rn "psam_open2\|psam_open3" pysam --include=*.pyx --include=*.pxd | grep -v libcport.pxd

# 2. Python-level open() calls in Cython source
grep -rn "open(" pysam --include=*.pyx

# 3. stdio FILE* opens in the C shim/util layer
grep -n "fopen\|_wfopen" pysam/htslib_util.c pysam/dynamic_libs.c pysam/conftest_cstd.c

# 4. fdopen/freopen variants (completeness)
grep -rn "fdopen\|freopen" pysam --include=*.pyx --include=*.pxd

# 5. dispatch-layer temp files
grep -n "mkstemp" pysam/libcutils.pyx
```

## Cython layer call sites

| File:Line | Call | Binary-mode status | How verified |
|---|---|---|---|
| `pysam/libcutils.pyx:359` | `c_open3(stdout_f_bytes, O_WRONLY\|O_CREAT\|O_TRUNC, 0o666)` (dispatch `save_stdout` redirect) | **Safe — closed 02-01, widened 02-02.** `psam_open3` → `psam_wopen` → `_wopen(..., flags \| _O_BINARY, mode & (_S_IREAD\|_S_IWRITE))` (`pysam/libcport.pxd:56-76`) | grep row 1; permanent test `test_dispatch_save_stdout_is_lf_only` (flagstat path, non-empty + CRLF-free) |
| `pysam/libcutils.pyx:390` | `c_open2(force_bytes(os.devnull), O_WRONLY)` | **Safe.** Same `psam_open2` mapping (`_O_BINARY` forced inside libcport) | grep row 1; same libcport source |
| `pysam/libcutils.pyx:397` | `c_open2(force_bytes(os.devnull), O_WRONLY)` | **Safe.** Same as above | grep row 1 |
| `pysam/libctabix.pyx:835` | `c_open(fn, O_RDONLY)` (tabix_compress input fd) | **Safe — closed 02-01, widened 02-02.** `psam_open2` → `psam_wopen` (`_O_BINARY` forced) | grep row 1; permanent test `test_tabix_compress_is_byte_faithful` (payload with 50 CRLF pairs round-trips byte-identically) |
| `pysam/libcutils.pyx:453` | `open(fn, "r")` (dispatch stderr collection) | **Intentional text.** Reads a stderr *message string* for an exception message, not binary data; a binary fallback exists at `:456` on `UnicodeDecodeError` | source read (`pysam/libcutils.pyx:451-460`) |
| `pysam/libcutils.pyx:456` | `open(fn, "rb")` (fallback) | **Safe.** Explicit `"b"` | source read |
| `pysam/libcfaidx.pyx:578` | `open(out_filename, mode='w')` | **Docstring only.** Doctest example in `FastxFile.__iter__` documentation; not live library code (upstream docstring, left untouched) | source read (`pysam/libcfaidx.pyx:570-581`) |

No other `psam_open*` call sites exist (grep row 1 output is exhaustive).

## C shim/util layer

`grep -n "fopen\|_wfopen" pysam/htslib_util.c pysam/dynamic_libs.c pysam/conftest_cstd.c`
returns **zero matches** (rc=1) — no stdio FILE* file opens in the shim layer.
`fdopen`/`freopen`: zero in `.pyx`/`.pxd` (grep row 4); the only match is the
`bgzf_fdopen` *declaration* in `pysam/libchtslib.pxd:158` (htslib API surface,
not a call site in pysam code).

## Dispatch-layer temporary files

`pysam/libcutils.pyx:353,364` — `tempfile.mkstemp()` fds are
**binary-by-construction** on Windows: the `tempfile` module ORs `O_BINARY`
into `_bin_openflags` (research A5, 02-RESEARCH.md). Empirical confirmation:
the D2-08 permanent suite (`test_dispatch_save_stdout_is_lf_only`) exercises
dispatch temp plumbing CRLF-free, and 02-01's byte probes (flagstat 460 bytes
CRLF-free) ran through the same machinery.

## htslib layer (recorded already-safe, evidence pointer)

Every htslib file open funnels through `hfile_oflags()`
(`htslib/hfile.c:825`, `flags |= O_BINARY` under `#ifdef O_BINARY`), which
covers all `hopen`/`bgzf`/index read paths (verified 02-RESEARCH.md;
hfile.c:766-793 pre-02-02 numbering). 02-02 additionally made `hopen_fd`
UTF-8→UTF-16 wide on `_WIN32` (`htslib/hfile.c:674-699`, `_wopen` via
two-call `MultiByteToWideChar`, no fixed-size buffer) — binary mode is
preserved because `hfile_oflags` still supplies `O_BINARY`. Index
auto-discovery probes use `idx_stat_exists()` (`htslib/hts.c:4771-4793`),
which is read-only metadata (no mode concern).

## Closure status

| Site | Closed by |
|---|---|
| write-side raw fd (`libcutils.pyx:359`) | 02-01 `psam_open3` (binary-by-flag) + 02-02 wide-open; permanent test locks it |
| read-side raw fd (`libctabix.pyx:835`) | 02-01 `psam_open2` + 02-02 wide-open; permanent test locks it |
| htslib open layer | already safe (`hfile_oflags` O_BINARY); 02-02 added the non-ASCII path capability (PORT-04) |
| everything else | safe by construction (explicit `"b"`), intentional text, or nonexistent (grep) |

**Zero unguarded sites remain.**
