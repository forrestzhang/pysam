---
phase: 03-msvc
verified: 2026-10-13T10:55:30Z
status: passed
score: 11/11 must-haves verified
covered_files: [".gitignore", ".planning/phases/03-msvc/03-01-PLAN.md", ".planning/phases/03-msvc/03-01-SUMMARY.md", ".planning/phases/03-msvc/03-02-PLAN.md", ".planning/phases/03-msvc/03-02-SUMMARY.md", ".planning/phases/03-msvc/03-03-PLAN.md", ".planning/phases/03-msvc/03-03-SUMMARY.md", ".planning/phases/03-msvc/03-04-PLAN.md", ".planning/phases/03-msvc/03-04-SUMMARY.md", ".planning/phases/03-msvc/03-05-PLAN.md", ".planning/phases/03-msvc/03-05-SUMMARY.md", "bcftools/abuf.c", "bcftools/abuf.c.pysam.c", "bcftools/bcftools.pysam.c", "bcftools/hex.h", "bcftools/variantkey.h", "bcftools/vcfgtcheck.c", "bcftools/vcfgtcheck.c.pysam.c", "bcftools/version.c", "bcftools/version.c.pysam.c", "devtools/check_libhts_objs_lockstep.py", "devtools/msvc-build.md", "devtools/msvc_compile_probe.py", "devtools/probe_symbol_check.py", "htslib/hts_internal.h", "htslib/htslib/hts_defs.h", "import/pysam.c", "pysam/htslib_util.h", "pysam/libcutils.pyx", "samtools/bam_cat.c.pysam.c", "samtools/bam_reheader.c.pysam.c", "samtools/coverage.c", "samtools/coverage.c.pysam.c", "samtools/samtools.pysam.c", "setup.py", "tests/PortabilityRegression_test.py", "tests/_compile_sizes.pyx", "vendor/.gitattributes", "vendor/HASHES.txt", "vendor/README.md", "vendor/bzip2/LICENSE", "vendor/bzip2/blocksort.c", "vendor/bzip2/bzlib.c", "vendor/bzip2/bzlib.h", "vendor/bzip2/bzlib_private.h", "vendor/bzip2/compress.c", "vendor/bzip2/crctable.c", "vendor/bzip2/decompress.c", "vendor/bzip2/huffman.c", "vendor/bzip2/randtable.c", "vendor/regex/COPYRIGHT", "vendor/regex/locale_impl.h", "vendor/regex/regcomp.c", "vendor/regex/regerror.c", "vendor/regex/regex.h", "vendor/regex/regexec.c", "vendor/regex/tre-mem.c", "vendor/regex/tre.h", "vendor/xz/COPYING", "vendor/xz/COPYING.0BSD", "vendor/xz/COPYING.GPLv2", "vendor/xz/COPYING.GPLv3", "vendor/xz/COPYING.LGPLv2.1", "vendor/xz/src/common/mythread.h", "vendor/xz/src/common/sysdefs.h", "vendor/xz/src/common/tuklib_common.h", "vendor/xz/src/common/tuklib_config.h", "vendor/xz/src/common/tuklib_cpucores.c", "vendor/xz/src/common/tuklib_cpucores.h", "vendor/xz/src/common/tuklib_integer.h", "vendor/xz/src/common/tuklib_physmem.c", "vendor/xz/src/common/tuklib_physmem.h", "vendor/xz/src/liblzma/api/lzma.h", "vendor/xz/src/liblzma/api/lzma/base.h", "vendor/xz/src/liblzma/api/lzma/bcj.h", "vendor/xz/src/liblzma/api/lzma/block.h", "vendor/xz/src/liblzma/api/lzma/check.h", "vendor/xz/src/liblzma/api/lzma/container.h", "vendor/xz/src/liblzma/api/lzma/delta.h", "vendor/xz/src/liblzma/api/lzma/filter.h", "vendor/xz/src/liblzma/api/lzma/hardware.h", "vendor/xz/src/liblzma/api/lzma/index.h", "vendor/xz/src/liblzma/api/lzma/index_hash.h", "vendor/xz/src/liblzma/api/lzma/lzma12.h", "vendor/xz/src/liblzma/api/lzma/stream_flags.h", "vendor/xz/src/liblzma/api/lzma/version.h", "vendor/xz/src/liblzma/api/lzma/vli.h", "vendor/xz/src/liblzma/check/check.c", "vendor/xz/src/liblzma/check/check.h", "vendor/xz/src/liblzma/check/crc32_arm64.h", "vendor/xz/src/liblzma/check/crc32_fast.c", "vendor/xz/src/liblzma/check/crc32_loongarch.h", "vendor/xz/src/liblzma/check/crc32_small.c", "vendor/xz/src/liblzma/check/crc32_table_be.h", "vendor/xz/src/liblzma/check/crc32_table_le.h", "vendor/xz/src/liblzma/check/crc32_tablegen.c", "vendor/xz/src/liblzma/check/crc64_fast.c", "vendor/xz/src/liblzma/check/crc64_small.c", "vendor/xz/src/liblzma/check/crc64_table_be.h", "vendor/xz/src/liblzma/check/crc64_table_le.h", "vendor/xz/src/liblzma/check/crc64_tablegen.c", "vendor/xz/src/liblzma/check/crc_clmul_consts_gen.c", "vendor/xz/src/liblzma/check/crc_common.h", "vendor/xz/src/liblzma/check/crc_x86_clmul.h", "vendor/xz/src/liblzma/check/sha256.c", "vendor/xz/src/liblzma/common/alone_decoder.c", "vendor/xz/src/liblzma/common/alone_decoder.h", "vendor/xz/src/liblzma/common/alone_encoder.c", "vendor/xz/src/liblzma/common/auto_decoder.c", "vendor/xz/src/liblzma/common/block_buffer_decoder.c", "vendor/xz/src/liblzma/common/block_buffer_encoder.c", "vendor/xz/src/liblzma/common/block_buffer_encoder.h", "vendor/xz/src/liblzma/common/block_decoder.c", "vendor/xz/src/liblzma/common/block_decoder.h", "vendor/xz/src/liblzma/common/block_encoder.c", "vendor/xz/src/liblzma/common/block_encoder.h", "vendor/xz/src/liblzma/common/block_header_decoder.c", "vendor/xz/src/liblzma/common/block_header_encoder.c", "vendor/xz/src/liblzma/common/block_util.c", "vendor/xz/src/liblzma/common/common.c", "vendor/xz/src/liblzma/common/common.h", "vendor/xz/src/liblzma/common/easy_buffer_encoder.c", "vendor/xz/src/liblzma/common/easy_decoder_memusage.c", "vendor/xz/src/liblzma/common/easy_encoder.c", "vendor/xz/src/liblzma/common/easy_encoder_memusage.c", "vendor/xz/src/liblzma/common/easy_preset.c", "vendor/xz/src/liblzma/common/easy_preset.h", "vendor/xz/src/liblzma/common/file_info.c", "vendor/xz/src/liblzma/common/filter_buffer_decoder.c", "vendor/xz/src/liblzma/common/filter_buffer_encoder.c", "vendor/xz/src/liblzma/common/filter_common.c", "vendor/xz/src/liblzma/common/filter_common.h", "vendor/xz/src/liblzma/common/filter_decoder.c", "vendor/xz/src/liblzma/common/filter_decoder.h", "vendor/xz/src/liblzma/common/filter_encoder.c", "vendor/xz/src/liblzma/common/filter_encoder.h", "vendor/xz/src/liblzma/common/filter_flags_decoder.c", "vendor/xz/src/liblzma/common/filter_flags_encoder.c", "vendor/xz/src/liblzma/common/hardware_cputhreads.c", "vendor/xz/src/liblzma/common/hardware_physmem.c", "vendor/xz/src/liblzma/common/index.c", "vendor/xz/src/liblzma/common/index.h", "vendor/xz/src/liblzma/common/index_decoder.c", "vendor/xz/src/liblzma/common/index_decoder.h", "vendor/xz/src/liblzma/common/index_encoder.c", "vendor/xz/src/liblzma/common/index_encoder.h", "vendor/xz/src/liblzma/common/index_hash.c", "vendor/xz/src/liblzma/common/lzip_decoder.c", "vendor/xz/src/liblzma/common/lzip_decoder.h", "vendor/xz/src/liblzma/common/memcmplen.h", "vendor/xz/src/liblzma/common/microlzma_decoder.c", "vendor/xz/src/liblzma/common/microlzma_encoder.c", "vendor/xz/src/liblzma/common/outqueue.c", "vendor/xz/src/liblzma/common/outqueue.h", "vendor/xz/src/liblzma/common/stream_buffer_decoder.c", "vendor/xz/src/liblzma/common/stream_buffer_encoder.c", "vendor/xz/src/liblzma/common/stream_decoder.c", "vendor/xz/src/liblzma/common/stream_decoder.h", "vendor/xz/src/liblzma/common/stream_decoder_mt.c", "vendor/xz/src/liblzma/common/stream_encoder.c", "vendor/xz/src/liblzma/common/stream_encoder_mt.c", "vendor/xz/src/liblzma/common/stream_flags_common.c", "vendor/xz/src/liblzma/common/stream_flags_common.h", "vendor/xz/src/liblzma/common/stream_flags_decoder.c", "vendor/xz/src/liblzma/common/stream_flags_encoder.c", "vendor/xz/src/liblzma/common/string_conversion.c", "vendor/xz/src/liblzma/common/vli_decoder.c", "vendor/xz/src/liblzma/common/vli_encoder.c", "vendor/xz/src/liblzma/common/vli_size.c", "vendor/xz/src/liblzma/delta/delta_common.c", "vendor/xz/src/liblzma/delta/delta_common.h", "vendor/xz/src/liblzma/delta/delta_decoder.c", "vendor/xz/src/liblzma/delta/delta_decoder.h", "vendor/xz/src/liblzma/delta/delta_encoder.c", "vendor/xz/src/liblzma/delta/delta_encoder.h", "vendor/xz/src/liblzma/delta/delta_private.h", "vendor/xz/src/liblzma/lz/lz_decoder.c", "vendor/xz/src/liblzma/lz/lz_decoder.h", "vendor/xz/src/liblzma/lz/lz_encoder.c", "vendor/xz/src/liblzma/lz/lz_encoder.h", "vendor/xz/src/liblzma/lz/lz_encoder_hash.h", "vendor/xz/src/liblzma/lz/lz_encoder_hash_table.h", "vendor/xz/src/liblzma/lz/lz_encoder_mf.c", "vendor/xz/src/liblzma/lzma/fastpos.h", "vendor/xz/src/liblzma/lzma/fastpos_table.c", "vendor/xz/src/liblzma/lzma/fastpos_tablegen.c", "vendor/xz/src/liblzma/lzma/lzma2_decoder.c", "vendor/xz/src/liblzma/lzma/lzma2_decoder.h", "vendor/xz/src/liblzma/lzma/lzma2_encoder.c", "vendor/xz/src/liblzma/lzma/lzma2_encoder.h", "vendor/xz/src/liblzma/lzma/lzma_common.h", "vendor/xz/src/liblzma/lzma/lzma_decoder.c", "vendor/xz/src/liblzma/lzma/lzma_decoder.h", "vendor/xz/src/liblzma/lzma/lzma_encoder.c", "vendor/xz/src/liblzma/lzma/lzma_encoder.h", "vendor/xz/src/liblzma/lzma/lzma_encoder_optimum_fast.c", "vendor/xz/src/liblzma/lzma/lzma_encoder_optimum_normal.c", "vendor/xz/src/liblzma/lzma/lzma_encoder_presets.c", "vendor/xz/src/liblzma/lzma/lzma_encoder_private.h", "vendor/xz/src/liblzma/rangecoder/price.h", "vendor/xz/src/liblzma/rangecoder/price_table.c", "vendor/xz/src/liblzma/rangecoder/price_tablegen.c", "vendor/xz/src/liblzma/rangecoder/range_common.h", "vendor/xz/src/liblzma/rangecoder/range_decoder.h", "vendor/xz/src/liblzma/rangecoder/range_encoder.h", "vendor/xz/src/liblzma/simple/arm.c", "vendor/xz/src/liblzma/simple/arm64.c", "vendor/xz/src/liblzma/simple/armthumb.c", "vendor/xz/src/liblzma/simple/ia64.c", "vendor/xz/src/liblzma/simple/powerpc.c", "vendor/xz/src/liblzma/simple/riscv.c", "vendor/xz/src/liblzma/simple/simple_coder.c", "vendor/xz/src/liblzma/simple/simple_coder.h", "vendor/xz/src/liblzma/simple/simple_decoder.c", "vendor/xz/src/liblzma/simple/simple_decoder.h", "vendor/xz/src/liblzma/simple/simple_encoder.c", "vendor/xz/src/liblzma/simple/simple_encoder.h", "vendor/xz/src/liblzma/simple/simple_private.h", "vendor/xz/src/liblzma/simple/sparc.c", "vendor/xz/src/liblzma/simple/x86.c", "vendor/xz/windows/INSTALL-MSVC.txt", "vendor/xz/windows/INSTALL-MinGW-w64_with_Autotools.txt", "vendor/xz/windows/INSTALL-MinGW-w64_with_CMake.txt", "vendor/xz/windows/README-Windows.txt", "vendor/xz/windows/build-with-cmake.bat", "vendor/xz/windows/build.bash", "vendor/xz/windows/liblzma-crt-mixing.txt", "vendor/zlib/LICENSE", "vendor/zlib/README", "vendor/zlib/adler32.c", "vendor/zlib/compress.c", "vendor/zlib/crc32.c", "vendor/zlib/crc32.h", "vendor/zlib/deflate.c", "vendor/zlib/deflate.h", "vendor/zlib/gzclose.c", "vendor/zlib/gzguts.h", "vendor/zlib/gzlib.c", "vendor/zlib/gzread.c", "vendor/zlib/gzwrite.c", "vendor/zlib/infback.c", "vendor/zlib/inffast.c", "vendor/zlib/inffast.h", "vendor/zlib/inffixed.h", "vendor/zlib/inflate.c", "vendor/zlib/inflate.h", "vendor/zlib/inftrees.c", "vendor/zlib/inftrees.h", "vendor/zlib/trees.c", "vendor/zlib/trees.h", "vendor/zlib/uncompr.c", "vendor/zlib/zconf.h", "vendor/zlib/zlib.h", "vendor/zlib/zutil.c", "vendor/zlib/zutil.h", "win32/bcftools_exports.def", "win32/chtslib_exports.def", "win32/config.h.msvc", "win32/msvc/dirent.h", "win32/msvc/msvc_compat.h", "win32/msvc/pthread.h", "win32/msvc/pthread_win32.c", "win32/msvc/shim_selftest.c", "win32/msvc/strings.h", "win32/msvc/sys/time.h", "win32/msvc/unistd.h", "win32/samtools_exports.def"]
covered_digest: "v3:sha256:61c01ee231693819e4c71b3eea093163a5f3bf788100c0fe7de518ab8d571949"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 11/11
  reason: "STALE-REFRESH (#4682) for milestone closeout — prior pass 2026-10-12T17:43:09Z at tree 5ecd0bc1; Phase 5 afterwards touched covered sources (setup.py comparator, shim headers/selftest, PortabilityRegression_test, new devtools probes)"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 03: MSVC Build System Verification Report

**Phase Goal:** pysam 可用 MSVC（Build Tools for VS 2022）完整构建并通过全量测试 — 官方 wheel 生态的原生工具链就位。(Machine runs VS 2026 Build Tools with v143+v145 toolsets; toolset presence, not the marketing year, is the criterion — per the recorded research.)
**Verified:** 2026-10-13T10:55:30Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH (#4682): full re-verify against the current tree at HEAD `6adf94e2` after Phase 5 touched covered sources

## Goal Achievement

### Observable Truths

The 11 merged must-have truths (ROADMAP SC-1/2/3 + five PLAN must_haves) from the prior 11/11 pass, re-verified against the CURRENT tree at HEAD `6adf94e2`. Phase 5's deltas over covered sources (setup.py lockstep comparator + win32-guarded wiring; shim_selftest dirent sentinel; dirent.h/pthread.h end-tag renames; +6 oracle teeth tests; comparator/probe devtools) were each individually examined and behaviorally re-proven — not accepted from SUMMARY claims.

| # | Truth | Status | Evidence (all re-run/re-read at HEAD `6adf94e2`) |
| --- | --- | --- | --- |
| 1 | SC-1: MSVC setup.py branch — compiler_type dispatch, pre-baked win32/config.h.msvc, explicit source lists, zero autotools on the MSVC path | ✓ VERIFIED | setup.py at HEAD = prior-verified bytes + exactly two Phase-5 hunks (comparator fn :151-191; wiring :877-879). Wiring confirmed to sit in the **non-MSVC else arm** after `run_make_print_config()` — the MSVC arm (:843-859, config.h.msvc rewrite + hard-coded mirror, no configure/make) is untouched and autotools-free. **Verifier re-ran**: `_venv-msvc/Scripts/python.exe setup.py --name` → exit 0, and htslib/config.h immediately after the run: `HAVE_LIBBZ2 1` ×1, GCC-builtin/attribute probe keys ×0 (deterministic rewrite re-proven; the on-disk file had been in UCRT64-configure state before the run — alternation by design). Subprocess audit re-run vs phase base `e53be051`: added lines referencing run_configure/run_make/run_nm/subprocess = 1, removed twin = 1 (the documented re-gated move; the Phase-5 comparator adds zero — it is pure-Python set comparison). MSVC_LIBHTS_OBJS mirror: 52 entries, 52 unique. Wiring greps: IS_MSVC_PYTHON ×10, std:c11 ×5, /IMPLIB: ×3, /DEF: ×3, HTS_BUILDING_LIBRARY ×3, dirname(get_ext_fullpath) ×2. |
| 2 | SC-2: MSVC artifacts import and the full default-collection suite is green, reconciled against the Phase-2 baseline | ✓ VERIFIED | **Independently re-run by verifier at HEAD**: `_venv-msvc/Scripts/python.exe -m pytest -q` → `1034 passed, 15 skipped in 25.31s`, exit 0. Skips unchanged at 15 (no skip creep). Count delta vs the phase-3-time 1028 = +6, all accounted for by Phase 5's additive `TestWin32OracleReadback` teeth class (6 test methods, verifier-counted in tests/PortabilityRegression_test.py) — later-phase test additions, not phase-3 scope loss. 03-SC2-RECONCILIATION.md (unchanged since prior pass) remains the phase-time parity record: 1028/15 vs 1027/15 baseline, empty exemption list. |
| 3 | SC-3: single centralized MSVC shim layer + clang-cl fallback evaluation decision record | ✓ VERIFIED | `win32/msvc/` 8 files; all five drop-ins (unistd/strings/sys/time/pthread/dirent) carry the `__GNUC__ && !_MSC_VER` forwarder arm. **Verifier re-ran the UCRT64 sentinel on the current (post-Phase-5) headers**: `gcc -fsyntax-only -I win32/msvc win32/msvc/shim_selftest.c` → FORWARDER-OK; the sentinel now touches all 5 drop-in surfaces incl. the new `struct dirent` probe (IN-01 closed). Stale `#endif /* __GNUC__ */` end comments: 0 across win32/msvc/ (IN-02 closed). 03-CLANGCL-EVAL.md unchanged since prior full read (4 sections, 17 clang-cl refs, contingency installs blocking-human). |
| 4 | D-17: out-of-tree MSVC build passes the symbol gate via the /IMPLIB: dirname path (Phase-4 wheel shape) | ✓ VERIFIED | **Verifier re-probed at HEAD**: `build/lib.win-amd64-cpython-313/pysam/` holds 13 emitted `.lib` import libraries; `llvm-nm -g -P` parses `libchtslib*.lib` → 2504 symbol rows; **every one of the 13 extension `.lib`s lists PyInit_ exports** (2 rows each). Emission and gate probe both derive from `get_ext_fullpath` dirname (setup.py unchanged in this region since the prior pass). The 6-cell windows CI matrix at the current code state (below) builds MSVC wheels end-to-end — the Phase-4 consumer of this shape. |
| 5 | D-20: dispatch setjmp branch compiler-gated in template and both twins (lockstep) | ✓ VERIFIED | **Verifier re-ran all gates at HEAD**: `grep -c "defined(_WIN32) && !defined(_MSC_VER)"` == 1 in each of import/pysam.c, samtools/samtools.pysam.c, bcftools/bcftools.pysam.c; sed regeneration proof re-run — `sed 's/@pysam@/<tool>/g' import/pysam.c` diffs clean against BOTH twins. |
| 6 | BUILD-02 C99 surface closed (VLA heap-allocated under MSVC; no array-parameter static qualifier) | ✓ VERIFIED | Re-read at HEAD: coverage.c:233-243 `#if defined(_MSC_VER)` → `malloc(hist_size * sizeof(double))` + `if (!hist_data)` NULL-check with print_error_errno + early return; `#else` keeps the VLA verbatim (POSIX bytes unchanged). Twin parity diff-verified identical. WR-01(review) NULL-check present in both twins ×1. `grep -c "\[static "` htslib/hts_internal.h == 0. |
| 7 | WR-01: dispatch-captured stdout decodes locale-independently, permanent regression test in suite | ✓ VERIFIED | Re-read at HEAD: libcutils.pyx `_collect` `open(fn, "rb")` ×1; strict-first UTF-8 decode with raw-bytes fallback (03-05 mechanism; honest comment matches behavior — WR-04(review) fix holds). `class TestDispatchOutputEncoding` present; exercised in the 1034-test green suite re-run on this toolchain. |
| 8 | vendor/ dependency closure with recorded provenance, no binaries/archives, UCRT64 untouched | ✓ VERIFIED | vendor/{zlib,bzip2,xz,regex} + HASHES.txt (sha256 rows ≥ 4) + README.md all present; license files (zlib LICENSE, bzip2 LICENSE, xz COPYING, regex COPYRIGHT) present; `git ls-files vendor/` archive/binary scan == 0. Trees unchanged since the prior pass (not in any post-5ecd0bc1 code commit); all four compile in the green MSVC build (stronger than probe evidence). |
| 9 | Full MSVC build of all 13 extensions + bundled + vendored deps completes; import, BAM round-trip, samtools/bcftools dispatch work (03-04 tracer) | ✓ VERIFIED | **Verifier re-ran the full suite at HEAD** (superset of devtools/smoke_test coverage): 1034/15/0 exit 0 — imports pysam, reads/writes BAM/CRAM, dispatches both tool families. 13 inplace `pysam/*cp313-win_amd64.pyd` (mtimes 2026-10-13T01:21, post-dating the last code commit `7b0c4256`) + 13 out-of-tree `.lib`s on disk. |
| 10 | Zero-regression: UCRT64 full suite green on the current tree; fork CI green on the current code state | ✓ VERIFIED | **Verifier re-ran the UCRT64 suite at HEAD** (after the comparator's parity configure — the designed config.h alternation): `1034 passed, 15 skipped in 22.72s`, exit 0 — identical counts to the MSVC run. UCRT64 `setup.py --name` control: exit 0 (module graph assembles; real configure path intact). **CI verdict via API**: run 38380672667 → head_sha `965760f1` == conclusion success, **25/25 jobs success** incl. the 6-cell windows matrix (3.10-3.15) and ubuntu/macos; `965760f1` is an ancestor of HEAD and the 3 commits after it (`f5607d75`, `160ef327`, `6adf94e2`) are docs-only — the verified code state IS the current code state. Prior pass's N-1 (unpushed review commits) is thereby resolved. |
| 11 | Code review convergence: 0 critical / 0 warning open; info items recorded as backlog | ✓ VERIFIED | 03-REVIEW-DISPOSITION.md: WR-01..WR-04 all `fixed` — re-verified in code at HEAD (malloc NULL-check in both coverage twins; `!defined(_MSC_VER)` forwarder gates ×5; X_OK = POSIX 1 with honest approximation comment; _collect comment matches strict-first behavior). Of the 9 info rows, IN-01/IN-02 are now closed in code by Phase 5 (dirent sentinel; end-tag renames — verifier-verified above) and the disposition was annotated accordingly at this refresh (open 9→7); IN-03..IN-09 remain recorded advisory backlog, none silently dropped. |

**Score:** 11/11 truths verified (0 present, behavior-unverified)

### Phase-5 Delta Examination (STALE-REFRESH Focus)

Every covered-source change since the prior pass (`git diff 5ecd0bc1..HEAD`, 7 files) was inspected and re-proven:

| Delta | Assessment | Evidence |
| ----- | ---------- | -------- |
| setup.py +54 (comparator `check_msvc_libhts_objs_lockstep` :151-191, wiring :877-879) | Additive, strengthening; MSVC arm untouched | Wiring inside the non-MSVC else arm; MSVC `setup.py --name` exit 0 + config.h rewrite re-proven; subprocess audit unchanged (added=1/removed=1, the documented re-gated move) |
| 52-TU mirror now machine-checked (IN-W2 closure) | **Verifier ran**: `MAKE=mingw32-make _venv/bin/python.exe devtools/check_libhts_objs_lockstep.py --self-test` (UCRT64 shell) | `lockstep OK: mirror == parity expansion (52 TUs)`; both teeth fire (synthetic drift → LinkError; duplicated mirror entry → LinkError); exit 0. The script ast-extracts setup.py's real comparator — single source of truth, no re-implementation |
| shim_selftest.c +13 (dirent sentinel) / dirent.h, pthread.h end-tag renames | IN-01/IN-02 closure | gcc sentinel FORWARDER-OK at HEAD; sentinel touches all 5 drop-ins; 0 stale end comments |
| tests/PortabilityRegression_test.py +108 (`TestWin32OracleReadback`, 6 tests) | Additive teeth tests | Counted in the diff; both suites green at 1034 (1028 + 6) |
| devtools/check_libhts_objs_lockstep.py (new), devtools/probe_symbol_check.py (cwd/EXT_SUFFIX scoping fix) | Devtools only; not on any build path | Read in full / diff-read; probe fix is UCRT64-side hardening |

### Advisory (New Scope, Unevidenced)

Re-verification ran; no advisory items found — every Phase-5 touch on covered sources was evidenced green on both toolchains at HEAD. Informational notes only:

| # | Note | Severity | Detail |
| --- | --- | --- | --- |
| N-1 | Prior note N-1 RESOLVED | ℹ️ Info | The prior pass's unpushed-review-commits concern is closed: the CI-verified SHA `965760f1` (run 38380672667, 25/25 success incl. windows matrix) is the current code state; only docs commits follow it. |
| N-2 | WR-01 truth wording superseded (carried) | ℹ️ Info | Unchanged from prior pass: plan 03-01's "replacement" wording was corrected by 03-05 to strict-first + bytes fallback; intent (locale-independent, never mojibake, never raise) holds, test-covered on both toolchains (re-run green). |

### Required Artifacts

`gsd_run query verify.artifacts` reports 0/0 for these plans (their `must_haves.artifacts` are plain strings, not `{path, provides}` objects); manual three-level verification performed, as at the prior pass. All artifacts exist, are substantive, and are wired/exercised by the green builds/suites re-run at HEAD.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| setup.py (MSVC two-level dispatch + Phase-5 comparator) | gate + module graph + flags split + lockstep gate | ✓ VERIFIED | Diff-audited vs prior-verified bytes: only the two comparator hunks added; both arms re-run (`--name` exit 0 ×2) |
| win32/config.h.msvc | curated pre-baked config, zero GCC-probe keys | ✓ VERIFIED | Unchanged since prior pass (builtin-key grep 0); rewrite behavior re-proven via MSVC run |
| win32/msvc/ (8 files incl. shim_selftest) | centralized shim layer | ✓ VERIFIED | All exist; 5/5 forwarder arms; sentinel FORWARDER-OK at HEAD (now incl. dirent) |
| win32/{chtslib,samtools,bcftools}_exports.def | supplementary export lists | ✓ VERIFIED | Unchanged since prior pass; exercised by the green builds |
| vendor/{zlib,bzip2,xz,regex} + HASHES.txt + README.md | MSVC dependency closure + provenance | ✓ VERIFIED | Files present; 0 archives/binaries tracked; compiled in the green build |
| devtools/msvc_compile_probe.py, devtools/msvc-build.md | probe tool + rebuild discipline doc | ✓ VERIFIED | Present, unchanged |
| devtools/check_libhts_objs_lockstep.py (Phase 5) | machine-checked mirror | ✓ VERIFIED | Self-test + teeth run by verifier, exit 0 |
| .planning/phases/03-msvc/03-SC2-RECONCILIATION.md | SC-2 parity evidence | ✓ VERIFIED | Unchanged since prior full read |
| .planning/phases/03-msvc/03-CLANGCL-EVAL.md | SC-3 decision record | ✓ VERIFIED | Unchanged since prior full read |
| MSVC inplace .pyd set (13) + out-of-tree .lib set (13) | built artifacts | ✓ VERIFIED | Both on disk; .pyds post-date last code commit; llvm-nm parses all 13 .libs with PyInit exports |

### Key Link Verification

setup.py's relevant regions are byte-identical to the prior-verified state except the two comparator hunks (examined above); all previously-WIRED links re-confirmed by greps at HEAD plus the behavioral re-runs:

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| implib emission | symbol-gate probe | both derive from `get_ext_fullpath` dirname | ✓ WIRED | dirname sites ×2 (msvc/mingw arms); 13 .libs + llvm-nm PyInit probe re-run |
| import/pysam.c template | both generated twins | devtools/import.py `@pysam@` substitution | ✓ WIRED | sed regeneration diffs clean vs both twins (re-run) |
| vendor include dirs | MSVC module-graph include_dirs | msvc_include_extra | ✓ WIRED | unchanged; green build exercises it |
| win32/msvc include dir | MSVC branch only | never the mingw/POSIX graph | ✓ WIRED | gcc sentinel FORWARDER-OK; UCRT64 suite green |
| /DEF + HTSLIB_BUILDING_LIBRARY dllexport | 12 consumer extensions' links | internal libraries + dllimport arm | ✓ WIRED | greps ×3 each; 13 suite-green .pyds |
| htslib/config.h.msvc | htslib/config.h | deterministic per-run rewrite | ✓ WIRED | Re-proven behaviorally: MSVC run flipped UCRT64-state config.h to MSVC state (probe keys 4→0, HAVE_LIBBZ2 1) |
| comparator (Phase 5) | mirror enforcement at build time | non-MSVC win32 arm after run_make_print_config | ✓ WIRED | Wiring read in the else arm; standalone script verdict == build-time comparator (ast-extracted) |

### Data-Flow Trace (Level 4)

Build-system phase — no rendered runtime data. The analogous check re-run at HEAD: the module graph's source lists resolve to real files (52-entry mirror machine-checked == Makefile expansion; 13 extensions compile/link/import green; a hollow list would fail the link or the suite).

### Behavioral Spot-Checks

All commands run by the verifier at HEAD `6adf94e2` on 2026-10-13:

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| MSVC arm + config.h rewrite | `_venv-msvc/Scripts/python.exe setup.py --name` | exit 0; config.h → HAVE_LIBBZ2 1, 0 probe keys | ✓ PASS |
| Full MSVC suite | `_venv-msvc/Scripts/python.exe -m pytest -q` | `1034 passed, 15 skipped in 25.31s`, exit 0 | ✓ PASS |
| UCRT64 control (module graph) | UCRT64 `_venv/bin/python.exe setup.py --name` | exit 0 (real configure path) | ✓ PASS |
| Full UCRT64 suite | UCRT64 `_venv/bin/python.exe -m pytest -q` | `1034 passed, 15 skipped in 22.72s`, exit 0 | ✓ PASS |
| Mirror lockstep + teeth | UCRT64 `check_libhts_objs_lockstep.py --self-test` | lockstep OK (52==52); both teeth raise; exit 0 | ✓ PASS |
| Symbol gate (out-of-tree) | `llvm-nm -g -P build/.../pysam/*.lib` | 2504 rows on libchtslib; PyInit in 13/13 libs | ✓ PASS |
| UCRT64 forwarder sentinel | `gcc -fsyntax-only -I win32/msvc win32/msvc/shim_selftest.c` | FORWARDER-OK | ✓ PASS |
| Template lockstep | `sed 's/@pysam@/<tool>/g' import/pysam.c \| diff - <twin>` | clean vs both twins | ✓ PASS |
| Fork CI at current code state | API run 38380672667 | 25/25 success, head_sha 965760f1 (ancestor; only docs commits after) | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared by this phase. The phase's runnable evidence instruments are the build+suite+gate+sentinel+comparator commands above — all re-run by the verifier.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| BUILD-02 | 03-01..03-05 (all) | MSVC 构建系统 — 预生成 win32/config.h + 显式源码清单（Pillow/h5py 模式），产出官方级构建 | ✓ SATISFIED | Truths 1-11 re-verified at HEAD on both toolchains; REQUIREMENTS.md maps only BUILD-02 to Phase 3 — no orphaned requirements |

### Anti-Patterns Found

Unchanged from the prior pass (no new debt markers in the Phase-5 deltas — the comparator, sentinel, and teeth tests are all real implementations):

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| samtools/bam_reheader.c.pysam.c | 124 | `FIXME: error checking` | ℹ️ Info | Upstream samtools comment (2016); not phase-introduced |
| setup.py | ~1215 | `TODO Eventually by running configure here...` | ℹ️ Info | Pre-existing upstream comment in the autotools prebuild block |
| vendor/regex/tre-mem.c etc. | — | C4267/C4005 known-benign warnings | ℹ️ Info | Documented in vendor/README.md as not-to-chase |

No TBD/XXX markers. No stubs. No text-mode reads of binary/captured output (`_collect` opens "rb"). No msvcrt.dll imports (MSVC closure). Generated twins edited with their template in the same commit (sed proof re-run green).

### Human Verification Required

None — infrastructure/foundation phase; all acceptance criteria verified programmatically at HEAD (both toolchains' full suites independently re-run green by the verifier; gate, sentinel, lockstep, comparator-teeth, and CI verdict all re-exercised). No truth left PRESENT_BEHAVIOR_UNVERIFIED.

### Gaps Summary

None. All 11 merged must-have truths are re-verified against the current tree with fresh behavioral evidence. The STALE-REFRESH concern (Phase 5 touched covered sources) is discharged: every delta is additive/strengthening, the MSVC arm remains autotools-free, the 52-TU mirror is now machine-enforced with firing teeth, and both toolchains' suites are green at HEAD with identical counts (1034/15/0) — the +6 over the phase-time 1028 being Phase 5's additive oracle teeth tests. BUILD-02 remains satisfied. The disposition file was annotated at this refresh to record the code-verified closure of IN-01/IN-02 (open 9→7); IN-03..IN-09 remain recorded advisory backlog.

---

_Verified: 2026-10-13T10:55:30Z_
_Verifier: Claude (gsd-verifier)_
