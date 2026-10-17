# Security Audit — AI-Generated Photo Portfolio

**Assessment state:** Baseline application built and source reviewed; manual tests described by the developer; fixes planned for a future sprint.

**Scope:** Only an application owned/controlled by the developer; not a third-party penetration test. Code locations refer to the unpatched ZIP snapshot reviewed October 17, 2026.

## Evidence standards
- **Code-confirmed:** Observable in the baseline source.
- **Author-reported PoC:** Test described by the developer; the test artifact is not present in the supplied ZIP.
- **Not demonstrated:** An exploit outcome has not been verified.

The archived SQLite database had six ordinary photo records and one admin row storing a bcrypt hash. **No injected `<script>` record** was found in that snapshot. The archive included six JPEG uploads but not the disguised non-image test file. Three UI screenshots demonstrate the app screens, not the execution of an exploit. Keep the database out of public GitHub.

## SEC-001 — Predictable development JWT signing secret
**Status:** Code-confirmed; exploit not demonstrated.

`auth.py:13` uses a fallback JWT signing secret (`dev-secret-change-me`) if an environment variable is absent. Default development credentials/configuration also warrant review. Using known secrets in a deployed environment risks authentication compromise.

**Planned remediation:** Require a strong environment-provided secret at startup, rotate development secrets, and verify token validation against invalid signatures.

## SEC-002a — Raw EXIF metadata storage and second-order XSS risk
**Status:** Code-confirmed unsafe data handling; injection/database observation author-reported; browser XSS execution **not established**.

`routers/admin.py:37–54` extracts camera Make/Model values; `routers/admin.py:145–154` persists them without sanitization. `models.py:20–21` defines the corresponding fields.

**Author-reported PoC:** Injected a `<script>` string into the EXIF metadata of a valid JPEG using ExifTool and observed the unsanitized value in SQLite. The archived database does not retain the injected row.

**Critical limitation:** The application's Jinja2 HTML templates auto-escape displayed metadata, so an injected string being stored **does not prove browser-executed stored XSS**. This is an untrusted-data storage/defense-in-depth issue with possible second-order XSS if future output paths fail to encode it.

**Planned remediation:** Use `html.escape()` on metadata values before persistence as requested, retain context-aware Jinja2 escaping, and test for double-encoding and unsafe output sinks.

## SEC-002b — Extension-only file upload validation
**Status:** Code-confirmed; author-reported bypass.

`routers/admin.py:133–143` decides upload eligibility using the filename extension, then writes the file; Pillow parsing errors do not cause rejection. The developer reports successfully uploading non-image text under a `.jpg` filename. The test file is not in the provided ZIP.

**Planned remediation:** Use `PIL.Image.verify()` plus decoded format allowlisting and size controls. Return HTTP 415 and clean up temporary files for invalid content. Confirm absence of both on-disk artifacts and database records after a rejected upload.

## SEC-003 — CSRF protections on authenticated forms
**Status:** Source review concern; cross-site exploit not demonstrated.

`routers/admin.py:78–84` configures JWT cookies with SameSite=Lax; authenticated state-changing routes at `routers/admin.py:125–131,158–163` and related forms do not show explicit CSRF tokens. SameSite mitigates many cross-site cases, so exploitability requires additional testing.

**Planned remediation:** Assess the CSRF threat model and add explicit CSRF tokens and/or suitable Origin checking as needed.

## SEC-004 — Unbounded upload stream
**Status:** Code-confirmed absence of application-level stream-size enforcement; DoS not demonstrated.

`routers/admin.py:140–143` copies upload content without explicit byte limits in application code.

**Planned remediation:** Enforce request size, pixel limits, timeouts and file handling cleanup, then safely test oversized content in isolation.

## SEC-005 — Container defaults to root
**Status:** Dockerfile lacks a `USER` directive; runtime not tested.

The current `Dockerfile` does not select an unprivileged runtime identity.

**Planned remediation:** Create `appuser`, change ownership of required writable paths, set `USER appuser`, and verify file permissions under the rebuilt image.

## Planned regression testing
1. Retry the disguised `.jpg` upload; expect HTTP 415, no saved file, and no database row.
2. Retry EXIF injection; document stored values and correctly encoded browser output.
3. Verify missing/weak JWT secret handling fails safely.
4. Check app runs as non-root and can still write needed files.
5. Assess CSRF and upload-limit protections.

## Reporting limitations
There is no preserved exploit screenshot, injected database row, or malicious upload payload in the supplied ZIP. No remediation patches are present in the reviewed snapshot. This report intentionally does not claim production exploitation, confirmed JavaScript execution, or completed defensive fixes.
