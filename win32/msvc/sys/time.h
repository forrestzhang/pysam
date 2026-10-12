/* win32/msvc/sys/time.h -- MSVC drop-in for <sys/time.h> (BUILD-02, 03-03).

   Supplies struct timeval (thread_pool.c:232 computes timedwait
   deadlines through it) and the gettimeofday declaration; the
   implementation lives in win32/msvc/pthread_win32.c.

   The struct is defined behind the same _TIMEVAL_DEFINED guard the
   Windows SDK's winsock2.h uses, so whichever of the two headers comes
   first, the other defers -- a double definition can never occur.

   The __GNUC__ forwarder arm keeps UCRT64 builds on MinGW's real
   sys/time.h (see win32/msvc/unistd.h for the include-order rationale). */

#ifndef PYSAM_WIN32_MSVC_SYS_TIME_H
#define PYSAM_WIN32_MSVC_SYS_TIME_H

#if defined(__GNUC__) && !defined(_MSC_VER)
#include_next <sys/time.h>
#else
#include <time.h>

#ifndef _TIMEVAL_DEFINED
#define _TIMEVAL_DEFINED
struct timeval {
    long tv_sec;   /* seconds */
    long tv_usec;  /* and microseconds */
};
#endif

int gettimeofday(struct timeval *tv, void *tz);
#endif

#endif /* PYSAM_WIN32_MSVC_SYS_TIME_H */
