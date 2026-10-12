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
   needed -- must be defined before the first <windows.h> include.
   NOMINMAX likewise stops windows.h defining min()/max() macros: the
   trees define their own static min/max functions (stats_isize.c:33,
   edlib.c:355) that the macros mangle. */
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif

/* the UCRT flags POSIX-spelled CRT entry points (_open, _mktemp_s, ...)
   C4996-deprecated; the project's MSVC path intentionally uses them.
   Silencing the class centrally keeps /W3 output readable for real
   diagnostics. _CRT_NONSTDC_NO_WARNINGS covers the second deprecation
   family: the POSIX NAMES themselves (each non-stdc declaration is
   wrapped in its own C4996). */
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif
#ifndef _CRT_NONSTDC_NO_WARNINGS
#define _CRT_NONSTDC_NO_WARNINGS
#endif

/* Close the UCRT's legacy non-stdc NAMES gate. With it open, <stdlib.h>
   defines min()/max() macros (gated on _CRT_INTERNAL_NONSTDC_NAMES,
   which this flag controls), and the trees define their own static
   min/max FUNCTIONS (stats_isize.c:33, edlib.c:355) that the macros
   mangle into syntax errors. With the gate closed, the handful of
   POSIX names the trees actually use resolve through the fixed-arity
   mappings below to their ALWAYS-declared underscore spellings
   (_access/_chmod/_getcwd/_mktemp/_strdup) instead of relying on the
   non-stdc declarations. Must precede every CRT include (this file is
   /FI'd first). */
#ifndef _CRT_DECLARE_NONSTDC_NAMES
#define _CRT_DECLARE_NONSTDC_NAMES 0
#endif

#include <BaseTsd.h>   /* SSIZE_T */
#include <direct.h>    /* _mkdir, _rmdir */
#include <fcntl.h>     /* _O_BINARY and friends (see the O_ mappings) */
#include <io.h>        /* _dup, _lseeki64, _chsize_s */
#include <process.h>   /* _getpid */
#include <stdint.h>    /* INTPTR_MAX (SSIZE_MAX below) */
#include <stdio.h>     /* _popen, _pclose */
#include <string.h>    /* _strtok_s */
#include <sys/stat.h>  /* _S_IFMT and friends; the stat -> _stat64 map */
#include <time.h>      /* struct timespec for the nanosleep declaration */

/* htslib uses ssize_t at API/ABI-relevant sites (bgzf.c, hfile). SSIZE_T
   is LONG_PTR, i.e. 64-bit on x64 -- the same width POSIX gives it. */
#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
typedef SSIZE_T ssize_t;
#endif

/* off_t: with the non-stdc names gate closed, MSVC sys/types.h no
   longer defines it (and its open-gate spelling is 32-bit `long` --
   hFILE.offset / hseek / htell would truncate >2GiB offsets). Define
   it at the 64-bit width the lseek mapping below (_lseeki64) returns.
   Deliberately NOT reusing _OFF_T_DEFINED: sys/types.h couples that
   guard to `typedef long _off_t`, which sys/stat.h's struct st_size
   still needs. The gate above keeps sys/types.h's own off_t out, so
   there is no second definition to collide with. */
#ifndef PYSAM_MSVC_OFF_T_DEFINED
#define PYSAM_MSVC_OFF_T_DEFINED
typedef long long off_t;
#endif

/* SSIZE_MAX (header.c:999's parse-length sanity check): POSIX limits.h
   extension; MSVC limits.h does not define it. ssize_t is SSIZE_T =
   LONG_PTR, so its max is INTPTR_MAX. */
#ifndef SSIZE_MAX
#define SSIZE_MAX INTPTR_MAX
#endif

/* PATH_MAX (dict.c's _WIN32 _fullpath arm; the UCRT has none). Match
   cram_io.c's own local definition: FILENAME_MAX (260 under cl). */
#ifndef PATH_MAX
#define PATH_MAX FILENAME_MAX
#endif

/* POSIX stat surface: with the non-stdc gate closed, the plain-S_IF*
   constants, struct stat, and the stat() wrapper are gone (only the
   _-prefixed originals remain). The object-like stat -> _stat64 macro
   covers both the struct tag and the call (cram_io.c, mFILE.c,
   bam_markdup.c, ...), and gives the 64-bit st_size the off_t typedef
   promises. fstat/lstat have no consumers in the trees. */
#define stat _stat64
#ifndef S_IFMT
#define S_IFMT  _S_IFMT
#define S_IFDIR _S_IFDIR
#define S_IFREG _S_IFREG
#define S_IFCHR _S_IFCHR
#define S_IFIFO _S_IFIFO
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

/* access() mode flags (cram_io.c's ref-cache probe). X_OK has no
   faithful Windows equivalent (no execute permission bit); _access
   treats it as existence-and-not-write-protected -- the same
   approximation every Windows port makes. Values are the POSIX
   iostream convention. */
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
     - ftruncate: _chsize_s returns 0/-1 like ftruncate.
     - strtok_r: the UCRT's 3-arg strtok_s is signature- and
       semantics-identical (bam_plcmd.c's tag parser). */
#define dup(fd)                        _dup(fd)
#define lseek(fd, offset, whence)      _lseeki64((fd), (offset), (whence))
#define unlink(path)                   _unlink(path)
#define rmdir(path)                    _rmdir(path)
#define ftruncate(fd, size)            _chsize_s((fd), (size))
#define getpid()                       _getpid()
#define popen(command, mode)           _popen((command), (mode))
#define pclose(stream)                 _pclose(stream)
#define mkdir(path, mode)              _mkdir(path)
#define strtok_r(str, delim, save)     strtok_s((str), (delim), (save))
/* these five were carried by the non-stdc declarations until the gate
   above closed (_CRT_DECLARE_NONSTDC_NAMES=0) -- now mapped like the
   rest of the POSIX storm */
#define access(path, mode)             _access((path), (mode))
#define chmod(path, mode)              _chmod((path), (mode))
#define getcwd(buf, size)              _getcwd((buf), (size))
#define mktemp(template)               _mktemp(template)
#define strdup(s)                      _strdup(s)
/* fd syscall family. read/write/close carry the exact bodies of the
   unistd.h drop-in (identical macro redefinition is legal C, so TUs
   that include <unistd.h> see one definition either way); open and
   setmode complete the set for zlib's gz* TUs and hfile.c, which used
   to rely on the non-stdc declarations under the open gate. Every bare
   open() call site in the trees takes exactly 3 arguments (hfile.c,
   tmp_file.c, reheader.c, gzlib.c) -- MSVC's _open signature. */
#define open(path, oflag, mode)        _open((path), (oflag), (mode))
#define setmode(fd, mode)              _setmode((fd), (mode))
#define read(fd, buf, count)           _read((fd), (buf), (count))
#define write(fd, buf, count)          _write((fd), (buf), (count))
#define close(fd)                      _close((fd))
/* fcntl open(2) flags, same non-stdc-gated story (fcntl.h defines the
   plain spellings only under the internal gate; the _O_* originals are
   unconditional). O_BINARY is a project red line for binary formats.
   O_CLOEXEC has no MSVC counterpart; hfile.c already #ifdef-guards it. */
#ifndef O_BINARY
#define O_BINARY    _O_BINARY
#define O_TEXT      _O_TEXT
#define O_RDONLY    _O_RDONLY
#define O_WRONLY    _O_WRONLY
#define O_RDWR      _O_RDWR
#define O_APPEND    _O_APPEND
#define O_CREAT     _O_CREAT
#define O_TRUNC     _O_TRUNC
#define O_EXCL      _O_EXCL
#define O_TEMPORARY _O_TEMPORARY
#endif

/* nanosleep (hts_internal.h hts_usleep, bam_consensus.c): implemented in
   pthread_win32.c. Declared here because hts_internal.h does not include
   <unistd.h> -- the /FI header is the only place every TU is guaranteed
   to see. Identical redeclaration against the drop-in headers is legal. */
int nanosleep(const struct timespec *req, struct timespec *rem);

/* Cross-module htslib DATA symbols (seq_nt16_str/table/int,
   hts_verbose, pysam_seq_comp_table): consumer-side dllimport lives in
   the declarations themselves -- htslib/htslib/hts_defs.h's HTSLIB_EXPORT
   consumer arm (which annotates all of them except pysam_seq_comp_table,
   guarded in pysam/htslib_util.h). MSVC takes the LAST declaration's
   linkage, so a /FI-side declaration cannot win over the headers' own
   (verified live, 03-04); do not attempt it here. */

#endif /* _MSC_VER */

#endif /* PYSAM_MSVC_COMPAT_H */
