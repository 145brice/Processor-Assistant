"""Check a deployed pa-api and pa-web (task T-40). Uses only invented sample data.

    python scripts/check_deployment.py https://<pa-api-url> https://<pa-web-url>

Exits 0 when every check passes, 1 otherwise. Run it after each deploy, and again after the domain
switch with the real domain for both arguments' web side.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.tests.fake_pdf import FAKE_APPROVAL  # noqa: E402  (an invented approval letter)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # report the redirect instead of following it
        return None


OPENER = urllib.request.build_opener(_NoRedirect)


def call(url, *, method="GET", headers=None, body=None):
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with OPENER.open(request, timeout=60) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def multipart(fields: dict[str, str], file_field: str, filename: str, data: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
                 f'Content-Type: application/pdf\r\n\r\n'.encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    api, web = (u.rstrip("/") for u in sys.argv[1:3])
    sandbox = {"X-PA-Sandbox": "1"}
    results: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # ---------- API ----------
    status, _, body = call(f"{api}/api/health")
    check("API health", status == 200 and json.loads(body or b"{}").get("ok") is True, f"HTTP {status}")

    status, _, body = call(f"{api}/api/me")
    shape = set(json.loads(body or b"{}").get("error", {})) if status == 401 else set()
    check("Signed-out request is refused (401, contract error shape)", status == 401 and shape == {"code", "message"}, f"HTTP {status}")

    status, _, body = call(f"{api}/api/loans", headers=sandbox)
    loans = json.loads(body or b"{}").get("loans", []) if status == 200 else []
    check("Sandbox sees the demo loans", status == 200 and len(loans) > 0, f"HTTP {status}, {len(loans)} loans")

    status, _, _ = call(f"{api}/api/loans", method="POST", headers={**sandbox, "Content-Type": "application/json"},
                        body=json.dumps({"loan_num": "FAKE-1", "borrower": "Testy McFakerson", "status": "Pending"}).encode())
    check("Sandbox cannot save changes (403)", status == 403, f"HTTP {status}")

    payload, content_type = multipart({"doc_type": "Approval Letter"}, "file", "Fake_Approval.pdf", FAKE_APPROVAL)
    status, _, body = call(f"{api}/api/scan", method="POST", headers={**sandbox, "Content-Type": content_type}, body=payload)
    scan = json.loads(body or b"{}") if status == 200 else {}
    result = scan.get("result", {})
    check("Sandbox scan of an invented approval letter works, with no AI", status == 200 and result.get("success") is True
          and result.get("ai_used") is False and len(result.get("conditions", [])) > 0, f"HTTP {status}")

    status, _, body = call(f"{api}/api/tools/spanish_reply", method="POST", headers={**sandbox, "Content-Type": "application/json"},
                           body=json.dumps({"input": {"action": "templates", "conditions": "1. Bank statements"}}).encode())
    check("More Tools are available", status == 200, f"HTTP {status}")

    status, headers, _ = call(f"{api}/api/health", headers={"Origin": web})
    check("API accepts the web app's address (CORS)", headers.get("access-control-allow-origin") == web, f"allowed: {headers.get('access-control-allow-origin')!r}")
    status, headers, _ = call(f"{api}/api/health", headers={"Origin": "https://evil.example"})
    check("API refuses other websites (CORS)", "access-control-allow-origin" not in {k.lower() for k in headers}, "")

    # ---------- web ----------
    status, _, _ = call(f"{web}/login")
    check("Web: login page loads", status == 200, f"HTTP {status}")
    status, headers, _ = call(f"{web}/scanner")
    check("Web: signed-out visitors are sent to login", status in (302, 307, 308) and "/login" in headers.get("Location", headers.get("location", "")), f"HTTP {status}")
    status, _, _ = call(f"{web}/scanner", headers={"Cookie": "pa_sandbox=1"})
    check("Web: the sample-loan visitor reaches the scanner", status == 200, f"HTTP {status}")
    status, _, _ = call(f"{web}/privacy")
    check("Web: privacy policy is public", status == 200, f"HTTP {status}")

    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
