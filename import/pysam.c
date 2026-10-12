#include <getopt.h>
#include <unistd.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "@pysam@.pysam.h"

FILE * @pysam@_stderr = NULL;
FILE * @pysam@_stdout = NULL;
const char * @pysam@_stdout_fn = NULL;


FILE * @pysam@_set_stderr(int fd)
{
  if (@pysam@_stderr != NULL)
    fclose(@pysam@_stderr);
  @pysam@_stderr = fdopen(fd, "w");
  return @pysam@_stderr;
}

void @pysam@_close_stderr(void)
{
  fclose(@pysam@_stderr);
  @pysam@_stderr = NULL;
}

FILE * @pysam@_set_stdout(int fd)
{
  if (@pysam@_stdout != NULL)
    fclose(@pysam@_stdout);
  @pysam@_stdout = fdopen(fd, "w");
  if (@pysam@_stdout == NULL)
    {
      fprintf(@pysam@_stderr, "could not set stdout to fd %i", fd);
    }
  return @pysam@_stdout;
}

void @pysam@_set_stdout_fn(const char *fn)
{
  @pysam@_stdout_fn = fn;
}

void @pysam@_close_stdout(void)
{
  fclose(@pysam@_stdout);
  @pysam@_stdout = NULL;
}

int @pysam@_puts(const char *s)
{
  if (fputs(s, @pysam@_stdout) == EOF) return EOF;
  return putc('\n', @pysam@_stdout);
}


/* pysam Windows port (Phase 2; compiler gate per D-20): UCRT longjmp()
   unwinds via RtlUnwindEx, which raises STATUS_BAD_STACK when it walks
   the GCC-compiled frames of this module, so exit interception crashes
   the interpreter.  GCC's builtins restore the saved registers directly
   with no SEH unwind, which is safe within this translation unit
   (setjmp and longjmp callers both live here).  MSVC provides neither
   builtin and its standard longjmp is the supported path across
   MSVC-compiled frames, so MSVC builds keep the standard setjmp/longjmp
   below.  POSIX builds keep the standard setjmp/longjmp below. */
#if defined(_WIN32) && !defined(_MSC_VER)
#define @pysam@_DISPATCH_GCC_BUILTIN_JMP
#endif

#ifdef @pysam@_DISPATCH_GCC_BUILTIN_JMP
static void *@pysam@_jmpbuf[5];
#else
static jmp_buf @pysam@_jmpbuf;
#endif
static int @pysam@_status = 0;

int @pysam@_dispatch(int argc, char *argv[])
{
  /* Reset getopt()/getopt_long() processing. */
#if defined __GLIBC__ || defined _MSC_VER
  /* _MSC_VER: the vendored win32/getopt.c IS GNU getopt (a private copy
     compiled into each tool module), which implements the glibc
     optind=0 reinitialize idiom.  optind=1 alone leaves getopt's
     internal permutation state (nextchar/first_nonopt) stale across
     dispatches, so a later dispatch can misparse its own options --
     seen live as a view -H -o dispatch dropping its -o and writing
     the header into the devnull capture (empty output, exit 0).
     MinGW keeps optind=1: its getopt is mingwex's BSD-style copy. */
  optind = 0;
#elif defined _OPTRESET || defined _OPTRESET_DECLARED
  optreset = optind = 1;
#else
  optind = 1;
#endif

#ifdef @pysam@_DISPATCH_GCC_BUILTIN_JMP
  if (__builtin_setjmp(@pysam@_jmpbuf) == 0)
    return @pysam@_main(argc, argv);
  else
    return @pysam@_status;
#else
  if (setjmp(@pysam@_jmpbuf) == 0)
    return @pysam@_main(argc, argv);
  else
    return @pysam@_status;
#endif
}

void @pysam@_exit(int status)
{
  @pysam@_status = status;
#ifdef @pysam@_DISPATCH_GCC_BUILTIN_JMP
  __builtin_longjmp(@pysam@_jmpbuf, 1);
#else
  longjmp(@pysam@_jmpbuf, 1);
#endif
}
