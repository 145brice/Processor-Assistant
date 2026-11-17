"""Account-scoped parsed scan history using the existing Supabase settings table."""
import json
import urllib.parse


def parsed_batch(batch):
    excluded = {"raw_text", "bank_raw_text", "text", "pdf_bytes", "file_bytes", "document_bytes",
                "bytes", "prompt", "ai_log", "raw_response", "raw_document", "ocr_text"}

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if str(k).lower() not in excluded
                    and not isinstance(v, (bytes, bytearray, memoryview))}
        if isinstance(value, list):
            return [clean(v) for v in value if not isinstance(v, (bytes, bytearray, memoryview))]
        return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)

    return clean(batch)


def load(user_key):
    import supabase_auth as auth
    api_key = auth._service_key() or auth._public_key()
    if not user_key or not api_key or not auth._supabase_url():
        return {"ok": False, "items": [], "error": "Supabase scan history is unavailable."}
    params = urllib.parse.urlencode({"key": f"eq.scan_history:{user_key}", "select": "value_json"})
    response = auth._json_request("GET", f"{auth._supabase_url()}/rest/v1/settings?{params}",
                                  None, api_key=api_key, bearer=api_key)
    if not response.get("ok"):
        return {"ok": False, "items": [], "error": "Could not load saved scans. Please retry."}
    try:
        rows = response.get("data") or []
        value = rows[0].get("value_json") if rows else {}
        value = json.loads(value) if isinstance(value, str) else value
        items = (value or {}).get("items", [])
        if not isinstance(items, list):
            raise ValueError("Invalid history")
        return {"ok": True, "items": [i for i in items if i.get("user_key") == user_key]}
    except (ValueError, TypeError, AttributeError):
        return {"ok": False, "items": [], "error": "Could not read saved scans. Contact info@edgelandings.com."}


def save(user_key, items, user_email=""):
    import supabase_auth as auth
    if not user_key:
        return {"ok": False, "error": "Sign in to save scans."}
    scoped = [parsed_batch(i) for i in items if i.get("user_key") == user_key]
    return auth._save_setting_json(f"scan_history:{user_key}", {"items": scoped},
                                  user_key=user_key, user_email=user_email)
