---
phase: "01"
slug: "01-mingw-w64"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-09-30"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| pacman repos -> dev machine | MSYS2 packages (toolchain, python, llvm-tools, libs) cross onto the machine via pacman | signed binary packages |
| git working tree -> build inputs | CRLF/encoding of vendored htslib/samtools/bcftools sources crosses into compilation | source bytes |
| build env vars -> configure invocation | HTSLIB_MODE / HTSLIB_CONFIGURE_OPTIONS flow into the pre-existing build pipeline | configuration strings |
| built .pyd binaries -> Python runtime | compiled extensions load into the interpreter (sibling DLL resolution) | native code |
| built artifacts -> distribution surface | point where a dev-validation build could wrongly become distributable | build outputs |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering | pacman package installs (bootstrap script) | high | mitigate | GPG-signed MSYS2 repos only; no PyPI binary installs on the build path (venv + pacman setuptools/Cython + --no-build-isolation); Package Legitimacy Audit in 01-RESEARCH.md approves all nine packages with zero [ASSUMED]/[SUS] verdicts | closed |
| T-01-02 | Tampering | vendored sources via CRLF checkout corruption | medium | mitigate | .gitattributes eol=lf rules + renormalization in Task 1 (01-01) restored byte fidelity; check-attr and ls-files --eol gates ran green | closed |
| T-01-03 | Tampering | toolchain binary substitution on PATH | low | mitigate | bootstrap verifies llvm-nm presence/version after install; UCRT64 MSYSTEM gate anchors the expected environment (observed firing live: exit 1 with full 9-package message, 2026-09-30) | closed |
| T-01-04 | Tampering/Elevation | HTSLIB_CONFIGURE_OPTIONS into the pre-existing shell=True configure string | medium | accept | pre-existing dev-only surface (setup.py:61-73); plan 02 added no new shell=True call sites; bootstrap sets the var to the constant --disable-libcurl, narrowing what flows through it | closed |
| T-01-05 | Tampering/Elevation | shell=True configure string (setup.py:61-73) | medium | accept | pre-existing dev-only surface; zero new shell=True call sites; whole build gated behind the UCRT64 check; injection concern owned by project security review tooling | closed |
| T-01-06 | Tampering | symbol gate silently skipped on Windows | high | mitigate | BUILD-03 fail-hard dispatch: win32 calls the check outside the exception-swallowing wrapper (verified first-hand 2026-09-30); vacuous-pass guard raises on empty symbol set; bootstrap log shows 0 skip warnings; probe teeth=904 honesty=0 | closed |
| T-01-07 | Tampering | linker input substitution via library_dirs | low | mitigate | implib lands in the repo-local pysam/ directory that library_dirs pins (verified 2026-09-30); no system-wide or PATH-dependent library search introduced | closed |
| T-01-08 | Tampering | pacman package installs during provisioning | high | mitigate | same controls as T-01-01: GPG-signed repos, --no-build-isolation, zero flagged Package Legitimacy Audit verdicts | closed |
| T-01-09 | Information Disclosure / Tampering | built .pyd loading at import time | medium | mitigate | sibling resolution via standard CPython DLL search of the extension's own directory (A4); smoke gate empirically proves the loaded set is the just-built one (import pysam -> 0.24.1 builtin, re-run 2026-09-30); no PATH-based DLL dependency | closed |
| T-01-10 | Information Disclosure / Tampering | accidental distribution of dev-validation artifacts | medium | mitigate | no wheel/sdist target invoked; verify commands assert import/smoke/gate outcomes only; re-verified 2026-09-30 during UAT: 0 *.whl, 0 *.tar.gz, no dist/, nothing tracked in git | closed |
| T-01-SC | Tampering | npm/pip/cargo installs | high | mitigate | none occur in this phase (pacman GPG-signed packages only; venv uses pacman setuptools/Cython via --no-build-isolation) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-04, T-01-05 | Pre-existing upstream shell=True configure surface, dev-only, unchanged blast radius this phase; flow-through value narrowed to a constant by the documented bootstrap flow | Plan-time threat model (01-01/01-02), ratified in UAT 2026-09-30 | 2026-09-30 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-30 | 11 | 11 | 0 | gsd-secure-phase (orchestrator, L1 — short-circuit: threats_open 0, register_authored_at_plan_time true, asvs 1); mitigation evidence cross-checked first-hand during the same session's UAT (T-01-03/06/07/09/10 re-verified by direct command) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-30
