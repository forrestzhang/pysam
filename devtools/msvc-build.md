# MSVC (cl.exe) build discipline — BUILD-02

This document is the MSVC analogue of `devtools/msys2-bootstrap.sh`: the
single source of truth for provisioning and rebuilding on the MSVC path.
setup.py's MSVC-mode banner mirrors its prerequisite wording verbatim
(D-03/D-13 single-source pattern, one message in two places).

The UCRT64 document stays authoritative for the MinGW path; nothing in
this file touches it. The two toolchains alternate safely in one
checkout (see "config.h alternation" below).

## Manual step 0 — prerequisites (the only manual steps)

1. **Visual Studio Build Tools with the C++ workload (2022 or later).**
   Download from https://visualstudio.microsoft.com/downloads/ ("Build
   Tools for Visual Studio", optional "Desktop development with C++"
   workload). No VS-version path is ever referenced by the build —
   setuptools locates the toolchain itself via vswhere, so VS 2022,
   2024, 2026, ... all work without code changes. (This machine runs
   VS 2026 BuildTools 18.4.1 with toolsets 14.44 + 14.50.)
2. **A win-amd64 CPython 3.13+** — python.org or conda builds both work;
   this machine uses Miniconda 3.13.5 (`D:/miniconda3/python.exe`).
   MSYS2's mingw python is NOT an MSVC-path interpreter (it takes the
   UCRT64 path instead).

Everything else is owned by setup.py: no vcvars, no environment setup.
**setuptools runs the Visual Studio environment discovery internally**
(`_get_vc_env`): a build from a plain Git Bash with a zero MSVC
environment is the verified canonical invocation.

## Environment gate (what setup.py does for you)

- On an nt python whose `sysconfig.get_platform()` starts with `mingw`,
  setup.py stays on the UCRT64 path (real configure + make).
- On any other nt python (win-amd64), setup.py selects MSVC mode and
  prints:

      # pysam: MSVC build mode (win CPython + cl.exe via setuptools)
      # pysam: MSVC builds require Visual Studio Build Tools with the
      # pysam: C++ workload (2022 or later) - see devtools/msvc-build.md

  If the Build Tools are missing, the build fails at compile time with
  setuptools' own "Microsoft Visual C++ 14.0 or greater is required"
  error — that is the MSVC fail-fast; install the prerequisite above.
- MSVC mode never invokes autotools: `htslib/config.h` is deterministically
  rewritten from the checked-in `win32/config.h.msvc` on every run, and
  the htslib source list is the hard-coded mirror of `htslib/Makefile`
  `LIBHTS_OBJS` (see `MSVC_LIBHTS_OBJS` in setup.py).

## One venv per toolchain

The MSVC interpreter gets its own venv, separate from the UCRT64 `_venv`
(build products separate naturally: `build/temp.win-amd64-cpython-3*`
vs `build/temp.mingw*`, and the `*.cp313-win_amd64.pyd` vs
`*.cp314-mingw*.pyd` extension suffixes):

    D:/miniconda3/python.exe -m venv _venv-msvc
    _venv-msvc/Scripts/python.exe -m pip install "Cython>=3,<4" pytest setuptools

(setuptools is listed explicitly: Python 3.12+ venvs no longer preinstall
it, and setup.py imports it at module level.)

## The symbol gate needs llvm-nm on PATH

The BUILD-03 symbol gate calls plain `llvm-nm`; on the MSVC path it
reads the emitted `.lib` import libraries (llvm-nm parses MSVC archives
— verified). Prepend the UCRT64 bin dir before building:

    export PATH="/c/msys64/ucrt64/bin:$PATH"

## Canonical build

From a plain Git Bash (no vcvars, no MSYS2 shell), repo root:

    export PATH="/c/msys64/ucrt64/bin:$PATH"
    _venv-msvc/Scripts/python.exe setup.py build_ext --inplace

Acceptance gate (same smoke script as UCRT64):

    _venv-msvc/Scripts/python.exe devtools/smoke_test.py

## Rebuild discipline

- **config.h alternation**: `htslib/config.h` flips content between
  toolchains (real configure output vs `win32/config.h.msvc`). Both
  paths rewrite it on every `setup.py` run, so switching toolchains
  simply works — but a stale binary built against the other toolchain's
  config needs a rebuild. When in doubt: full rebuild of the affected
  tree (`rm -rf build` + `--force`, see below).
- **After editing htslib/samtools/bcftools C sources**: extensions do
  not relink on source changes automatically (Phase-2 lesson):

      _venv-msvc/Scripts/python.exe setup.py build_ext --inplace --force

- **Clean rebuild** (configuration or toolchain change):

      rm -rf build pysam.egg-info
      rm -f pysam/*.pyd pysam/*.lib
      _venv-msvc/Scripts/python.exe setup.py build_ext --inplace --force

- **gcc probes / UCRT64 verification runs must happen inside the
  MSYS2 shell** (`MSYSTEM=UCRT64 CHERE_INVOKING=1
  /c/msys64/usr/bin/bash.exe -lc '...'`): outside it gcc fails
  *silently* (exit 1, no diagnostics) — the zero-regression control
  (UCRT64 `setup.py --name` after every MSVC change) is only meaningful
  from inside that shell.
- Raw cl.exe experiments (outside setuptools) need the vcvars64.bat
  wrapper pattern — a plain `cmd //c "cl ..."` fails path resolution;
  write a .bat that calls vcvars64.bat first, then the cl command.

## Zero-regression control

Every setup.py change on the MSVC path must keep the UCRT64 path
byte-identical (module graph keyed on platform, flags keyed on
compiler_type). Verify after each change, from the UCRT64 shell:

    MSYSTEM=UCRT64 CHERE_INVOKING=1 /c/msys64/usr/bin/bash.exe -lc \
      'cd /d/Github/pysam && HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl \
       MAKE=mingw32-make _venv/bin/python.exe setup.py --name'

Fork CI (ubuntu/macos) additionally guards the POSIX path on every push.
