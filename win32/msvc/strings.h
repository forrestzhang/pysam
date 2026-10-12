/* win32/msvc/strings.h -- MSVC drop-in for <strings.h> (BUILD-02, 03-03).

   Macro-only: the strcasecmp/strncasecmp mappings live in
   win32/msvc/msvc_compat.h (force-included into every TU), because most
   call sites using those names never include <strings.h> (hts.c does;
   the other ~200 call sites do not). This header exists so that a bare
   '#include <strings.h>' resolves under cl at all.

   The __GNUC__ forwarder arm keeps UCRT64 builds on MinGW's real
   strings.h (see win32/msvc/unistd.h for the include-order rationale). */

#ifndef PYSAM_WIN32_MSVC_STRINGS_H
#define PYSAM_WIN32_MSVC_STRINGS_H

#if defined(__GNUC__)
#include_next <strings.h>
#else
/* mappings live in msvc_compat.h; nothing to define here */
#endif

#endif /* PYSAM_WIN32_MSVC_STRINGS_H */
