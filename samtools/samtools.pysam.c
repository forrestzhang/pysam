#include <getopt.h>
#include <unistd.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "samtools.pysam.h"

FILE * samtools_stderr = NULL;
FILE * samtools_stdout = NULL;
const char * samtools_stdout_fn = NULL;


FILE * samtools_set_stderr(int fd)
{
  if (samtools_stderr != NULL)
    fclose(samtools_stderr);
  samtools_stderr = fdopen(fd, "w");
  return samtools_stderr;
}

void samtools_close_stderr(void)
{
  fclose(samtools_stderr);
  samtools_stderr = NULL;
}

FILE * samtools_set_stdout(int fd)
{
  if (samtools_stdout != NULL)
    fclose(samtools_stdout);
  samtools_stdout = fdopen(fd, "w");
  if (samtools_stdout == NULL)
    {
      fprintf(samtools_stderr, "could not set stdout to fd %i", fd);
    }
  return samtools_stdout;
}

void samtools_set_stdout_fn(const char *fn)
{
  samtools_stdout_fn = fn;
}

void samtools_close_stdout(void)
{
  fclose(samtools_stdout);
  samtools_stdout = NULL;
}

int samtools_puts(const char *s)
{
  if (fputs(s, samtools_stdout) == EOF) return EOF;
  return putc('\n', samtools_stdout);
}


#ifdef _WIN32
/* pysam Windows port (Phase 2): UCRT longjmp() unwinds via RtlUnwindEx,
   which raises STATUS_BAD_STACK when it walks the GCC-compiled frames of
   this module, so exit interception crashes the interpreter (seen with
   usage() of depth/flagstat/stats/idxstats/reheader).  GCC's builtins
   restore the saved registers directly with no SEH unwind, which is
   safe within this translation unit (setjmp and longjmp callers both
   live here).  POSIX builds keep the standard setjmp/longjmp below. */
static void *samtools_jmpbuf[5];
#else
static jmp_buf samtools_jmpbuf;
#endif
static int samtools_status = 0;

int samtools_dispatch(int argc, char *argv[])
{
  /* Reset getopt()/getopt_long() processing. */
#if defined __GLIBC__
  optind = 0;
#elif defined _OPTRESET || defined _OPTRESET_DECLARED
  optreset = optind = 1;
#else
  optind = 1;
#endif

#ifdef _WIN32
  if (__builtin_setjmp(samtools_jmpbuf) == 0)
    return samtools_main(argc, argv);
  else
    return samtools_status;
#else
  if (setjmp(samtools_jmpbuf) == 0)
    return samtools_main(argc, argv);
  else
    return samtools_status;
#endif
}

void samtools_exit(int status)
{
  samtools_status = status;
#ifdef _WIN32
  __builtin_longjmp(samtools_jmpbuf, 1);
#else
  longjmp(samtools_jmpbuf, 1);
#endif
}
