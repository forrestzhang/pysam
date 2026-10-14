# PORT-01 / D2-03: POSIX-Symbol Grep-Clean Checklist

**Artifact of:** Plan 02-01, Task 3 (decision D2-03 — PORT-01 acceptance = grep-clean audit)
**Audited tree:** `win` branch @ 0b252e65 (post Tasks 1-2)
**Purpose:** every POSIX-only symbol/path in the Cython layer is enumerated with a
disposition and runnable evidence; doubles as the Phase 3 MSVC porting inventory
(symbol → Windows CRT target → MSVC status).

**Disposition vocabulary:** `eliminated` (removed outright) / `platform-guarded`
(switched inside `pysam/libcport.pxd`) / `verified-closed` (already fixed, verified
here by grep) / `out-of-scope-documented` (deferred by an explicit decision).

All evidence commands were run this session from the repo root and their exit
codes recorded (`rc=1` from grep means zero matches — the clean result).

## Inventory

| symbol/path | file:line | disposition | evidence | MSVC status (Phase 3) |
|---|---|---|---|---|
| `from posix.fcntl cimport open as c_open, O_WRONLY, O_CREAT, O_TRUNC` | `pysam/libcutils.pyx:22` (old) | eliminated → `pysam.libcport` (commit dc40dd29) | `grep -rn "from posix" pysam --include=*.pyx --include=*.pxd` → rc=1 (zero matches) | closed for MSVC: mapping is C-preprocessor level, `_open` family exists in MSVC CRT |
| `from posix.unistd cimport dup as c_dup, SEEK_SET, SEEK_CUR, SEEK_END, STDOUT_FILENO` | `pysam/libcutils.pyx:23` (old) | eliminated → `pysam.libcport` + `libc.stdio` (SEEK_* are ISO-C stdio.h constants; `Cython/Includes/libc/stdio.pxd:44`) | same grep → rc=1 | closed: `_dup`/literal `1` + stdio SEEK_* are MSVC-native |
| `from posix.fcntl cimport open as c_open, O_RDONLY` | `pysam/libctabix.pyx:62` (old) | eliminated → `pysam.libcport` (commit 0b252e65) | same grep → rc=1 | closed: same `_open` mapping |
| `from posix.unistd cimport close, dup, read` | `pysam/libctabix.pyx:63` (old) | eliminated → `pysam.libcport` (commit 0b252e65) | same grep → rc=1 | closed: `_close`/`_dup`/`_read` |
| `from posix.unistd cimport dup` | `pysam/libchtslib.pyx:10` (old) | eliminated → `pysam.libcport` (commit 0b252e65) | same grep → rc=1 | closed: `_dup` |
| `from posix.types cimport off_t` | `pysam/libchtslib.pxd:7` (old; W2's missed 4th site) | eliminated → `cimport psam_off_t as off_t` (commit 0b252e65); 64-bit `long long` on Windows matches htslib's `_FILE_OFFSET_BITS 64` build (`htslib/config.h:218`), identity `off_t` on POSIX | `grep -n "cimport psam_off_t as off_t" pysam/libchtslib.pxd` → `7:from pysam.libcport cimport psam_off_t as off_t`; tell/seek roundtrip probe passed (24/24 records) | mapped: `typedef long long psam_off_t`; verify width with D2-09 static asserts under MSVC |
| hardcoded `b"/dev/null"` (W3) | `pysam/libcutils.pyx` dispatch null-out sites (now :390, :397) | verified-closed via `os.devnull` (D2-02): stdlib platform constant — `"NUL"` on Windows, `"/dev/null"` on POSIX; arrived in Phase 1, verified here without code change | `grep -c "os.devnull" pysam/libcutils.pyx` → `2`; `grep -rn "/dev/null" pysam --include=*.pyx --include=*.pxd` → rc=1 (no residual literal) | closed: `"NUL"` is the MSVC/Windows null device |
| `fork` / `signal` / `kill` / `pipe` POSIX-only calls | Cython layer (none found) | verified-closed: zero call sites | `grep -rnE "\b(fork|signal|kill|pipe)\(" pysam --include=*.pyx --include=*.pxd` → rc=1 (zero hits; research predicted zero — confirmed) | n/a — no sites to port |
| unistd-only calls (`usleep/sysconf/getcwd/getpid/chdir/access/unlink/rmdir/getpagesize/lseek/execv/system`) | Cython layer (none found — `write(` hits are Python-level `cpdef write` methods, not unistd `write`) | verified-closed: zero call sites | `grep -rnE "\b(usleep|sysconf|getcwd|getpid|chdir|access|unlink|rmdir|getpagesize|lseek|write|pipe2|execv|system)\(" pysam --include=*.pyx --include=*.pxd` → only `cpdef int write(self, ...)` / `fout.write(...)` / `def write(self, ...)` Python methods | n/a — no sites to port |
| POSIX path separators in string literals (`'/path/to/...'`) | `pysam/libcbcf.pyx:1301,1703,1985,2175,2249,4042` | out-of-scope-documented: docstring example paths (`pysam.VariantFile('/path/to/file.vcf.gz')`), never executed as filesystem operations | `grep -rnE "['\"]/[a-zA-Z.]" pysam --include=*.pyx --include=*.pxd` → 6 hits, all in docstrings; `grep -rnE "(/tmp/\|/bin/\|/usr/)" pysam --include=*.pyx --include=*.pxd` → rc=1 | n/a — docstring text only |
| shell/dev paths in literals (`/tmp/`, `/bin/`, `/usr/`) | Cython layer (none found) | verified-closed: zero sites | grep above → rc=1 | n/a |
| `SEEK_SET/CUR/END` provenance | `pysam/libcutils.pyx:30` (now), `pysam/libcbgzf.pyx:13` (already) | eliminated-posix: both source from `libc.stdio` (ISO-C `stdio.h`, MSVC-native); `io.SEEK_*` uses are Python-level | `grep -rn "SEEK_" pysam --include=*.pyx --include=*.pxd` → only `libc.stdio` cimports, `io.SEEK_*` Python refs, and the libcutils mapping function | closed: ISO-C constants exist under MSVC |
| raw fd `open` without binary mode (PORT-02 live bug, read side) | `pysam/libctabix.pyx:835` (`tabix_compress` copy loop; old :832) | platform-guarded: `psam_open2` forces `_O_BINARY` inside libcport on Windows; RED→GREEN evidence: 203-byte payload with 50 CRLF pairs read back 153 bytes before, 203 bytes byte-identical after | plan verify snippet: `in: 203 out: 203`, `assert back == payload` passes | mapped: `_open(path, flags\|_O_BINARY)` |
| raw fd `open` without binary mode (PORT-02, write side) | `pysam/libcutils.pyx:359` (`save_stdout` redirect; old :352) | platform-guarded: `psam_open3` forces `_O_BINARY` + masks pmode to `_S_IREAD\|_S_IWRITE`; in-process write corruption is currently masked by CPython's startup `_fmode=_O_BINARY` (fdopen `"w"` FILE\* inherits it); standalone-C probe proves the CRT default corrupts without it (14 bytes `hello\r\nworld\r\n`) | flagstat save_stdout byte check: 460 bytes, no CRLF; `grep -c "psam_open3" pysam/libcutils.pyx` → 1 | mapped: `_open(path, (flags)\|_O_BINARY, (mode) & (_S_IREAD\|_S_IWRITE))` — pmode mask is the MSVC-debug-CRT safety (undocumented bits assert) |
| bench-file `samtoolsshell` builders (`os.popen`/`os.system` pipelines) | `tests/PileupTestUtils.py`, `tests/AlignmentFileFetchTestUtils.py`, `tests/*_bench.py` | out-of-scope-documented: **D2-11** — bench files are excluded from the default pytest collection (`setup.cfg testpaths`), so they are not in the "green" perimeter; the collected-file rewrites happen in Plans 02-02/02-03 | D2-11 decision text (02-CONTEXT.md); `*_bench.py` unmatched by pytest `python_files` patterns | n/a — test layer, not shipped code |
| remote-I/O libcurl gates (`http://`/`s3://`/`gs://` open paths) | htslib C layer (`--disable-libcurl` build) | out-of-scope-documented: **v2 deferral** — no Windows libcurl implementation in v1 scope (PROJECT.md decision 4); tests hitting remote I/O are expected documented Windows skips under D2-07's no-silent-skip discipline | PROJECT.md 关键决策 #4; build exports `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl` (Phase 1 D-14 bootstrap) | deferred to v2 — no MSVC work this milestone |
| `fdopen(fd, "w")` in dispatch shim (W10) | `samtools/samtools.pysam.c:19,33`, `bcftools/bcftools.pysam.c:19,33` (from `import/pysam.c` template) | out-of-scope-documented: **W10 explicitly not restructured this phase** — the fd-redirection structure around the dispatch stays untouched; MSVC names it `_fdopen` (one-line `#ifdef _MSC_VER` shim when Phase 3 arrives). Note the FILE\*'s translation mode comes from the `"w"` mode string + CRT `_fmode` (binary under CPython), not from the fd flags | 02-CONTEXT D2-02 ("fd-redirection structure around it stays untouched (W10/`fdopen` territory is deliberately not restructured)"); CONCERNS.md W10 | open for Phase 3: add `fdopen`→`_fdopen` mapping; consider `"wb"` mode string |
| bundled-C tty APIs `isatty`/`fileno` (W4) | `bcftools/consensus.c`, `csq.c`, `reheader.c`, `vcfannotate.c`, `vcfcall.c` (+ `.pysam.c` twins) | out-of-scope-documented: **bundled C layer, usage-test gated on both platforms** — MinGW provides the POSIX names so the UCRT64 build is unaffected; MSVC needs the `win32/unistd.h` shim extension in Phase 3 | CONCERNS.md W4; usage tests exercise the paths identically on Linux | open for Phase 3: extend `win32/unistd.h` with `#define isatty _isatty` / `#define fileno _fileno` |

## The libcport contract (Phase 3 entry point)

Single mapping layer `pysam/libcport.pxd` — one `cdef extern from *` verbatim-C
block, C-preprocessor switched (`#ifdef _WIN32` / `#else`), no deprecated Cython
compile-time conditionals, no variadic macros (two fixed-arity open forms). The
POSIX branch is pure identity aliases, so Linux/macOS objects are unchanged
(zero-regression; fork CI gates it formally in Plan 02-04).

| psam_* name | Windows CRT target | POSIX target | MSVC status (Phase 3) |
|---|---|---|---|
| `psam_dup(fd)` | `_dup` | `dup` | mapped, unverified under MSVC (research A3) |
| `psam_open2(path, flags)` | `_open(path, (flags) \| _O_BINARY)` | `open(path, flags)` | mapped, unverified under MSVC |
| `psam_open3(path, flags, mode)` | `_open(path, (flags) \| _O_BINARY, (mode) & (_S_IREAD \| _S_IWRITE))` | `open(path, flags, mode)` | mapped, unverified under MSVC (pmode mask is the debug-CRT assertion guard) |
| `psam_read(fd, buf, count)` | `_read` | `read` | mapped, unverified under MSVC (int→Py_ssize_t widening is safe) |
| `psam_close(fd)` | `_close` | `close` | mapped, unverified under MSVC |
| `PSAM_O_RDONLY/WRONLY/CREAT/TRUNC` | `_O_*` constants | `O_*` constants | mapped, unverified under MSVC |
| `PSAM_STDOUT_FILENO` | literal `1` | `STDOUT_FILENO` | mapped, unverified under MSVC |
| `psam_off_t` | `typedef long long` (64-bit, matches htslib `_FILE_OFFSET_BITS 64`) | `typedef off_t` (identity) | mapped, unverified under MSVC — verify width with D2-09 static asserts |

**Consumers (all rewired, cimport lines only):**
`pysam/libcutils.pyx` (:25-30 cimports; call sites :359/:390/:397),
`pysam/libctabix.pyx` (:65-66), `pysam/libchtslib.pyx` (:10),
`pysam/libchtslib.pxd` (:7).

## Summary of dispositions

| disposition | count | rows |
|---|---|---|
| eliminated (posix cimports) | 5 | libcutils ×2, libctabix ×1 (2 lines), libchtslib.pyx, libchtslib.pxd |
| platform-guarded (libcport) | 2 | tabix read loop, save_stdout redirect write |
| verified-closed (grep-proven) | 6 | /dev/null via os.devnull (D2-02), fork/signal/kill/pipe, unistd-only calls, shell-path literals, SEEK_* provenance, (libcutils clean sweep) |
| out-of-scope-documented | 4 | bench samtoolsshell (D2-11), libcurl remote I/O (v2), W10 fdopen (not this phase), W4 bundled-C tty (Phase 3 shim) |

**PORT-01 acceptance state:** grep-clean — zero `posix.*` cimports, zero
`/dev/null` literals, zero fork/signal/kill/pipe sites, zero unistd-only calls
across `pysam/*.pyx` and `pysam/*.pxd`; every enumerated residual carries a
disposition citing its decision ID. Formal zero-regression closure = fork CI on
the pushed commits (recorded in Plan 02-04).

---
*Plan 02-01 Task 3 · D2-03 · 2026-10-12*
