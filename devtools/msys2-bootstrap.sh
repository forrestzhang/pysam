#!/bin/sh -e
# Bootstrap the MSYS2 UCRT64 build environment for pysam (Windows).
#
# Manual step 0 (D-15) -- the only manual steps besides running this script:
#   1. Install MSYS2 from https://www.msys2.org/ with the official installer.
#   2. Open the "UCRT64" shell (NOT MINGW64) and let the first `pacman -Syu`
#      finish. If that first update asks to terminate the shell, accept,
#      reopen the UCRT64 shell, and rerun this script (it is idempotent via
#      `--needed`).
#
# Everything after MSYS2 itself is owned by this script: pacman packages,
# environment sanity, venv creation, the canonical editable build, and the
# acceptance smoke gate.
#
# msvcrt-flavored MinGW environments (the legacy MINGW64 shell) are
# UNSUPPORTED: their fd/heap ABI is incompatible with UCRT-based runtimes
# and silently corrupts data (project anti-pattern).
#
# The PKGS list below is the single source of truth for the Windows build
# prerequisites; setup.py's UCRT64 fail-fast message mirrors it verbatim
# (D-03 + D-13).

PKGS='mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pip mingw-w64-ucrt-x86_64-python-setuptools mingw-w64-ucrt-x86_64-python-cython mingw-w64-ucrt-x86_64-toolchain mingw-w64-ucrt-x86_64-llvm-tools mingw-w64-ucrt-x86_64-zlib mingw-w64-ucrt-x86_64-bzip2 mingw-w64-ucrt-x86_64-xz'

# Gate: run inside the UCRT64 shell only (analog of the POSIX
# install-prerequisites.sh detection chain).
if [ "${MSYSTEM:-}" != "UCRT64" ]; then
    echo "ERROR: pysam Windows builds must be bootstrapped inside the" >&2
    echo "MSYS2 UCRT64 shell. Open the 'UCRT64' shell from the MSYS2" >&2
    echo "launcher and rerun: sh devtools/msys2-bootstrap.sh" >&2
    exit 1
fi

# Environment sanity: HTSLIB_MODE must be unset or 'shared'. 'separate'
# silently disables the symbol-conflict check and 'external' skips the
# bundled htslib build entirely (see setup.py).
case "${HTSLIB_MODE:-}" in
    "" | shared) ;;
    *)
        echo "ERROR: HTSLIB_MODE='${HTSLIB_MODE}' is not supported for the" >&2
        echo "Windows build. Unset it or set it to 'shared', then rerun." >&2
        exit 1
        ;;
esac

# Known pacman behaviors (both expected, both recoverable):
#  * The first-ever `pacman -Syu` may ask to terminate the shell: accept,
#    reopen the UCRT64 shell, and rerun this script (--needed makes it
#    idempotent).
#  * llvm-tools may offer to replace binutils tools (e.g. nm): accept the
#    replacement.
echo "Installing UCRT64 toolchain and library packages..."
pacman -Syu --needed $PKGS

echo "Installed package versions:"
for pkg in $PKGS; do
    pacman -Qi "$pkg" | sed -n '1,2p'
done

if ! command -v llvm-nm >/dev/null 2>&1; then
    echo "ERROR: llvm-nm is not on PATH after installation." >&2
    echo "Install it explicitly: pacman -S mingw-w64-ucrt-x86_64-llvm-tools" >&2
    exit 1
fi
llvm-nm --version

# Remote I/O (libcurl/S3/GCS) stays disabled on Windows in v1 (REMOTE-01
# deferred to v2); htslib is configured accordingly.
HTSLIB_CONFIGURE_OPTIONS="--disable-libcurl"
export HTSLIB_CONFIGURE_OPTIONS

# Dev install goes into a venv (D-07), not pacman-managed site-packages.
# --system-site-packages keeps the pacman Cython/setuptools visible: PyPI
# binary wheels are incompatible with the MSYS2 python.
python -m venv --system-site-packages _venv
. _venv/bin/activate

# Canonical one-command build (D-14): the PEP 517 path end to end.
# --no-build-isolation keeps the pacman-provided setuptools/Cython (PEP 517
# isolation would pip-fetch PyPI wheels that cannot run on msys2 python).
python -m pip install -e . --no-build-isolation

# Acceptance gate (D-04): import pysam, build/read a BAM, dispatch one
# samtools and one bcftools command.
python devtools/smoke_test.py

# Troubleshooting:
#
# Rebuild after a configure-option or toolchain change. Stale state makes
# prebuild_libchtslib SKIP the rebuild whenever htslib/libhts.a exists,
# silently reusing the old configuration. Clean before rebuilding:
#     git clean -xfd htslib samtools bcftools
#     rm -f pysam/config.py pysam/*.pyd pysam/*.dll.a
#     rm -rf pysam.egg-info build
# and optionally recreate the venv:  rm -rf _venv
