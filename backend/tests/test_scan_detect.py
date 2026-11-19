"""POST /api/scan/detect (task T-20)."""
from fastapi.testclient import TestClient

from backend.pa_api import detection
from backend.pa_api.main import app
from backend.pa_api.routers import scanning
from backend.tests.fake_pdf import BLANK, FAKE_APPROVAL

client = TestClient(app)
SANDBOX = {"X-PA-Sandbox": "1"}


def _post(*files):
    return client.post(
        "/api/scan/detect",
        headers=SANDBOX,
        files=[("files", (name, data, "application/pdf")) for name, data in files],
    )


def test_detects_type_from_text():
    response = _post(("doc-001.pdf", FAKE_APPROVAL))
    assert response.status_code == 200
    (item,) = response.json()["files"]
    assert item["name"] == "doc-001.pdf"
    assert item["size_bytes"] == len(FAKE_APPROVAL)
    assert item["detected_type"] == "Approval Letter"
    assert item["confidence"] in {"High", "Medium"}


def test_unreadable_pdf_falls_back_to_filename_with_low_confidence():
    response = _post(("Fake_W2_2025.pdf", BLANK), ("scan-123.pdf", BLANK))
    assert response.status_code == 200
    first, second = response.json()["files"]
    assert (first["detected_type"], first["confidence"]) == ("W-2", "Low")
    assert (second["detected_type"], second["confidence"]) == ("Unknown", "Low")


def test_several_files_keep_their_order():
    response = _post(("b.pdf", BLANK), ("a.pdf", FAKE_APPROVAL), ("c.pdf", BLANK))
    assert [f["name"] for f in response.json()["files"]] == ["b.pdf", "a.pdf", "c.pdf"]


def test_types_outside_the_contract_become_unknown(monkeypatch):
    monkeypatch.setattr(detection.ai_engine, "detect_doc_type",
                        lambda _b: {"doc_type": "Closing Disclosure (CD)", "confidence": "High"})
    (item,) = _post(("cd.pdf", FAKE_APPROVAL)).json()["files"]
    assert item["detected_type"] == "Unknown"


def test_file_over_the_limit_is_413(monkeypatch):
    monkeypatch.setattr(scanning, "MAX_UPLOAD_BYTES", 100)
    response = _post(("big.pdf", FAKE_APPROVAL))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_non_pdf_is_400():
    response = client.post("/api/scan/detect", headers=SANDBOX,
                           files=[("files", ("notes.txt", b"just some text", "text/plain"))])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "not_a_pdf"


def test_signed_out_is_401():
    response = client.post("/api/scan/detect", files=[("files", ("a.pdf", FAKE_APPROVAL, "application/pdf"))])
    assert response.status_code == 401


def test_errors_never_echo_document_text(monkeypatch):
    monkeypatch.setattr(scanning, "MAX_UPLOAD_BYTES", 100)
    body = _post(("big.pdf", FAKE_APPROVAL)).text
    assert "Testy" not in body and "McFakerson" not in body
