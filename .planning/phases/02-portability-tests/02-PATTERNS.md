# Phase 2: 可移植性加固与测试全绿 - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 16 (new + modified)
**Analogs found:** 14 / 16 (2 have no in-tree analog; use RESEARCH.md verified prototypes)

All analog paths below verified git-tracked (`git ls-files` non-empty). Line numbers refer to the current `win` branch working tree.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pysam/libcport.pxd` (NEW) | Cython declaration layer (platform mapping) | n/a (compile-time) | RESEARCH.md Pattern 1 verified prototype + `pysam/libchtslib.pxd` `cdef extern from` idiom | prototype (no in-tree analog) |
| `pysam/libcutils.pyx` (cimport rewiring + O_BINARY site :352) | Cython module (dispatch machinery) | file-I/O (fd redirect) | itself — current lines 22-23, 352, 383-390 are the sites to change | exact (self-referential edit) |
| `pysam/libctabix.pyx` (cimport rewiring + :832 read loop) | Cython module (tabix compress/index) | file-I/O (streaming copy) | itself — current lines 62-63, 802-854 | exact |
| `pysam/libchtslib.pyx` (cimport line 10) | Cython module (htslib core) | file-I/O | itself — current line 10 | exact |
| `pysam/libchtslib.pxd` (line 7 off_t → psam_off_t; :111-112 signatures) | Cython declaration | n/a | itself — current lines 7, 111-112 | exact |
| `htslib/hfile.c` (PORT-04 `_wopen` shim in `hopen_fd`) | C library code | file-I/O | `htslib/hfile.c` `hopen_fd_stdinout` (:761-770) + `hfile_oflags` (:772-797) — existing `_WIN32`/O_BINARY idiom in same file | exact (same file, same idiom) |
| `tests/conftest.py` (threading httpserver + `os.pathsep`) | test config/fixture | event-driven (server) | itself — current lines 1-55 | exact |
| `tests/TestUtils.py` (make_data_files win32 branch) | test utility | batch (data generation) | itself — `make_data_files` :164-185 | exact |
| `tests/pysam_data/make_data.py` (NEW) | test-data generator | transform (SAM→BAM/CRAM/BCF) | `tests/pysam_data/Makefile` (rule semantics) + `TestUtils.check_samtools_view_equal` in-process idiom (:95-128) | role-match |
| `tests/tabix_data/` generator (NEW) | test-data generator | transform | `tests/tabix_data/Makefile` + `pysam.tabix_compress`/`tabix_index` (`libctabix.pyx:802/857`) | role-match |
| `tests/cbcf_data/` generator (NEW) | test-data generator | transform | `tests/cbcf_data/Makefile` + `pysam.bcftools.view/index` | role-match |
| `tests/PileupTestUtils.py` (drop samtoolsshell/pipe builders) | test utility | transform | `build_*_with_pysam` functions in same file (:22-24, 43-50, 72-79, 92-98) | exact (in-tree target idiom already present) |
| `tests/samtools_test.py` (in-process rewrite of run_command/get_version/check_statement) | test | request-response (command compare) | `TestUtils.check_samtools_view_equal` :95-128 (in-process oracle) + `check_statement` current body :172-229 | role-match |
| `tests/StreamFiledescriptors_test.py` (head → sys.executable consumer) | test | streaming (fd pipe) | itself — current :45-61 (keep Popen + pipe shape; only the command string changes) | exact |
| `tests/compile_test.py` (LLP64 assertions + static asserts) + `tests/_compile_sizes.pyx` (NEW) | test + pyximport module | n/a | `tests/compile_test.py` `TestBinaryCompatibility` :57-82 + `tests/_compile_test.pyx` (pyximport consumer shape) | exact |
| Byte-level regression tests + CJK canary tests (NEW, in existing test files) | test | CRUD round-trip | `TestUtils.checkBinaryEqual` :54-79 / `checkGZBinaryEqual` :82-92; test class idiom per `.planning/codebase/TESTING.md` | role-match |

## Pattern Assignments

### `pysam/libcport.pxd` (NEW — centralized platform mapping layer)

**No in-tree analog** — but the file it must blend with stylistically is `pysam/libchtslib.pxd` (same directory, same declaration-only conventions). Use the RESEARCH.md Pattern 1 prototype, which was compiled and executed on the actual toolchain (Cython 3.3.0 / UCRT64 gcc 16.2.0):

```cython
cdef extern from *:
    """
    #ifdef _WIN32
    #include <fcntl.h>
    #include <io.h>
    #define psam_dup _dup
    ...
    #else
    #include <fcntl.h>
    #include <unistd.h>
    #define psam_dup dup
    ...
    #endif
    """
    int psam_dup(int fd)
    ...
```

Design constraints locked by research (do not deviate):
- Two fixed-arity exports `psam_open2(path, flags)` / `psam_open3(path, flags, mode)` — no variadic macros (MSVC `/Zc:preprocessor` safety for Phase 3).
- Windows mapping forces `| _O_BINARY` (`0x8000`; `_O_RDONLY` is `0x0000`) and masks pmode to `_S_IREAD|_S_IWRITE` (`mode & 0x180`).
- Publish `psam_off_t` (`typedef long long` on `_WIN32`, `off_t` else) per RESEARCH Pattern 2 — htslib is compiled with `_FILE_OFFSET_BITS 64` (`htslib/config.h:218`) so the 32-bit header default is an ABI gap.
- `SEEK_SET/CUR/END` come from `libc.stdio` (ISO-C, declared at `Cython/Includes/libc/stdio.pxd:44`), not posix.unistd.

### `pysam/libcutils.pyx` (cimport rewiring + binary-mode site)

**Analog:** the file's own current state. Exact lines to replace:

Current cimports (lines 22-23):
```cython
from posix.fcntl cimport open as c_open, O_WRONLY, O_CREAT, O_TRUNC
from posix.unistd cimport dup as c_dup, SEEK_SET, SEEK_CUR, SEEK_END, STDOUT_FILENO
```

PORT-02 live bug at line 352 (text-mode open of a redirect target):
```cython
        stdout_h = c_open(stdout_f_bytes, O_WRONLY|O_CREAT|O_TRUNC, 0o666)
        if stdout_h == -1:
            raise OSError_from_errno("Could not redirect standard output", stdout_f)
```
Fix by routing through `psam_open3` (O_BINARY forced inside libcport). Error-handling idiom to keep: the `== -1` → `OSError_from_errno("context", filename)` pattern visible at :353-354 and :383-390.

Already-correct Phase 1 pattern (lines 383, 390 — keep, D2-02 closes via verification only):
```cython
            stdout_h = c_open(force_bytes(os.devnull), O_WRONLY)
```
`os.devnull` is `"NUL"` on Windows — the platform-conditional constant D2-02 asked for, already arrived via stdlib.

### `pysam/libctabix.pyx` (cimport rewiring + read loop)

Current cimports (lines 62-63):
```cython
from posix.fcntl cimport open as c_open, O_RDONLY
from posix.unistd cimport close, dup, read
```

PORT-02 live bug #2 at line 832 (inside `tabix_compress`, :802-854) — the fd copy loop:
```cython
    fn = encode_filename(filename_in)
    fd_src = c_open(fn, O_RDONLY)
    if fd_src < 0:
        raise OSError_from_errno("Could not open input", filename_in)
```
Rewire to `psam_open2`; the `read`/`close` in the nogil loop (:839-852) become `psam_read`/`psam_close`. Note `encode_filename` (:824, :831) already produces UTF-8 bytes — do not touch it (PORT-04 fix belongs in htslib C).

### `pysam/libchtslib.pyx` + `pysam/libchtslib.pxd`

Minimal one-line edits. Current `libchtslib.pyx:10`:
```cython
from posix.unistd cimport dup
```
Current `libchtslib.pxd:7`:
```cython
from posix.types cimport off_t
```
and the consumers at :111-112:
```cython
    off_t hseek(hFILE *fp, off_t offset, int whence)
    off_t htell(hFILE *fp)
```
Recommendation from research (Open Question 4): have libcport export the aliased name `off_t` so the pxd body diff stays one line — `from pysam.libcport cimport off_t` (aliased to `psam_off_t` internally).

### `htslib/hfile.c` (PORT-04 `_wopen` shim)

**Analog: same file.** The patch site is `hopen_fd` (lines 664-683):
```c
static hFILE *hopen_fd(const char *filename, const char *mode)
{
    hFILE_fd *fp = NULL;
    int fd = open(filename, hfile_oflags(mode), 0666);
    if (fd < 0) goto error;
```
Copy the existing in-file `_WIN32` / capability-guard idiom:
- `hopen_fd_stdinout` (:761-770) — `#if defined HAVE_SETMODE && defined O_BINARY` conditional compilation style;
- `hopen_fd_fileuri` (:753-756) — `#if defined(_WIN32) || defined(__MSYS__)` block style;
- `hfile_oflags` (:792-794) — `#ifdef O_BINARY flags |= O_BINARY; #endif`.

The shim: on `_WIN32`, convert `filename` UTF-8 → UTF-16 via `MultiByteToWideChar(CP_UTF8, ...)` and call `_wopen`; free the scratch buffer on exit; keep the `goto error` cleanup structure (:679-682) intact. Zero changes on the POSIX side of every `#if`.

### `tests/conftest.py` (threading httpserver + REF_PATH)

Current fixture (lines 35-45) — the multiprocessing shape to replace:
```python
@pytest.fixture(scope="session")
def httpserver():
    rconn, wconn = multiprocessing.Pipe(duplex=False)
    process = multiprocessing.Process(target=_httpd, args=[wconn, Path(__file__).parent], name="httpd", daemon=True)
    process.start()

    host, port = rconn.recv()
    yield f"{host}:{port}"

    process.terminate()
    process.join()
```
Rewrite: keep `_httpd`'s `QuietHTTPServer`/`QuietRequestHandler` classes verbatim (:11-32, including the localhost-ephemeral-port bind and BrokenPipeError suppression — security-relevant), but instantiate the server in the fixture body inside a `threading.Thread(target=server.serve_forever, daemon=True)` and read `server.server_port` directly (no Pipe handshake). Teardown: `server.shutdown()`.

Line 53 today:
```python
    os.environ["REF_PATH"] = ":"
```
→ `os.environ["REF_PATH"] = os.pathsep` (matches `HTS_PATH_SEPARATOR_CHAR ';'` on `_WIN32`, `htslib/htslib/hts.h:44-51`).

### `tests/TestUtils.py` (make_data_files platform dispatch)

Current function (:164-185). Key structural facts to preserve: `all.stamp` idempotency check (:165-166), `all.lock` mkdir retry loop (:170-178), `finally: os.rmdir` (:184-185). The win32 branch must sit **before** `make` is invoked (the current `except CalledProcessError` does not catch Windows' `FileNotFoundError` for a missing `make` — reproduced):

```python
    if sys.platform == 'win32':
        from make_data import generate
        generate(directory)
    else:
        subprocess.check_output([make, '-C', directory], stderr=subprocess.STDOUT, encoding='ascii')
```
(The `import` stays inside the branch so POSIX never imports generator modules.)

**In-process oracle pattern to copy for D2-05 rewrites** — `check_samtools_view_equal` (:95-128):
```python
    lines1 = pysam.samtools.view(*(args + [filename1]))
    lines2 = pysam.samtools.view(*(args + [filename2]))
```
plus its fallback ladder (byte-equal → sorted-field line compare → False). `checkBinaryEqual` (:54-79) / `checkGZBinaryEqual` (:82-92) are the D2-08 assertion primitives — both already pure-Python and Windows-safe.

### `tests/pysam_data/make_data.py` + tabix_data/cbcf_data generators (NEW)

**Analog for semantics:** `tests/pysam_data/Makefile` — mirror each rule 1:1 (research's dispatch table maps every rule to a `pysam.samtools.*`/`pysam.bcftools.*`/`tabix_compress`/stdlib call). Notable rules and their Python shapes:
- `%.bam: %.sam` → `pysam.samtools.view("--no-PG", "-bo", out, inp)` (Makefile's `NO_PG` probe :6 becomes unconditional `--no-PG` for deterministic headers);
- `ex2_truncated.bam` (`dd bs=$((wc-c-512))`, :72-73) → `open(rb); data[:len-512]` write-out;
- `ex2_corrupt.bam` (bgzip/printf pipeline, :76-77) → decompress → append `b'\x1f\0\0\0\x01\0\0\0'` → `tabix_compress`;
- `empty.bam` (grep `^@` | view, :83-84) → filter header lines in Python, `AlignmentFile(header_from=...)` write.
Committed inputs (ex1.sam.gz, ex1.fa, *.sam, *.vcf...) are read-only; generators never regenerate them. `setUpModule(): make_data_files(DATADIR)` in each test module (idiom at `tests/compile_test.py:17-20`, `tests/samtools_test.py:18-19`) stays the sole entry point — no test-file churn.

### `tests/PileupTestUtils.py` (drop external samtools builders)

The in-tree target idiom already exists alongside the code being removed — keep/extend the `*_with_pysam` family and delete the `os.system`/`subprocess.Popen(["samtools", ...])` builders (:8-20, :27-41, :53-65, :109-116, :127-134, :145-153). Example of the pattern to keep (:22-24):
```python
def build_pileup_with_pysam(*args, **kwargs):
    with pysam.AlignmentFile(*args, **kwargs) as inf:
        return len(list(inf.pileup(stepper="samtools")))
```
and (:68-69):
```python
def build_query_bases_with_samtoolspysam(fn, *args):
    return [x.split()[4] for x in pysam.samtools.mpileup(fn, *args).splitlines()]
```
Consumers: `AlignmentFilePileup_test.py` (collected) + `*_bench.py` (out of scope, D2-11) — check bench imports don't break at import time even though uncollected.

### `tests/samtools_test.py` (in-process rewrite)

Rewrite targets: `run_command` (:22-30, `shell=True` subprocess), `get_version` (:33-44, Popen+shell probe), `check_version` (autouse-called at :144 — this poisons every TestSamtools test on Windows per research Anti-Patterns), `check_statement`'s "run samtools" half (:186-188). Pattern to move toward: both sides of each comparison become `pysam.samtools.*` dispatch calls with `catch_stdout=True, raw=True` (the pysam half already does this at :198-200):
```python
        output = pysam_method(*pysam_parts,
                              raw=True,
                              catch_stdout=True)
```
Keep: `check_version` replaced by a `pysam.__samtools_version__` self-check or gated on `shutil.which`; the tmp_path requisites-copy fixture body (:146-161); the three-tier comparison ladder at :220-229 (checkBinaryEqual → check_samtools_view_equal → slurp_file line compare).

### `tests/StreamFiledescriptors_test.py` (head pipe replacement)

Keep the structure of `test_text_processing` (:45-61) — a real subprocess with stdin/stdout pipes is the test's purpose (fd-based streaming). Only the command changes:
```python
        with subprocess.Popen('head -n200',
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              shell=True) as proc:
```
→ `subprocess.Popen([sys.executable, "-c", <read-200-lines script>"], ...)` (list form, no shell). The writer-thread + EPIPE-tolerant error handling (:16-33) and `assert read == 198` stay. `test_samtools_processing` keeps its existing `@pytest.mark.skip` (:63).

### `tests/compile_test.py` + `tests/_compile_sizes.pyx` (PORT-03)

`TestBinaryCompatibility` (:57-82) is the assertion idiom — plain `assert fp.__sizeof__() == 120` under a `@pytest.mark.skipif(platform.machine() not in (...), reason="different scalar sizes")` gate. Extend the skipif/make per-platform rather than deleting assertions. New static-assert module rides the **existing pyximport machinery** already installed at :29-35:
```python
    import pyximport
    pyximport.install(build_in_temp=False)
    import _compile_test
```
`_compile_sizes.pyx` copies the consumer shape of `tests/_compile_test.pyx` (cimport from `pysam.*`, plain `def` functions) but adds the RESEARCH.md `cdef extern from *` block with `_Static_assert(sizeof(hts_pos_t) == 8, ...)`.

### Byte-level regression tests (D2-08) + CJK canary (D2-10) (NEW tests in existing files)

Assertions via `TestUtils.checkBinaryEqual` (:54-79). Test-class idiom: class-based xunit, `setUpModule(): make_data_files(DATADIR)` module prep, `tmp_path`/`monkeypatch` built-ins only, no unittest.mock (per `.planning/codebase/TESTING.md`). CJK canary: write/read/index round-trip under `tmp_path` with CJK directory+filenames, covering AlignmentFile/VariantFile (.bai/.csi/.tbi), tabix fetch, one dispatch command. Run discipline: `-s` (no capture) is mandatory in `setup.cfg` addopts — never run with capture.

## Shared Patterns

### Platform gating (win32 branch)
**Source:** `setup.py:95-103, 152, 770-791`
**Apply to:** TestUtils dispatch, conftest, generators
```python
        if sys.platform == 'win32':
            ...
```
and the comment-rich `if platform.system() == 'Windows':` block at setup.py:768-791 — Phase 1's precedent of documenting *why* each win32 branch exists (decision IDs in comments) is the house style; carry D2-xx IDs into new comments.

### Cython error handling on fd operations
**Source:** `pysam/libcutils.pyx:353-354`, `pysam/libctabix.pyx:833-834, 848-854`
**Apply to:** every libcport call site
```cython
    if fd_src < 0:
        raise OSError_from_errno("Could not open input", filename_in)
```
Keep the "context string + original filename" argument shape; return-value checks (`== -1` / `< 0`) precede any use of the fd.

### htslib C conditional-compilation guards
**Source:** `htslib/hfile.c:753-756, 766-768, 792-794`
**Apply to:** the PORT-04 `_wopen` shim
```c
#ifdef O_BINARY
    flags |= O_BINARY;
#endif
```
Prefer capability guards (`HAVE_*`/`O_BINARY`) over bare platform guards where the existing file already does; use `#if defined(_WIN32) || defined(__MSYS__)` where it doesn't.

### In-process comparison oracle
**Source:** `tests/TestUtils.py:106-107`
**Apply to:** samtools_test, PileupTestUtils, StreamFiledescriptors, TestSAMFromStringIO rewrites
```python
    lines1 = pysam.samtools.view(*(args + [filename1]))
```
Both comparison sides go through pysam dispatch; the external-oracle coverage moves to the fork CI ubuntu job (zero-regression story).

### Idempotent data generation
**Source:** `tests/TestUtils.py:164-185`
**Apply to:** all three generator directories
stamp-check → lock-mkdir-retry → generate → finally unlock. Generators plug in behind the existing `make_data_files()`; the Makefile/POSIX branch stays byte-identical.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pysam/libcport.pxd` | Cython platform-mapping declaration | compile-time | No `cdef extern from *` platform-switch exists in-tree; use RESEARCH.md Pattern 1 (verified end-to-end on the target toolchain: compiles, links, runs `dup ok: True`) |
| `tests/_compile_sizes.pyx` | pyximport static-assert module | compile-time | No `_Static_assert` module exists; shape = `tests/_compile_test.pyx` consumer skeleton + RESEARCH.md D2-09 excerpt |

## Metadata

**Analog search scope:** `pysam/*.pyx`, `pysam/*.pxd`, `tests/` (all blocker files fully read), `htslib/hfile.c`, `setup.py`, `tests/*/Makefile`
**Files scanned:** ~18 direct reads + grep sweeps (setup.py win32 idiom, off_t consumers, hopen_fd sites)
**Tracked-source gate:** all 11 named analog paths verified via `git ls-files` (11/11 non-empty)
**Pattern extraction date:** 2026-10-12
