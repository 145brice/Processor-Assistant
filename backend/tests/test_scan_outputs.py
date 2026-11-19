"""POST /api/outputs/* (task T-22): drafts, CSV and PDF built locally from a scan result."""
import fitz
from fastapi.testclient import TestClient

from backend.pa_api.main import app

client = TestClient(app)
SANDBOX = {"X-PA-Sandbox": "1"}

BATCH = {
    "file": "Fake_Approval.pdf",
    "type": "Approval Letter",
    "result": {
        "success": True, "doc_type": "Approval Letter",
        "conditions": [
            {"num": 1, "desc": "Provide two months of bank statements", "party": "Borrower", "status": "Needed"},
            {"num": 2, "desc": "Title commitment", "party": "Title", "status": "Requested"},
            {"num": 3, "desc": "Final VOE", "party": "Employer", "status": "Cleared"},
        ],
        "extracted_data": {"loan_amount": "$100,000", "formula": "=1+1"},
        "contacts": {"borrower": {"name": "Testy McFakerson"}},
        "risks": "", "image_only": False, "ai_used": False, "ai_note": "Local extraction", "error": "",
    },
    "loan_match": {"loan_id": None, "loan_num": "FAKE-123", "borrower": "", "confidence": 0, "suggestion": "unknown"},
}


def test_email_drafts_split_subject_and_list_only_open_borrower_items():
    response = client.post("/api/outputs/email-drafts", headers=SANDBOX, json={"batch": BATCH})
    assert response.status_code == 200, response.text
    drafts = response.json()
    needs = drafts["borrower_needs_list"]
    assert needs["subject"] == "Documents needed for your loan FAKE-123"
    assert "Hi Testy McFakerson" in needs["body"] and "bank statements" in needs["body"]
    assert "Title commitment" not in needs["body"]            # not the borrower's item
    update = drafts["loan_officer_update"]
    assert update["subject"].startswith("Loan FAKE-123")
    assert "Title commitment" in update["body"] and "Final VOE" not in update["body"]  # cleared is omitted
    assert not needs["body"].lower().startswith("subject:")


def test_csv_download_escapes_formulas():
    response = client.post("/api/outputs/csv", headers=SANDBOX, json={"batch": BATCH})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="loan-scan.csv"' in response.headers["content-disposition"]
    text = response.content.decode("utf-8-sig")
    assert "Field,Value" in text and "'=1+1" in text           # spreadsheet formula injection blocked


def test_pdf_download_opens_and_contains_the_conditions():
    response = client.post("/api/outputs/pdf", headers=SANDBOX, json={"batch": BATCH})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    with fitz.open(stream=response.content, filetype="pdf") as doc:
        text = "".join(page.get_text() for page in doc)
    assert "Provide two months of bank statements" in text


def test_outputs_require_sign_in():
    assert client.post("/api/outputs/csv", json={"batch": BATCH}).status_code == 401
