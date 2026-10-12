/* musl-internal header stand-in (vendored for the MSVC build path only).
 *
 * Upstream src/internal/locale_impl.h is deeply coupled to the musl runtime:
 * it includes libc.h and pthread_impl.h and resolves LCTRANS_CUR(msg) through
 * CURRENT_LOCALE (__pthread_self()->locale->cat[LC_MESSAGES]). regerror.c's
 * only use of that header is LCTRANS_CUR(s) around the error strings.
 *
 * musl's own default C-locale behavior for that macro is the identity
 * function: the weak alias __lctrans_impl in src/locale/__lctrans.c is a
 * dummy that returns its argument unchanged. This shim reproduces exactly
 * that default, without dragging any musl runtime machinery into the MSVC
 * build. Documented in vendor/README.md ("vendor/regex" section).
 */
#ifndef _LOCALE_IMPL_H
#define _LOCALE_IMPL_H

#define LCTRANS_CUR(msg) (msg)

#endif
