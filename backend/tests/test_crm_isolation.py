"""Users of the API must never share crm's loan cache or load state.

The API serves requests on parallel threads in ONE process. crm keeps "which user's loans are
loaded" in streamlit's session_state, and outside Streamlit that is a single dictionary shared by
every user. This test hammers crm._load() from two users at once and checks nobody ever receives
the other's loans. It also checks the state accessors directly.
"""
import threading
import time

import pytest

import crm
from backend.pa_api import context


def ctx(user: str) -> context.RequestContext:
    return context.RequestContext(user, f"{user}@example.test", "", False)


@pytest.fixture
def two_users(monkeypatch, tmp_path):
    """Supabase returns each user their own loans, slowly enough for requests to overlap."""
    import supabase_sync

    def load(user_key=None):
        time.sleep(0.002)
        if not user_key:
            return {"ok": True, "loans": []}
        return {"ok": True, "loans": [{"id": 1, "loan_num": f"LOAN-{user_key}", "borrower": f"Borrower of {user_key}",
                                       "owner_user_key": user_key, "created_by_user_key": user_key}]}

    monkeypatch.setattr(supabase_sync, "load_pipeline_snapshot", load)
    monkeypatch.setattr(supabase_sync, "save_pipeline_snapshot", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(crm, "_PIPELINE_FILE", str(tmp_path / "pipeline.json"))   # never the real file
    crm._API_STATE.clear() if hasattr(crm, "_API_STATE") else None
    yield


def test_state_is_not_shared_between_users():
    with context.use(ctx("user-a")):
        crm._set_load_state(attempted=True, ok=True, loaded_user_key="user-a")
        crm._set_cached_loans([{"id": 1, "borrower": "A's borrower"}])
    with context.use(ctx("user-b")):
        assert crm._get_cached_loans() is None, "user B can see user A's cached loans"
        assert crm._get_load_state() == (False, False, None), "user B shares user A's load state"
    with context.use(ctx("user-a")):                         # and A still has its own
        assert crm._get_cached_loans() == [{"id": 1, "borrower": "A's borrower"}]


def test_sandbox_visitors_do_not_share_state_with_real_users():
    with context.use(ctx("user-a")):
        crm._set_cached_loans([{"id": 1, "borrower": "A's borrower"}])
    with context.use(context.SANDBOX):
        assert crm._get_cached_loans() is None


def test_outside_the_api_the_old_behaviour_is_unchanged():
    assert context.current() is None
    assert crm._api_bucket() is None if hasattr(crm, "_api_bucket") else True


def test_parallel_requests_never_get_each_others_loans(two_users):
    wrong: list[str] = []

    def worker(user: str, rounds: int):
        for _ in range(rounds):
            with context.use(ctx(user)):
                for loan in crm._load():
                    if loan.get("owner_user_key") != user:
                        wrong.append(f"{user} received {loan.get('loan_num')}")

    threads = [threading.Thread(target=worker, args=(user, 40)) for user in ("user-a", "user-b") * 4]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert wrong == [], f"cross-user leak: {wrong[:3]}"


# ---------- who the engine says is writing (supabase_sync, supabase_auth) ----------
def test_engine_writes_are_attributed_to_the_api_caller_not_a_blank_user(monkeypatch):
    """Rows written to Supabase while serving a request carry that caller's key and email.

    supabase_sync and supabase_auth used to read these from the Streamlit session, which is empty in
    the API, so activity rows had no owner and every pipeline snapshot save blanked user_email.
    """
    import supabase_auth
    import supabase_sync

    with context.use(context.RequestContext("user-a", "a@example.test", "", False)):
        assert supabase_sync._current_user_key() == "user-a"
        assert supabase_sync._current_user_email() == "a@example.test"
        assert supabase_auth._current_user_email() == "a@example.test"
    with context.use(context.SANDBOX):                      # the demo user is nobody
        assert supabase_sync._current_user_key() == "" and supabase_sync._current_user_email() == ""

    saved = {}

    class FakeTable:
        def upsert(self, payload):
            saved.update(payload)
            return self

        def execute(self):
            return None

    class FakeClient:
        def table(self, name):
            return FakeTable()

    monkeypatch.setattr(supabase_sync, "is_enabled", lambda: True)
    monkeypatch.setattr(supabase_sync, "_get_client", lambda: FakeClient())
    with context.use(context.RequestContext("user-a", "a@example.test", "", False)):
        out = supabase_sync.save_pipeline_snapshot([{"id": 1, "loan_num": "FAKE-1"}], user_key="user-a")
    assert out["ok"] is True
    assert saved["user_key"] == "user-a" and saved["user_email"] == "a@example.test"
