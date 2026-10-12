/* win32/msvc/shim_selftest.c -- permanent shim-layer probe
   (BUILD-02, plan 03-03).

   Includes the central compat header and all four drop-in headers and
   touches one symbol or type of each (pthread_mutex_t family, gettimeofday,
   strcasecmp, ssize_t, STDIN_FILENO). Doubles as the UCRT64 forwarder
   sentinel: this file must also compile under UCRT64 gcc
   ('gcc -fsyntax-only -I win32/msvc win32/msvc/shim_selftest.c'), where
   every header takes its __GNUC__ forwarder arm -- proving the shim
   layer cannot shadow or redefine MinGW's system headers. */

#include "msvc_compat.h"

#include <string.h>
#include <strings.h>
#include <sys/time.h>
#include <unistd.h>
#include <pthread.h>

static void once_ran(void) { /* pthread_once target */ }

int main(void) {
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    pthread_mutexattr_t mattr;
    pthread_cond_t cond;
    pthread_once_t once = PTHREAD_ONCE_INIT;
    struct timeval tv;
    ssize_t len = 0;
    int fd;

    if (pthread_mutex_init(&mutex, NULL) != 0) return 1;
    if (pthread_mutex_lock(&mutex) != 0) return 2;
    if (pthread_mutex_unlock(&mutex) != 0) return 3;
    if (pthread_mutexattr_init(&mattr) != 0) return 4;
    if (pthread_mutexattr_settype(&mattr, PTHREAD_MUTEX_RECURSIVE) != 0)
        return 5;
    if (pthread_mutexattr_destroy(&mattr) != 0) return 6;
    if (pthread_mutex_destroy(&mutex) != 0) return 7;

    if (pthread_cond_init(&cond, NULL) != 0) return 8;
    if (pthread_cond_signal(&cond) != 0) return 9;
    if (pthread_cond_destroy(&cond) != 0) return 10;

    if (pthread_once(&once, once_ran) != 0) return 11;

    if (gettimeofday(&tv, NULL) != 0) return 12;

    if (strcasecmp("pysam", "PYSAM") != 0) return 13;
    if (strncasecmp("pysam", "PYSAM", 5) != 0) return 14;

    fd = STDIN_FILENO;
    if (fd == STDOUT_FILENO || fd == STDERR_FILENO) return 15;

    len = (ssize_t)tv.tv_sec;
    return (int)(len == 0);  /* 0 == success */
}
