/* win32/msvc/dirent.h -- MSVC drop-in for <dirent.h> (BUILD-02, 03-04).

   vcfplugin.c:35 / vcfannotate.c:35 (and their .pysam.c twins) include
   <dirent.h> unconditionally; MSVC has none. The opendir/readdir/
   closedir API is implemented in win32/msvc/pthread_win32.c over
   FindFirstFileA/FindNextFileA. Only the surface the trees use is
   provided: iteration plus d_name (the plugin-path scanner reads
   ep->d_name only). The "." / ".." entries are returned, matching
   POSIX readdir semantics; callers that care skip them (vcfplugin's
   extension match does).

   The __GNUC__ forwarder arm keeps UCRT64 builds on MinGW-w64's real
   dirent.h (see win32/msvc/unistd.h for the include-order rationale). */

#ifndef PYSAM_WIN32_MSVC_DIRENT_H
#define PYSAM_WIN32_MSVC_DIRENT_H

#if defined(__GNUC__) && !defined(_MSC_VER)
#include_next <dirent.h>
#else

#include <windows.h>

struct dirent {
    /* NTFS exposes no stable inode through this API; 0 marks unknown */
    unsigned long long d_ino;
    char d_name[MAX_PATH];
};

typedef struct {
    HANDLE find;
    WIN32_FIND_DATAA data;
    struct dirent ent;
    int first;               /* FindFirstFileA already produced entry 1 */
} DIR;

DIR *opendir(const char *path);
struct dirent *readdir(DIR *dir);
int closedir(DIR *dir);

#endif /* __GNUC__ */

#endif /* PYSAM_WIN32_MSVC_DIRENT_H */
