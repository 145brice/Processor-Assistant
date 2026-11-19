import asyncio
import json

import crm
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from backend.pa_api import context
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans


@pytest.fixture
def temporary_pipeline(tmp_path, monkeypatch):
    pipeline = tmp_path / "pipeline.json"
    removed = tmp_path / "removed"
    monkeypatch.setattr(crm, "_PIPELINE_FILE", str(pipeline))
    monkeypatch.setattr(crm, "_REMOVED_DIR", str(removed))
    monkeypatch.setattr(crm, "_REMOVED_CFG", str(tmp_path / "removed_config.json"))
    monkeypatch.setattr(crm, "_get_load_state", lambda: (False, False, ""))
    monkeypatch.setattr(crm, "_set_load_state", lambda **kwargs: None)
    monkeypatch.setattr(crm, "_set_cached_loans", lambda loans: None)
    return pipeline


def ctx(user: str, sandbox: bool = False):
    return context.RequestContext(user, f"{user}@example.test", "", sandbox)


def run(request_context, function, *args):
    with context.use(request_context):
        return function(*args, ctx=request_context)


def test_user_lifecycle_and_visibility(temporary_pipeline):
    user_a, user_b = ctx("user-a"), ctx("user-b")
    created = run(user_a, loans.create_loan, loans.m.LoanCreate(loan_num="FAKE-1", borrower="Avery Example", status="Pending"))
    assert [item.id for item in run(user_a, loans.list_loans).loans] == [created.id]
    assert run(user_b, loans.list_loans).loans == []
    changed = run(user_a, loans.set_status, created.id, loans.m.StatusIn(status="Requested"))
    assert changed.status == "Requested"
    with pytest.raises(ApiError) as denied:
        run(user_b, loans.set_status, created.id, loans.m.StatusIn(status="Cleared"))
    assert denied.value.status == 404
    run(user_a, loans.delete_loan, created.id)
    assert run(user_a, loans.list_loans).loans == []
    with pytest.raises(ApiError):
        run(user_b, loans.restore_loan, created.id)
    restored = run(user_a, loans.restore_loan, created.id)
    assert restored.id == created.id


def test_csv_import_stamps_importing_user(temporary_pipeline):
    upload = UploadFile(filename="loans.csv", file=__import__("io").BytesIO(b"loan_num,borrower,status\nFAKE-2,Blair Example,Pending\n"), headers=Headers())
    importer = ctx("importer")
    with context.use(importer):
        result = asyncio.run(loans.import_loans(upload, importer))
    assert result.imported == 1
    assert crm.get_all_loans()[0]["created_by_user_key"] == "importer"


def test_every_sandbox_write_is_rejected(temporary_pipeline):
    sandbox = ctx("", True)
    body = loans.m.LoanCreate(loan_num="FAKE-3", borrower="Casey Example", status="Pending")
    operations = [
        lambda: run(sandbox, loans.create_loan, body),
        lambda: run(sandbox, lambda upload, ctx: asyncio.run(loans.import_loans(upload, ctx)), UploadFile(filename="x.csv", file=__import__("io").BytesIO(b"loan_num,borrower\nFAKE-4,Drew Example\n"), headers=Headers())),
        lambda: run(sandbox, loans.delete_loan, 1),
        lambda: run(sandbox, loans.set_status, 1, loans.m.StatusIn(status="Cleared")),
        lambda: run(sandbox, loans.restore_loan, 1),
    ]
    for operation in operations:
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.status == 403
