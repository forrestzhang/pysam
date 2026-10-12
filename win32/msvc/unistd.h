/* win32/msvc/unistd.h -- MSVC drop-in for <unistd.h> (BUILD-02, 03-03).

   The __GNUC__ forwarder arm is what keeps UCRT64 builds byte-identical:
   include order puts the /I directories ahead of the system directories
   for BOTH toolchains, so when this directory is on the include path a
   bare '#include <unistd.h>' would find this file even under MinGW --
   the forwarder immediately chains to the real system header instead of
   redefining anything. The forwarder arm is proven by compiling
   win32/msvc/shim_selftest.c with 'gcc -fsyntax-only -I win32/msvc'.

   The MSVC arm maps the raw fd trio with fixed-arity macros -- the
   libcport.pxd precedent (D-18): fixed arity keeps the mapping
   compatible with MSVC's conforming preprocessor and cannot capture
   unrelated identifiers such as struct members named read/close.
   usleep and mkstemp are implemented in win32/msvc/pthread_win32.c. */

#ifndef PYSAM_WIN32_MSVC_UNISTD_H
#define PYSAM_WIN32_MSVC_UNISTD_H

#if defined(__GNUC__)
#include_next <unistd.h>
#else
#include <io.h>
#include <process.h>
#include <stdlib.h>

/* MinGW's real unistd.h declares the getopt family, and samtools/bcftools
   sources rely on that (bam_quickcheck.c uses getopt/optind including only
   <unistd.h>). Under MSVC the vendored win32/getopt.h carries the family
   (win32/ is on every extension's include path; the D-16 private-copy
   model links the implementation per tool extension). */
#include <getopt.h>

#define read(fd, buf, count)   _read((fd), (buf), (count))
#define write(fd, buf, count)  _write((fd), (buf), (count))
#define close(fd)              _close((fd))

int usleep(unsigned int usec);
int mkstemp(char *name_template);
#endif

#endif /* PYSAM_WIN32_MSVC_UNISTD_H */
