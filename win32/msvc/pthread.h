/* win32/msvc/pthread.h -- MSVC drop-in for <pthread.h> (BUILD-02, 03-03).

   Declares exactly the bounded pthread surface the bundled trees use
   (03-RESEARCH Pattern 4's empirically enumerated list, plus the
   pthread_attr and pthread_equal families the enumeration's
   clean-compile stub covered): htslib thread_pool.c, htscodecs utils.c /
   rANS_static4x16pr.c (once + TLS), samtools bam_sort (attr
   detachstate), the tool mains. The implementation is
   win32/msvc/pthread_win32.c over Win32 primitives:

     - mutex:    CRITICAL_SECTION (natively re-entrant -- thread_pool.c
                 sets PTHREAD_MUTEX_RECURSIVE); PTHREAD_MUTEX_INITIALIZER
                 lazily initializes through an INIT_ONCE member
     - condvar:  CONDITION_VARIABLE (timedwait converts the absolute
                 timespec deadline to relative ms via gettimeofday)
     - once:     INIT_ONCE (PTHREAD_ONCE_INIT = INIT_ONCE_STATIC_INIT)
     - TLS:      FlsAlloc family
     - threads:  CreateThread / WaitForSingleObject

   Known, documented deviations from POSIX (all irrelevant to the
   bundled consumers): the default mutex type is recursive (the
   CRITICAL_SECTION substrate cannot be non-recursive); a thread's
   return value passes through ExitThread's DWORD, so joined
   value_ptr only carries the low 32 bits (no bundled caller joins a
   meaningful value); pthread_kill is a no-op stub.

   The __GNUC__ forwarder arm keeps UCRT64 builds on MinGW-w64's real
   pthread.h (winpthreads) -- see win32/msvc/unistd.h for the
   include-order rationale. */

#ifndef PYSAM_WIN32_MSVC_PTHREAD_H
#define PYSAM_WIN32_MSVC_PTHREAD_H

#if defined(__GNUC__) && !defined(_MSC_VER)
#include_next <pthread.h>
#else

#include <windows.h>   /* CRITICAL_SECTION, CONDITION_VARIABLE, INIT_ONCE */
#include <time.h>      /* struct timespec (UCRT time.h defines it) */

/* thread identity: h is the CreateThread HANDLE (NULL for ids obtained
   from pthread_self, where only identity comparison is needed); id is
   the kernel thread id pthread_equal compares */
typedef struct {
    void *h;
    unsigned long id;
} pthread_t;

typedef struct {
    size_t stacksize;
    int detachstate;
} pthread_attr_t;

typedef struct {
    INIT_ONCE once;          /* INIT_ONCE_STATIC_INIT-compatible */
    CRITICAL_SECTION cs;     /* lazily initialized via once */
} pthread_mutex_t;

typedef struct {
    int type;                /* recorded; CRITICAL_SECTION is always recursive */
} pthread_mutexattr_t;

typedef CONDITION_VARIABLE pthread_cond_t;
typedef struct {
    int unused;
} pthread_condattr_t;

typedef DWORD pthread_key_t;
typedef INIT_ONCE pthread_once_t;

#define PTHREAD_MUTEX_INITIALIZER  { INIT_ONCE_STATIC_INIT, { 0 } }
#define PTHREAD_ONCE_INIT          INIT_ONCE_STATIC_INIT

#define PTHREAD_MUTEX_NORMAL       0
#define PTHREAD_MUTEX_RECURSIVE    1
#define PTHREAD_MUTEX_ERRORCHECK   2
#define PTHREAD_MUTEX_DEFAULT      PTHREAD_MUTEX_RECURSIVE

#define PTHREAD_CREATE_JOINABLE    0
#define PTHREAD_CREATE_DETACHED    1

int pthread_create(pthread_t *tid, const pthread_attr_t *attr,
                   void *(*start)(void *), void *arg);
int pthread_join(pthread_t tid, void **value_ptr);
void pthread_exit(void *value_ptr);
pthread_t pthread_self(void);
int pthread_equal(pthread_t a, pthread_t b);

int pthread_mutex_init(pthread_mutex_t *mutex,
                       const pthread_mutexattr_t *attr);
int pthread_mutex_lock(pthread_mutex_t *mutex);
int pthread_mutex_unlock(pthread_mutex_t *mutex);
int pthread_mutex_destroy(pthread_mutex_t *mutex);
int pthread_mutexattr_init(pthread_mutexattr_t *attr);
int pthread_mutexattr_settype(pthread_mutexattr_t *attr, int type);
int pthread_mutexattr_destroy(pthread_mutexattr_t *attr);

int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr);
int pthread_cond_signal(pthread_cond_t *cond);
int pthread_cond_broadcast(pthread_cond_t *cond);
int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mutex);
int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex,
                           const struct timespec *abstime);
int pthread_cond_destroy(pthread_cond_t *cond);
int pthread_condattr_init(pthread_condattr_t *attr);
int pthread_condattr_destroy(pthread_condattr_t *attr);

int pthread_attr_init(pthread_attr_t *attr);
int pthread_attr_destroy(pthread_attr_t *attr);
int pthread_attr_getstacksize(const pthread_attr_t *attr, size_t *stacksize);
int pthread_attr_setstacksize(pthread_attr_t *attr, size_t stacksize);
int pthread_attr_setdetachstate(pthread_attr_t *attr, int detachstate);

int pthread_once(pthread_once_t *once, void (*init_fn)(void));

int pthread_key_create(pthread_key_t *key, void (*destructor)(void *));
int pthread_key_delete(pthread_key_t key);
void *pthread_getspecific(pthread_key_t key);
int pthread_setspecific(pthread_key_t key, const void *value);

/* thread_pool.c's hts_tpool_destroy teardown issues
   pthread_kill(p->t[i].tid, SIGINT); workers observe the shutdown flag
   instead, so this is a documented no-op returning success. */
int pthread_kill(pthread_t tid, int sig);

#endif /* __GNUC__ */

#endif /* PYSAM_WIN32_MSVC_PTHREAD_H */
