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
   diagnostics. */
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif

#include <BaseTsd.h>   /* SSIZE_T */
#include <sys/stat.h>  /* S_IFMT, S_IFREG, S_IFDIR for the S_IS* macros */

/* htslib uses ssize_t at API/ABI-relevant sites (bgzf.c, hfile). SSIZE_T
   is LONG_PTR, i.e. 64-bit on x64 -- the same width POSIX gives it. */
#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
typedef SSIZE_T ssize_t;
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

#endif /* _MSC_VER */

#endif /* PYSAM_MSVC_COMPAT_H */
