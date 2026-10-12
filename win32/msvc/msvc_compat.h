/* win32/msvc/msvc_compat.h -- central MSVC compatibility header
   (BUILD-02, plan 03-03).

   This header is force-included (/FI) into every translation unit on
   the MSVC branch of setup.py, and ONLY there. The whole body is
   guarded on _MSC_VER so that a GCC compile that reaches this file
   (shim_selftest.c includes it explicitly as the UCRT64 sentinel) sees
   an empty file -- the win32/msvc/ directory must be invisible to the
   UCRT64 build (zero-regression red line).

   Why the mappings live here rather than in the drop-in headers: this
   file follows the same single-switch discipline as pysam/libcport.pxd
   (D-18) -- most call sites using these POSIX names never include the
   POSIX header that would canonically declare them (strcasecmp call
   sites rarely include <strings.h>), so the only place every
   translation unit is guaranteed to see is the force-included header.
   Keep this list global-by-design; do not move entries into per-file
   patches (whack-a-mole prohibition). */

#ifndef PYSAM_MSVC_COMPAT_H
#define PYSAM_MSVC_COMPAT_H

#ifdef _MSC_VER

/* math constants (M_LN10 etc., errmod.c) are gated behind this in the
   UCRT; must be defined before the first <math.h> include */
#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

/* trim <windows.h>; subsystem headers are included explicitly where
   needed -- must be defined before the first <windows.h> include */
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

/* the UCRT flags POSIX-spelled CRT entry points (_open, _mktemp_s, ...)
   C4996-deprecated; the project's MSVC path intentionally uses them.
   Silencing the class centrally keeps /W3 output readable for real
   diagnostics. _CRT_NONSTDC_NO_WARNINGS covers the second deprecation
   family: the POSIX NAMES themselves (strdup/access/chmod/getcwd/mktemp
   are all declared by the UCRT under non-stdc names, each wrapped in
   its own C4996). */
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif
#ifndef _CRT_NONSTDC_NO_WARNINGS
#define _CRT_NONSTDC_NO_WARNINGS
#endif

#include <BaseTsd.h>   /* SSIZE_T */
#include <direct.h>    /* _mkdir, _rmdir; POSIX-name getcwd (non-stdc) */
#include <io.h>        /* _dup, _lseeki64, _chsize_s; access/chmod (non-stdc) */
#include <process.h>   /* _getpid */
#include <stdint.h>    /* INTPTR_MAX (SSIZE_MAX below) */
#include <stdio.h>     /* _popen, _pclose */
#include <sys/stat.h>  /* S_IFMT, S_IFREG, S_IFDIR for the S_IS* macros */
#include <time.h>      /* struct timespec for the nanosleep declaration */

/* htslib uses ssize_t at API/ABI-relevant sites (bgzf.c, hfile). SSIZE_T
   is LONG_PTR, i.e. 64-bit on x64 -- the same width POSIX gives it. */
#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
typedef SSIZE_T ssize_t;
#endif

/* SSIZE_MAX (header.c:999's parse-length sanity check): POSIX limits.h
   extension; MSVC limits.h does not define it. ssize_t is SSIZE_T =
   LONG_PTR, so its max is INTPTR_MAX. */
#ifndef SSIZE_MAX
#define SSIZE_MAX INTPTR_MAX
#endif

/* stat mode-classification macros (POSIX; MSVC sys/stat.h lacks them) */
#ifndef S_ISREG
#define S_ISREG(m) (((m) & S_IFMT) == S_IFREG)
#endif
#ifndef S_ISDIR
#define S_ISDIR(m) (((m) & S_IFMT) == S_IFDIR)
#endif

/* POSIX name mappings to the underscore-prefixed UCRT spellings.
   Function-like names here are simple object-like macros: the UCRT
   declares the underscore forms in the standard headers, and the POSIX
   spellings are never declared at all. fdopen is the W10 mapping
   deferred from 02-PORT01-CHECKLIST. */
#define strcasecmp  _stricmp
#define strncasecmp _strnicmp
#define fdopen      _fdopen
#define isatty      _isatty
#define fileno      _fileno

/* standard-descriptor fileno constants (thread_pool.c, samtools mains) */
#define STDIN_FILENO  0
#define STDOUT_FILENO 1
#define STDERR_FILENO 2

/* access() mode flags: the UCRT declares access() itself (corecrt_io.h,
   non-stdc names) but not the POSIX flag constants. X_OK has no faithful
   Windows equivalent (no execute permission bit); _access treats it as
   existence-and-not-write-protected -- the same approximation every
   Windows port makes. Values are the POSIX iostream convention. */
#ifndef F_OK
#define F_OK 0
#define X_OK 6
#define W_OK 2
#define R_OK 4
#endif

/* POSIX stat mode constants (cram_io.c chmod, extsort.c _chmod,
   vcfsort.c chmod): MSVC sys/stat.h ships only _S_IREAD/_S_IWRITE/
   _S_IEXEC. Values are the POSIX bits, matching what the callers'
   semantic intent (owner read/write) maps to under _chmod. */
#ifndef S_IRUSR
#define S_IRUSR 0400
#define S_IWUSR 0200
#define S_IXUSR 0100
#define S_IRWXU 0700
#define S_IRGRP 0040
#define S_IWGRP 0020
#define S_IXGRP 0010
#define S_IRWXG 0070
#define S_IROTH 0004
#define S_IWOTH 0002
#define S_IXOTH 0001
#define S_IRWXO 0007
#endif

/* POSIX io/process names the UCRT declares ONLY underscore-prefixed (or
   not at all): fixed-arity mappings, the libcport.pxd precedent (D-18)
   -- fixed arity keeps the mapping compatible with MSVC's conforming
   preprocessor and cannot capture unrelated identifiers.
     - mkdir: UCRT's _mkdir has no mode parameter; Windows ACLs ignore
       the POSIX mode anyway, and discarded macro arguments are never
       name-looked-up, so vcfisec.c's S_IRWXU|... argument is inert.
     - lseek: _lseeki64 (plain _lseek returns 32-bit long; hfile.c
       fd_seek returns htslib's 64-bit off_t -- truncation is silent).
     - ftruncate: _chsize_s returns 0/-1 like ftruncate. */
#define dup(fd)                        _dup(fd)
#define lseek(fd, offset, whence)      _lseeki64((fd), (offset), (whence))
#define unlink(path)                   _unlink(path)
#define rmdir(path)                    _rmdir(path)
#define ftruncate(fd, size)            _chsize_s((fd), (size))
#define getpid()                       _getpid()
#define popen(command, mode)           _popen((command), (mode))
#define pclose(stream)                 _pclose(stream)
#define mkdir(path, mode)              _mkdir(path)

/* nanosleep (hts_internal.h hts_usleep, bam_consensus.c): implemented in
   pthread_win32.c. Declared here because hts_internal.h does not include
   <unistd.h> -- the /FI header is the only place every TU is guaranteed
   to see. Identical redeclaration against the drop-in headers is legal. */
int nanosleep(const struct timespec *req, struct timespec *rem);

#endif /* _MSC_VER */

#endif /* PYSAM_MSVC_COMPAT_H */
