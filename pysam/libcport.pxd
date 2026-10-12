# cython: language_level=3
"""Centralized fd-I/O platform mapping for pysam (decisions D2-01/D2-04).

All raw file-descriptor I/O in the Cython layer resolves through this single
declaration module so that platform differences are handled at exactly one
point: on Windows the CRT underscore variants are used and every open is
forced into binary mode (`_O_BINARY`, `0x8000`) with the `pmode` argument
masked to `_S_IREAD |_S_IWRITE` (the only bits MSVC's `_open` accepts); on
POSIX every name is an identity alias to the libc symbol, so Linux and macOS
compile to source- and behavior-identical objects (zero-regression
constraint, PROJECT.md).

The switch is implemented in the C preprocessor via `cdef extern from *`
verbatim C. Cython 3.3 (the version this project pins) has no usable
compile-time conditional at the Cython language level: the legacy
compile-time conditionals are deprecated with removal scheduled, and the
compile-time environment names are not plain names. C-preprocessor level
switching is the Cython-maintainer-sanctioned replacement ("should be
handled at C compile time", cython/cython#4310).

Consumers must not branch on the platform at their call sites; they cimport
the portable names and keep POSIX-visible behavior unchanged:

    from pysam.libcport cimport psam_open2 as c_open, PSAM_O_RDONLY as O_RDONLY

`psam_off_t` exists because htslib is compiled with `_FILE_OFFSET_BITS 64`
so `off_t` is 64-bit there, while the MinGW-w64 header default for a plain
`off_t` is 32-bit — publishing the 64-bit alias closes that ABI gap at the
`hseek`/`htell` signatures (pysam/libchtslib.pxd). It is an identity
typedef of `off_t` on POSIX.

The two fixed-arity open forms (no variadic macro) keep the mapping
compilable under MSVC's conforming preprocessor for the Phase 3 toolchain.
"""

cdef extern from *:
    """
    #ifdef _WIN32
    #include <fcntl.h>
    #include <io.h>
    #include <sys/stat.h>
    #define psam_dup(fd)            _dup(fd)
    #define psam_open2(path, flags) \
        _open(path, (flags) | _O_BINARY)
    #define psam_open3(path, flags, mode) \
        _open(path, (flags) | _O_BINARY, (mode) & (_S_IREAD | _S_IWRITE))
    #define psam_read(fd, buf, count)    _read(fd, buf, count)
    #define psam_close(fd)               _close(fd)
    #define PSAM_STDOUT_FILENO           1
    #define PSAM_O_RDONLY                _O_RDONLY
    #define PSAM_O_WRONLY                _O_WRONLY
    #define PSAM_O_CREAT                 _O_CREAT
    #define PSAM_O_TRUNC                 _O_TRUNC
    typedef long long psam_off_t;
    #else
    #include <fcntl.h>
    #include <unistd.h>
    #define psam_dup(fd)            dup(fd)
    #define psam_open2(path, flags) open(path, flags)
    #define psam_open3(path, flags, mode) open(path, flags, mode)
    #define psam_read(fd, buf, count)    read(fd, buf, count)
    #define psam_close(fd)               close(fd)
    #define PSAM_STDOUT_FILENO           STDOUT_FILENO
    #define PSAM_O_RDONLY                O_RDONLY
    #define PSAM_O_WRONLY                O_WRONLY
    #define PSAM_O_CREAT                 O_CREAT
    #define PSAM_O_TRUNC                 O_TRUNC
    typedef off_t psam_off_t;
    #endif
    """

    int psam_dup(int fd)
    int psam_open2(const char *path, int flags)
    int psam_open3(const char *path, int flags, int mode)
    Py_ssize_t psam_read(int fd, void *buf, size_t count)
    int psam_close(int fd)

    int PSAM_O_RDONLY
    int PSAM_O_WRONLY
    int PSAM_O_CREAT
    int PSAM_O_TRUNC
    int PSAM_STDOUT_FILENO

    ctypedef long long psam_off_t
