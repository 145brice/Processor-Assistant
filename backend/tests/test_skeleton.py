"""Skeleton guarantees that must keep holding as tasks are built."""
import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend.pa_api import context
from backend.pa_api.main import app

client = TestClient(app)
SANDBOX = {"X-PA-Sandbox": "1"}
CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "nextjs-rebuild" / "API_CONTRACT.md"


def _contract_endpoints() -> set[tuple[str, str]]:
    rows = re.findall(r"^\| `(GET|POST|PUT|PATCH|DELETE) (/api/[^`]+)`", CONTRACT.read_text(encoding="utf-8"), re.M)
    return {(method, re.sub(r"\{[^}]+\}", "{}", path)) for method, path in rows}


def _app_endpoints() -> set[tuple[str, str]]:
    # Read the published OpenAPI schema: newer FastAPI wraps included routers, so app.routes
    # does not list their endpoints directly.
    out = set()
    for path, operations in app.openapi()["paths"].items():
        if path.startswith("/api"):
            for method in operations:
                out.add((method.upper(), re.sub(r"\{[^}]+\}", "{}", path)))
    return out


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_api_matches_contract_exactly():
    contract, built = _contract_endpoints(), _app_endpoints()
    assert contract, "could not read endpoints from API_CONTRACT.md"
    assert contract - built == set(), f"in contract but missing from API: {sorted(contract - built)}"
    assert built - contract == set(), f"in API but missing from contract: {sorted(built - contract)}"


def test_signed_out_request_is_401_in_contract_shape():
    response = client.get("/api/me")
    assert response.status_code == 401
    assert set(response.json()["error"]) == {"code", "message"}


def test_pipeline_list_returns_loans_and_counts():
    response = client.get("/api/loans", headers=SANDBOX)
    assert response.status_code == 200
    assert set(response.json()) == {"loans", "counts"}


def test_unbuilt_endpoint_names_its_task():
    response = client.post("/api/tools/team", headers=SANDBOX, json={})
    assert response.status_code == 501
    assert "T-33" in response.json()["error"]["message"]


def test_context_is_active_only_inside_a_request():
    assert context.current() is None
    ctx = context.RequestContext(user_key="u1", email="a@example.com", gemini_key="AIza-secret", sandbox=False)
    with context.use(ctx):
        assert context.current() is ctx
    assert context.current() is None


def test_context_never_prints_the_key_or_email():
    ctx = context.RequestContext(user_key="u1", email="a@example.com", gemini_key="AIza-secret", sandbox=False)
    assert "AIza-secret" not in repr(ctx) and "a@example.com" not in repr(ctx)
