# Phase 1: MinGW-w64 构建系统 - Context

**Gathered:** 2026-09-17
**Status:** Ready for planning

<domain>
## Phase Boundary

A developer on MSYS2 UCRT64 runs one canonical command (`pip install -e .` inside a UCRT64 venv) and gets a working pysam: all Cython extension modules plus bundled htslib/htscodecs/samtools/bcftools compiled through the existing autotools flow (`sh configure` + `make` re-plumbed, not replaced), `import pysam` succeeding, one BAM opened, and one samtools/bcftools command dispatched via `_pysam_dispatch`. `check_ext_symbol_conflicts` actually runs on Windows via llvm-nm and fails the build on duplicate symbols. Linux/macOS builds and CI stay green throughout (BUILD-01 + BUILD-03).

NOT in this phase: MSVC toolchain (Phase 3), Windows CI runners and wheels (Phase 4), POSIX-dependency cleanup in Cython sources beyond what compilation requires, test-suite porting (Phase 2), remote I/O (v2).

</domain>

<decisions>
## Implementation Decisions

### Pre-locked project constraints (carried forward — do not re-litigate)
- **Autotools flow stays**: `sh configure` and `make` run inside MSYS2; only the `setup.py` invocation pipeline is adapted. Pre-baked `config.h` is the Phase 3 MSVC approach (BUILD-01).
- **Symbol check is mandatory on Windows**: via llvm-nm, actually executed, build fails on duplicates — never silently skipped (BUILD-03, success criterion 3).
- **libcurl/remote I/O stays off** on the Windows path in v1 (REMOTE-01 deferred to v2): configure with `--disable-libcurl` on Windows.
- **UCRT64 environment mandatory**; msvcrt-flavored MinGW is a blocking anti-pattern (python.org CPython fd/heap ABI corruption).
- **MinGW output is dev-validation only** — never distributed as a wheel (wheels are MSVC-only, Phase 3+4).

### Target Python runtime
- **D-01:** The Phase 1 build targets **MSYS2 UCRT64's own pacman python** (`mingw-w64-ucrt-x86_64-python`), NOT python.org CPython — setuptools finds GCC natively, no import-library glue needed. — **Reversibility:** costly — the bootstrap script, INSTALL docs, fail-fast gating, and the v1 support boundary below all encode this choice; Phases 2–4 assume it.
- **D-02:** Validate against a **single Python version** (whatever UCRT64 currently ships). The version matrix is CI-03's job in Phase 4.
- **D-03:** **Strict fail-fast** outside UCRT64: when a Windows build is attempted outside a UCRT64 shell, `setup.py` stops immediately with one actionable message listing the pacman packages to install (message content mirrors the bootstrap script). Protects against msvcrt-MinGW attempts failing deep in compilation.
- **D-04:** Acceptance smoke check is a **committed script** (`devtools/smoke_test.py` or similar): imports pysam, opens a BAM from test data, dispatches one samtools/bcftools command, exits nonzero on failure. Reused later as the Phase 4 CI smoke gate.
- **D-05:** **GCC ↔ python.org-CPython is explicitly unsupported in v1** — documented in one sentence; the real-user Python is served by the Phase 3 MSVC path. Prevents wasted effort on gendef/dlltool glue.
- **D-06:** The build checkout stays at **`D:\Github\pysam`** (Windows path, single checkout, Git Bash workflow unchanged); the UCRT64 shell builds via `/d/Github/pysam`, accepting slower drvfs build iteration.
- **D-07:** Dev installs go into a **venv** created inside the UCRT64 shell (`python -m venv` + `pip install -e .`), not into pacman-managed site-packages.

### setup.py change style
- **D-08:** **Minimal inline diff philosophy**: small `sys.platform == 'win32'` / MSYSTEM-gated branches exactly where the POSIX pipeline breaks (configure/make invocation points, rpath flag, nm call). No restructuring of the 807-line monolith, no helper-module extraction. Keeps the diff upstreamable and the zero-regression review surface small.
- **D-09:** The dead "untested" win32 branch at `setup.py:634` is **rewritten in place** — same insertion point, new working UCRT64 body. No parallel stale branch left behind.
- **D-10:** From the 2013 `win32/` shims, **only `win32/getopt.c` survives** on the UCRT64 include path (MinGW-w64 has no getopt_long — *premise falsified at the first real build; superseded by D-16 for the linking model*). `win32/unistd.h` and `win32/stdint.h` are dropped — UCRT64 GCC ships real ones, and the stale shim is missing `isatty`/`fileno` (W7). Phase researcher verifies per-shim during planning.

### POSIX regression guard
- **D-11:** Linux/macOS zero-regression is verified by **fork CI on every push**: the `win` branch is pushed to the GitHub fork after each committed change; the existing `ci.yaml` ubuntu+macos jobs run automatically on push.
- **D-12:** Success criterion 4 ("existing builds and CI stay green") is defined as: **ubuntu and macos jobs green on the phase's final commit**. The FreeBSD/NetBSD VM jobs are advisory only.

### MSYS2 bootstrap form
- **D-13:** Bootstrap deliverable is **script + docs**: a committed UCRT64 bootstrap script (pacman toolchain/library package list + venv creation + build deps; Windows counterpart to `devtools/install-prerequisites.sh`) plus an INSTALL Windows section documenting the two manual steps. The script is the single source of truth for the fail-fast message content.
- **D-14:** The canonical documented one-step build command is **`pip install -e .`** inside the UCRT64 venv (exercises the PEP 517 path end to end). `setup.py build` remains functional but undocumented.
- **D-15:** Division of labor: **MSYS2 itself is installed manually** (documented link, one GUI run); **the script owns everything after** (pacman packages, venv, build deps).

### First real-build corrections (plan 03, human-approved)
- **D-16:** The D-10 linking premise is **falsified**: MinGW's getopt family lives in the *static* libmingwex.a, and plain data references (optarg/optind) cannot resolve through a PE import library during archive scanning, so every extension pulls its own mingwex getopt copy regardless of who exports one — sharing win32/getopt.c via libchtslib's import library necessarily collides ("multiple definition of 'getopt'"). Adopted model = the isolation of separate samtools.exe/bcftools.exe on Windows: win32/getopt.c stays compiled into libchtslib (also needed for the Phase 3 MSVC path), the getopt family is **excluded from every win32 module's exports** (`-Wl,--exclude-symbols=`), each tool extension keeps a private mingwex copy, and the BUILD-03 gate exempts exactly the closed set {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt} on win32 — every other duplicate still fails the build. Human-approved checkpoint decision (2026-09-18).

### Claude's Discretion
- Exact pacman package list contents (researcher/planner determine precise package names and versions).
- Smoke script location and internal structure (`devtools/smoke_test.py` suggested, not mandated).
- The precise detection mechanism for "am I in UCRT64" (MSYSTEM env var vs compiler probe vs both).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition and requirements
- `.planning/PROJECT.md` — Core value, constraints (zero POSIX regression, upstreamable patches only), key decisions table
- `.planning/REQUIREMENTS.md` — BUILD-01 and BUILD-03 definitions (this phase); v1/v2 boundary incl. REMOTE-01 deferral
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria 1–4, dependency notes
- `.claude/CLAUDE.md` — Project instructions: hard constraints, anti-patterns table (msvcrt MinGW, text-mode I/O), roadmap ordering

### Codebase maps (build-system relevant)
- `.planning/codebase/STACK.md` — Build System Detail section: setup.py entry points, HTSLIB_MODE env vars, platform-specific handling, generated files
- `.planning/codebase/ARCHITECTURE.md` — Build path data flow, extension dependency chain (`setup.py:666-672`), POSIX-assumption constraints
- `.planning/codebase/CONCERNS.md` — Windows blockers W1–W10 (esp. W1 autotools hardwiring, W5 rpath flag, W7 stale shims), tech debt on the monolithic setup.py, security note on `shell=True` configure invocation

### Prior research
- `.planning/research/SUMMARY.md` — Bootstrap research synthesis; STACK confidence MEDIUM on UCRT64-GCC ↔ CPython `build_ext` glue (now scoped to MSYS2-native python by D-01)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `win32/getopt.c` + `win32/getopt.h` — vendored getopt_long, still needed by bundled samtools/bcftools main loops under UCRT64 (D-10)
- `HTSLIB_MODE` / `HTSLIB_CONFIGURE_OPTIONS` / `PYSAM_*` env-var machinery — established configuration surface; Windows options should follow the same env-var pattern rather than inventing new config
- `CyExtension` `init_func`/`prebuild_func` hooks (`setup.py`) — the natural mechanism for running `make lib-static` and any Windows-specific prebuild steps
- `devtools/install-prerequisites.sh` — POSIX counterpart whose structure the new UCRT64 bootstrap script should mirror (D-13)
- Empty-`config.h` fallback at `setup.py:535-541` — existing hint of the no-configure path (Phase 3 will need it; Phase 1 keeps real configure)

### Established Patterns
- Platform branching by `sys.platform == 'darwin'` inline branches (`setup.py:46`, `:401-423`) — D-08's minimal-inline style extends this existing pattern with a win32 branch
- Env-var-driven build configuration (no config files) — keep Windows gating consistent
- Post-link verification via `check_ext_symbol_conflicts` (`setup.py:320-337`) — extend tool invocation (llvm-nm), keep the fail-on-duplicate contract

### Integration Points
- `run_configure()` / `run_make_print_config()` / `run_make()` / `run_nm_defined_symbols()` (`setup.py:61-112`) — the four subprocess call sites that need UCRT64-path handling
- `configure_library()` (`setup.py:247-268`) and the `prebuild_libchtslib` hook (`setup.py:678-692`) — where configure/make orchestration gates
- rpath branch `setup.py:419-423` — needs explicit win32 elif (no rpath on Windows; W5)
- Dead win32 branch `setup.py:634` — rewrite target (D-09)
- `pysam/config.py` generation from `htslib/config.h` (`setup.py:597-620`) — must keep working with MSYS2-generated config.h

</code_context>

<specifics>
## Specific Ideas

- The bootstrap script's package list should double verbatim as the fail-fast error message content — one source of truth (D-03 + D-13).
- The smoke script should be designed from the start to be reusable as the Phase 4 CI smoke gate (D-04).
- `pip install -e .` is the command all docs and the phase's success demonstration should use; do not document the setup.py direct path (D-14).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-MinGW-w64 构建系统*
*Context gathered: 2026-09-17*
