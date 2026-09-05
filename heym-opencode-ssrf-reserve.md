# Heym — OpenCode SSRF Findings (Reserve)

**Status:** Confirmed finding; deliberately kept in reserve for later investigation/reporting  
**Repository:** `heymrun/heym`  
**Affected version checked:** `0.0.105` / `main` at commit `34a76d8`  
**Audit date:** 2026-09-06  
**Finding:** SSRF in OpenCode model discovery via attacker-controlled `base_url`  
**Current decision:** Do not report yet. Keep as reserve while auditing other trust boundaries for a stronger issue.

---

## 1. Executive Summary

Heym's OpenCode model discovery endpoint accepts a user-controlled `base_url` and passes it to a backend HTTP client without an SSRF guard.

The request path is:

```text
Authenticated user
    -> GET /api/opencode-go/models?base_url=<attacker URL>
    -> fetch_opencode_models(base_url=...)
    -> _get_json(f"{base_url}/models")
    -> httpx.AsyncClient().get(...)
```

Because the backend makes the outbound request, an authenticated user can cause the server to connect to an attacker-selected internal or private network destination.

A local proof of concept confirmed that the Heym backend made an HTTP request to a loopback listener at:

```text
127.0.0.1:19001
```

This is a real SSRF primitive.

---

## 2. Affected Code

### Endpoint

File:

```text
backend/app/api/opencode_go.py
```

Relevant code:

```python
@router.get("/models")
async def list_opencode_models(
    base_url: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> dict:
    models, source = await fetch_opencode_models(base_url=base_url)
    return {"models": models, "source": source}
```

Important points:

- The endpoint is authenticated, but does not require an admin role.
- `base_url` comes directly from the request.
- The endpoint passes it to `fetch_opencode_models()`.

### HTTP client

File:

```text
backend/app/services/opencode_models.py
```

Relevant code:

```python
async def _get_json(url: str) -> object:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

async def fetch_opencode_models(*, base_url: str | None = None):
    base = (base_url or OPENCODE_ZEN_BASE_URL).rstrip("/")
    cached = _CACHE.get(base)
    if cached and (time.time() - cached[0]) < _TTL_SECONDS:
        return cached[1], "live"
    try:
        payload = await _get_json(f"{base}/models")
        ...
```

The important security property is that the user-controlled `base_url` reaches the raw HTTP client without a visible SSRF validation step.

---

## 3. Trust Boundary

Attacker requirements:

- A normal authenticated Heym account.
- Ability to call the OpenCode model-discovery endpoint.

The attacker does **not** need:

- server shell access,
- filesystem access,
- administrator privileges,
- control of the target machine.

The vulnerable server performs the outbound HTTP request on the attacker's behalf.

---

## 4. Proof of Concept

### Setup

A local HTTP server was started on:

```text
127.0.0.1:19001
```

The PoC supplied a loopback URL as `base_url`.

Expected vulnerable behavior:

```text
GET /api/opencode-go/models?base_url=http://127.0.0.1:19001
```

The Heym backend then attempted:

```text
GET http://127.0.0.1:19001/models
```

The local listener observed the inbound request.

This confirms that the backend can be induced to connect to a loopback address selected by the caller.

### Why this matters

The vulnerability is not dependent on successful parsing of attacker-controlled JSON. The security-relevant fact is that the backend performed the network connection to an attacker-selected address.

A production-safe confirmation should use an HTTP listener the tester controls rather than probing unrelated third-party infrastructure.

---

## 5. Potential SSRF Targets

The primitive may allow requests toward destinations reachable from the Heym server, subject to the deployment's network controls.

Candidate classes to investigate safely:

### Loopback

```text
127.0.0.1
::1
localhost
```

### RFC1918 private networks

```text
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

### Link-local / cloud metadata

Examples include provider-specific metadata addresses such as:

```text
169.254.169.254
```

Do not access real cloud metadata services unless explicitly authorized and necessary for a controlled test.

### IPv6 and alternate address representations

Investigate whether URL parsing and SSRF defenses correctly handle:

- IPv6 loopback
- IPv4-mapped IPv6
- unusual but valid IP representations
- DNS names resolving to private addresses
- redirects, where applicable

These are follow-up research vectors, not all proven by the current PoC.

---

## 6. Existing SSRF Defenses in Heym

The codebase contains SSRF protection in other request paths, including guarded HTTP clients / URL guards used by recently hardened integrations.

The key observation for this finding is that the OpenCode model-discovery path does not visibly use the same protection.

Recent security-hardening work on `main` also did not remove this OpenCode path's raw HTTP request.

This makes the issue look like a security-boundary inconsistency rather than an intentional unrestricted egress feature.

---

## 7. Potential Impact

Confirmed impact:

- Server-side HTTP request to attacker-selected destination.
- Access to network locations reachable from the Heym backend.
- Potential interaction with internal HTTP services that are not directly reachable by the attacker.

Potential additional impact depends on deployment/network topology:

- internal service enumeration,
- access to internal administrative APIs,
- cloud metadata access,
- interactions with services that trust requests originating from the internal network.

The current evidence **does not by itself prove credential theft or arbitrary code execution**.

Impact should therefore be described according to what can be demonstrated in a controlled environment.

---

## 8. Why This Finding Is Currently Reserved

This is a valid security bug, but it is intentionally not being treated as the final / strongest finding yet.

Reasons:

1. Heym already has recent SSRF-related security history.
2. The accepted credential-exfiltration SSRF advisory is potentially more impactful because it involved a credential-backed request path.
3. The OpenCode model-discovery path currently demonstrates SSRF, but the exact reachable targets and practical impact need not be larger than the previously reported issue.
4. A stronger issue may exist in another trust boundary, especially authorization / identity / execution-state handling.

Therefore:

> **Do not report this immediately. Preserve it as a confirmed reserve finding while continuing the audit in another direction.**

---

## 9. Stronger Variant Worth Investigating Later

There is a second OpenCode-related path that may deserve deeper analysis:

```text
backend/app/services/opencode_usage_service.py
```

Relevant behavior observed during audit:

```python
async def fetch_opencode_usage(*, credential_id, api_key, base_url=""):
    ...
    result = await _probe(api_key, base_url)
```

and:

```python
async def _probe(api_key, base_url):
    headers = merge_outbound_headers({
        "Authorization": f"Bearer {api_key}",
        ...
    })
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(usage_url(base_url), headers=headers)
```

This path appears more security-sensitive because:

- `base_url` can be credential-controlled.
- The request includes an Authorization bearer token derived from the credential.
- A raw HTTP client is used.
- The exact authorization/shareability/call path still needs to be established before claiming exploitability.

### Important: do not assume this is a second confirmed vulnerability.

Questions that must be answered later:

1. Who can configure or modify an OpenCode credential?
2. Can team/shared users trigger usage reporting for another user's credential?
3. Is `base_url` owner-controlled, collaborator-controlled, or globally trusted?
4. Who can cause `fetch_opencode_usage()` to execute?
5. Can an attacker make the backend send a shared credential's API key to an attacker-controlled server?
6. Are there SSRF guards elsewhere in the complete call path?
7. Does redirect handling introduce any additional credential exposure?
8. What exact endpoint / UI action causes the usage probe?
9. Does credential ownership or team sharing prevent a lower-privileged user from reaching the vulnerable path?

This variant could potentially be stronger than the model-discovery SSRF, but it is **unproven** until the full trust and call paths are established.

---

## 10. Likely Remediation

For the model-discovery endpoint, the preferred fix is to apply the same SSRF protection used elsewhere in Heym.

Conceptually:

```python
safe_base = guard_http_url(
    base_url,
    subject="OpenCode base_url",
)
```

or route the request through an existing guarded HTTP client.

The exact implementation should follow the repository's established SSRF-defense abstraction rather than introducing a one-off URL parser.

### Remediation requirements

A robust fix should account for:

- loopback
- private address ranges
- link-local addresses
- IPv6 equivalents
- DNS resolution to private addresses
- redirect behavior
- normalization / alternate IP representations
- clear allowlisting if arbitrary custom OpenCode-compatible servers are intended

If custom OpenCode endpoints are a supported feature, the security policy should explicitly define what destinations are allowed rather than simply disabling the check.

---

## 11. Suggested Security Report Skeleton

When this is eventually reported, use a structure like:

### Title

```text
SSRF in OpenCode model discovery via user-controlled base_url
```

### Severity

Start with the confirmed technical impact and calculate CVSS after establishing the practical reachable target set.

Do not inflate severity solely because metadata/private ranges are theoretically reachable.

### Affected versions

Currently observed on:

```text
v0.0.105
commit 34a76d8
```

Confirm exact fixed/affected ranges immediately before reporting.

### Description

Authenticated users can supply an arbitrary OpenCode `base_url`. The backend constructs `<base_url>/models` and performs a raw outbound HTTP request without the repository's SSRF guard.

### Reproduction

Use a controlled HTTP listener and show that the Heym backend connects to:

```text
http://127.0.0.1:19001/models
```

### Impact

Describe the proven ability to reach attacker-selected server-side network destinations and any additional controlled impact demonstrated during validation.

### Remediation

Use Heym's existing SSRF URL validation / guarded HTTP client for the OpenCode `base_url` path.

---

## 12. Evidence / References

Primary source files:

```text
backend/app/api/opencode_go.py
backend/app/services/opencode_models.py
backend/app/services/opencode_usage_service.py
backend/app/services/opencode_catalog.py
```

Repository state audited:

```text
main: 34a76d8
release: v0.0.105
```

Related security context:

- Heym has existing SSRF hardening in other credential-backed integration paths.
- The OpenCode model-discovery path was not covered by the same visible SSRF protection at the time of the audit.

---

## 13. Current Status Checklist

- [x] Vulnerable code path identified
- [x] Authenticated attack surface identified
- [x] Missing SSRF guard identified
- [x] Local loopback PoC reproduced
- [x] Server-side outbound request confirmed
- [ ] Internal/private target impact fully mapped
- [ ] OpenCode usage-path variant fully audited
- [ ] Credential-sharing exploitability established
- [ ] Exact CVSS determined
- [ ] Final affected-version range confirmed
- [ ] Patch prepared
- [ ] Security advisory submitted

---

## 14. Important Handling Note

This document records a **confirmed security finding for future use**.

Do not perform destructive testing, credential extraction, metadata harvesting, internal service access, or testing against infrastructure that is not owned/authorized.

For further validation, prefer:

- localhost services on your own test machine,
- purpose-built internal test listeners,
- harmless requests,
- self-hosted Heym instances,
- controlled credentials.

The goal of the next audit phase is to determine whether Heym contains a stronger authorization / identity / execution-state vulnerability before this SSRF is reported.
