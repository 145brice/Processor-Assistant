import crm
import cloud_client
from backend.pa_api import context


def test_api_context_key_does_not_fall_back_to_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-server-key")
    with context.use(context.RequestContext("user-123", "fake@example.test", "", False)):
        config = cloud_client.get_config()
        enabled = cloud_client.is_enabled()

    assert config["api_key"] == ""
    assert enabled is False


def test_api_context_key_is_used():
    with context.use(context.RequestContext("user-123", "fake@example.test", "AIza-user", False)):
        config = cloud_client.get_config()

    assert config["api_key"] == "AIza-user"


def test_crm_uses_api_context_identity_and_sandbox():
    with context.use(context.RequestContext("user-123", "fake@example.test", "", False)):
        assert crm._current_user_key() == "user-123"
        assert crm._is_sandbox() is False

    with context.use(context.SANDBOX):
        assert crm._current_user_key() == ""
        assert crm._is_sandbox() is True


def test_crm_falls_back_to_streamlit_outside_api_context():
    assert context.current() is None
    assert crm._current_user_key() == ""

