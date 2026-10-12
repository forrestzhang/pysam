/* win32/msvc/pthread_win32.c -- Win32 implementation of the bounded
   pthread surface declared in win32/msvc/pthread.h, plus the gettimeofday
   / mkstemp / usleep shims (BUILD-02, plan 03-03).

   Compiled into libchtslib only, on the MSVC branch of setup.py. The
   substrate choices and their POSIX deviations are documented in
   pthread.h's header comment; the notable mechanics here:

     - PTHREAD_MUTEX_INITIALIZER: the CRITICAL_SECTION member cannot be
       statically initialized, so each pthread_mutex_t carries an
       INIT_ONCE that lazily runs InitializeCriticalSection exactly once
       (InitOnceExecuteOnce blocks racing first users -- no torn init).
     - pthread_cond_timedwait: POSIX absolute timespec deadlines convert
       to the relative milliseconds SleepConditionVariableCS wants; the
       delta is capped just under INFINITE so a far-future deadline
       degrades to "wait indefinitely" rather than "return immediately".
     - mkstemp: _mktemp_s mangles the trailing six X's in place, then the
       open uses _O_BINARY | _O_EXCL (binary mode is a project red line;
       O_EXCL closes the create race _mktemp_s leaves open). */

#include "msvc_compat.h"

#include <errno.h>
#include <fcntl.h>
#include <io.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <windows.h>

#include "pthread.h"
#include "sys/time.h"

/* ---------- threads ---------- */

int pthread_create(pthread_t *tid, const pthread_attr_t *attr,
                   void *(*start)(void *), void *arg) {
    SIZE_T stack = attr ? attr->stacksize : 0;
    HANDLE h;

    /* LPTHREAD_START_ROUTINE is DWORD (*)(LPVOID); the thread's return
       value travels through ExitThread's DWORD (32-bit truncation --
       documented in pthread.h, no bundled caller returns a pointer) */
    h = CreateThread(NULL, stack, (LPTHREAD_START_ROUTINE)start, arg, 0,
                     (LPDWORD)&tid->id);
    if (h == NULL) return (int)GetLastError();
    tid->h = h;
    if (attr && attr->detachstate == PTHREAD_CREATE_DETACHED) {
        CloseHandle(h);
        tid->h = NULL;
    }
    return 0;
}

int pthread_join(pthread_t tid, void **value_ptr) {
    DWORD ec = 0;
    HANDLE h = (HANDLE)tid.h;

    if (h == NULL) return EINVAL;
    if (WaitForSingleObject(h, INFINITE) != WAIT_OBJECT_0)
        return (int)GetLastError();
    if (value_ptr) {
        if (GetExitCodeThread(h, &ec))
            *value_ptr = (void *)(UINT_PTR)ec;
    }
    CloseHandle(h);
    return 0;
}

void pthread_exit(void *value_ptr) {
    ExitThread((DWORD)(UINT_PTR)value_ptr);
}

pthread_t pthread_self(void) {
    pthread_t t;
    t.h = NULL;
    t.id = GetCurrentThreadId();
    return t;
}

int pthread_equal(pthread_t a, pthread_t b) {
    return a.id == b.id;
}

/* pthread_kill: documented no-op (see pthread.h). */
int pthread_kill(pthread_t tid, int sig) {
    (void)tid; (void)sig;
    return 0;
}

/* ---------- mutex (CRITICAL_SECTION, natively recursive) ---------- */

static BOOL CALLBACK pysam_mutex_init_cb(PINIT_ONCE once, PVOID param,
                                         PVOID *ctx) {
    pthread_mutex_t *m = (pthread_mutex_t *)param;
    (void)once; (void)ctx;
    InitializeCriticalSection(&m->cs);
    return TRUE;
}

static void pysam_mutex_ensure_init(pthread_mutex_t *m) {
    InitOnceExecuteOnce(&m->once, pysam_mutex_init_cb, m, NULL);
}

int pthread_mutex_init(pthread_mutex_t *mutex,
                       const pthread_mutexattr_t *attr) {
    (void)attr;  /* CRITICAL_SECTION is always recursive; type recorded
                    by the attr family has no effect here */
    InitOnceInitialize(&mutex->once);
    pysam_mutex_ensure_init(mutex);
    return 0;
}

int pthread_mutex_lock(pthread_mutex_t *mutex) {
    pysam_mutex_ensure_init(mutex);
    EnterCriticalSection(&mutex->cs);
    return 0;
}

int pthread_mutex_unlock(pthread_mutex_t *mutex) {
    pysam_mutex_ensure_init(mutex);
    LeaveCriticalSection(&mutex->cs);
    return 0;
}

int pthread_mutex_destroy(pthread_mutex_t *mutex) {
    pysam_mutex_ensure_init(mutex);
    DeleteCriticalSection(&mutex->cs);
    InitOnceInitialize(&mutex->once);  /* allow POSIX re-init after destroy */
    return 0;
}

int pthread_mutexattr_init(pthread_mutexattr_t *attr) {
    attr->type = PTHREAD_MUTEX_RECURSIVE;  /* the substrate's semantics */
    return 0;
}

int pthread_mutexattr_settype(pthread_mutexattr_t *attr, int type) {
    attr->type = type;
    return 0;
}

int pthread_mutexattr_destroy(pthread_mutexattr_t *attr) {
    (void)attr;
    return 0;
}

/* ---------- condvar (CONDITION_VARIABLE) ---------- */

int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr) {
    (void)attr;
    InitializeConditionVariable(cond);
    return 0;
}

int pthread_cond_signal(pthread_cond_t *cond) {
    WakeConditionVariable(cond);
    return 0;
}

int pthread_cond_broadcast(pthread_cond_t *cond) {
    WakeAllConditionVariable(cond);
    return 0;
}

int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mutex) {
    pysam_mutex_ensure_init(mutex);
    if (!SleepConditionVariableCS(cond, &mutex->cs, INFINITE))
        return (int)GetLastError();
    return 0;
}

int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex,
                           const struct timespec *abstime) {
    struct timeval now;
    ULONGLONG now_ms, abstime_ms, delta_ms;

    pysam_mutex_ensure_init(mutex);
    if (abstime == NULL) return EINVAL;
    gettimeofday(&now, NULL);
    now_ms = (ULONGLONG)now.tv_sec * 1000ULL + (ULONGLONG)now.tv_usec / 1000ULL;
    abstime_ms = (ULONGLONG)abstime->tv_sec * 1000ULL
               + (ULONGLONG)abstime->tv_nsec / 1000000ULL;
    if (abstime_ms <= now_ms)
        delta_ms = 0;
    else
        delta_ms = abstime_ms - now_ms;
    if (delta_ms > 0xFFFFFFFEULL) delta_ms = 0xFFFFFFFEULL;  /* < INFINITE */

    if (!SleepConditionVariableCS(cond, &mutex->cs, (DWORD)delta_ms)) {
        if (GetLastError() == ERROR_TIMEOUT) return ETIMEDOUT;
        return (int)GetLastError();
    }
    return 0;
}

int pthread_cond_destroy(pthread_cond_t *cond) {
    (void)cond;  /* CONDITION_VARIABLE needs no teardown */
    return 0;
}

int pthread_condattr_init(pthread_condattr_t *attr) {
    (void)attr;
    return 0;
}

int pthread_condattr_destroy(pthread_condattr_t *attr) {
    (void)attr;
    return 0;
}

/* ---------- thread attributes ---------- */

int pthread_attr_init(pthread_attr_t *attr) {
    attr->stacksize = 0;  /* 0: CreateThread default */
    attr->detachstate = PTHREAD_CREATE_JOINABLE;
    return 0;
}

int pthread_attr_destroy(pthread_attr_t *attr) {
    (void)attr;
    return 0;
}

int pthread_attr_getstacksize(const pthread_attr_t *attr, size_t *stacksize) {
    *stacksize = attr->stacksize;
    return 0;
}

int pthread_attr_setstacksize(pthread_attr_t *attr, size_t stacksize) {
    attr->stacksize = stacksize;
    return 0;
}

int pthread_attr_setdetachstate(pthread_attr_t *attr, int detachstate) {
    attr->detachstate = detachstate;
    return 0;
}

/* ---------- once (INIT_ONCE) ---------- */

static BOOL CALLBACK pysam_once_trampoline(PINIT_ONCE once, PVOID param,
                                           PVOID *ctx) {
    void (*init_fn)(void) = (void (*)(void))param;
    (void)once; (void)ctx;
    init_fn();
    return TRUE;
}

int pthread_once(pthread_once_t *once, void (*init_fn)(void)) {
    InitOnceExecuteOnce(once, pysam_once_trampoline, (PVOID)init_fn, NULL);
    return 0;
}

/* ---------- TLS (FlsAlloc family) ---------- */

int pthread_key_create(pthread_key_t *key, void (*destructor)(void *)) {
    DWORD k = FlsAlloc((PFLS_CALLBACK_FUNCTION)destructor);
    if (k == FLS_OUT_OF_INDEXES) return EAGAIN;
    *key = k;
    return 0;
}

int pthread_key_delete(pthread_key_t key) {
    return FlsFree(key) ? 0 : EINVAL;
}

void *pthread_getspecific(pthread_key_t key) {
    return FlsGetValue(key);
}

int pthread_setspecific(pthread_key_t key, const void *value) {
    return FlsSetValue(key, (LPVOID)value) ? 0 : EINVAL;
}

/* ---------- time / temp-file shims ---------- */

int gettimeofday(struct timeval *tv, void *tz) {
    FILETIME ft;
    ULARGE_INTEGER since_1601;
    ULONGLONG since_1970;

    (void)tz;  /* timezone argument: unused by every bundled caller */
    if (tv == NULL) return EINVAL;
    GetSystemTimeAsFileTime(&ft);
    since_1601.LowPart = ft.dwLowDateTime;
    since_1601.HighPart = ft.dwHighDateTime;
    /* 116444736000000000: 1601-01-01 -> 1970-01-01, in 100ns ticks */
    since_1970 = since_1601.QuadPart - 116444736000000000ULL;
    tv->tv_sec = (long)(since_1970 / 10000000ULL);
    tv->tv_usec = (long)((since_1970 % 10000000ULL) / 10ULL);
    return 0;
}

int mkstemp(char *name_template) {
    if (_mktemp_s(name_template, strlen(name_template) + 1) != 0)
        return -1;
    /* _O_BINARY is the project red line for binary formats; _O_EXCL
       closes the create race _mktemp_s leaves open */
    return _open(name_template,
                 _O_RDWR | _O_CREAT | _O_EXCL | _O_BINARY,
                 _S_IREAD | _S_IWRITE);
}

int usleep(unsigned int usec) {
    Sleep(usec / 1000U);
    return 0;
}
