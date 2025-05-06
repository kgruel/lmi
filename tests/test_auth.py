import time
import pytest

from lmi import auth


def make_fake_token(expires_in=60):
    now = int(time.time())
    return {
        "access_token": "fake-token",
        "expires_in": expires_in,
        "issued_at": now,
        "expires_at": now + expires_in,
    }

def test_token_cache(tmp_path, monkeypatch):
    env_name = "testenv"
    cache_dir = tmp_path / "tokens"
    monkeypatch.setattr(auth, "TOKEN_CACHE_DIR", cache_dir)
    token = make_fake_token(60)
    auth.save_token(env_name, token)
    loaded = auth.load_cached_token(env_name)
    assert loaded["access_token"] == "fake-token"
    # Expired token
    expired = make_fake_token(-10)
    auth.save_token(env_name, expired)
    assert auth.load_cached_token(env_name) is None

def test_is_token_expired():
    token = make_fake_token(1)
    assert not auth.is_token_expired(token)
    token["expires_at"] = int(time.time()) - 1
    assert auth.is_token_expired(token)

def test_is_token_expired_fallback():
    # No expires_at, fallback to issued_at + expires_in
    now = int(time.time())
    token = {"issued_at": now, "expires_in": 1}
    assert not auth.is_token_expired(token)
    token["issued_at"] = now - 10
    token["expires_in"] = 1
    assert auth.is_token_expired(token)

def test_is_token_expired_fallback_no_issued_at():
    # No expires_at, no issued_at, no expires_in
    token = {}
    # Should fallback to 0+0, so always expired
    assert auth.is_token_expired(token)

def test_acquire_token_client_credentials(monkeypatch):
    config = {
        "OAUTH_CLIENT_ID": "id",
        "OAUTH_CLIENT_SECRET": "secret",
        "OAUTH_TOKEN_URL": "https://example.com/token",
    }
    fake_response = {
        "access_token": "abc123",
        "expires_in": 60,
    }
    class FakeClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, url, data):
            assert url == config["OAUTH_TOKEN_URL"]
            assert data["client_id"] == config["OAUTH_CLIENT_ID"]
            return type("Resp", (), {"raise_for_status": lambda s: None, "json": lambda s: fake_response})()
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": FakeClient}))
    token = auth.acquire_token(config, grant_type="client_credentials")
    assert token["access_token"] == "abc123"
    assert "expires_at" in token

def test_acquire_token_invalid_grant(monkeypatch):
    config = {"OAUTH_CLIENT_ID": "id", "OAUTH_CLIENT_SECRET": "secret", "OAUTH_TOKEN_URL": "url"}
    with pytest.raises(ValueError):
        auth.acquire_token(config, grant_type="invalid")

def test_authenticated_client_refresh(monkeypatch):
    config = {
        "OAUTH_CLIENT_ID": "id",
        "OAUTH_CLIENT_SECRET": "secret",
        "OAUTH_TOKEN_URL": "https://example.com/token",
    }
    env_name = "testenv"
    tokens = [
        {"access_token": "expired", "expires_in": 1, "issued_at": int(time.time()) - 10, "expires_at": int(time.time()) - 1},
        {"access_token": "fresh", "expires_in": 60, "issued_at": int(time.time()), "expires_at": int(time.time()) + 60},
    ]
    calls = {"post": 0, "request": 0}
    class FakeClient:
        def __init__(self, *a, **k): self.headers = {}
        def request(self, method, url, **kwargs):
            calls["request"] += 1
            if calls["request"] == 1:
                return type("Resp", (), {"status_code": 401})()
            return type("Resp", (), {"status_code": 200})()
        def close(self): pass
    def fake_get_token(config, env_name):
        return tokens.pop() if tokens else make_fake_token(60)
    def fake_acquire_token(config, grant_type):
        return make_fake_token(60)
    monkeypatch.setattr(auth, "get_token", fake_get_token)
    monkeypatch.setattr(auth, "acquire_token", fake_acquire_token)
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": lambda *a, **k: FakeClient()}))
    client = auth.AuthenticatedClient(config, env_name)
    resp = client.request("GET", "https://api.example.com/resource")
    assert calls["request"] == 2
    client.close()

def test_authenticated_client_get_post(monkeypatch):
    config = {"OAUTH_CLIENT_ID": "id", "OAUTH_CLIENT_SECRET": "secret", "OAUTH_TOKEN_URL": "url"}
    env_name = "testenv"
    class FakeClient:
        def __init__(self, *a, **k): self.headers = {}
        def request(self, method, url, **kwargs):
            return type("Resp", (), {"status_code": 200})()
        def close(self): pass
    monkeypatch.setattr(auth, "get_token", lambda *a, **k: make_fake_token(60))
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": lambda *a, **k: FakeClient()}))
    client = auth.AuthenticatedClient(config, env_name)
    resp = client.get("http://foo")
    assert resp.status_code == 200
    resp = client.post("http://foo")
    assert resp.status_code == 200
    client.close()

def test_acquire_token_no_expires_in(monkeypatch):
    config = {
        "OAUTH_CLIENT_ID": "id",
        "OAUTH_CLIENT_SECRET": "secret",
        "OAUTH_TOKEN_URL": "https://example.com/token",
    }
    fake_response = {
        "access_token": "abc123",
        # no expires_in
    }
    class FakeClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, url, data):
            return type("Resp", (), {"raise_for_status": lambda s: None, "json": lambda s: fake_response})()
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": FakeClient}))
    token = auth.acquire_token(config, grant_type="client_credentials")
    assert token["access_token"] == "abc123"
    assert "issued_at" in token


def test_authenticated_client_401_empty_token(monkeypatch):
    config = {"OAUTH_CLIENT_ID": "id", "OAUTH_CLIENT_SECRET": "secret", "OAUTH_TOKEN_URL": "url"}
    env_name = "testenv"
    calls = {"request": 0}
    class FakeClient:
        def __init__(self, *a, **k): self.headers = {}
        def request(self, method, url, **kwargs):
            calls["request"] += 1
            if calls["request"] == 1:
                return type("Resp", (), {"status_code": 401})()
            return type("Resp", (), {"status_code": 200})()
        def close(self): pass
    def fake_get_token(config, env_name):
        return make_fake_token(60)
    def fake_acquire_token(config, grant_type):
        return make_fake_token(60)
    monkeypatch.setattr(auth, "get_token", fake_get_token)
    monkeypatch.setattr(auth, "acquire_token", fake_acquire_token)
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": lambda *a, **k: FakeClient()}))
    client = auth.AuthenticatedClient(config, env_name)
    resp = client.request("GET", "https://api.example.com/resource")
    assert calls["request"] == 2
    client.close()

def test_load_cached_token_exception(monkeypatch, tmp_path):
    env_name = "testenv"
    cache_dir = tmp_path / "tokens"
    cache_dir.mkdir(parents=True)
    monkeypatch.setattr(auth, "TOKEN_CACHE_DIR", cache_dir)
    path = cache_dir / f"{env_name}.json"
    path.write_text("not a json")
    # Should not raise, just log warning and return None
    assert auth.load_cached_token(env_name) is None

def test_authenticated_client_401_post_retry(monkeypatch):
    config = {"OAUTH_CLIENT_ID": "id", "OAUTH_CLIENT_SECRET": "secret", "OAUTH_TOKEN_URL": "url"}
    env_name = "testenv"
    calls = {"request": 0}
    class FakeClient:
        def __init__(self, *a, **k): self.headers = {}
        def request(self, method, url, **kwargs):
            calls["request"] += 1
            if calls["request"] == 1:
                return type("Resp", (), {"status_code": 401})()
            return type("Resp", (), {"status_code": 200})()
        def close(self): pass
    def fake_get_token(config, env_name):
        return make_fake_token(60)
    def fake_acquire_token(config, grant_type):
        return make_fake_token(60)
    monkeypatch.setattr(auth, "get_token", fake_get_token)
    monkeypatch.setattr(auth, "acquire_token", fake_acquire_token)
    monkeypatch.setattr(auth, "httpx", type("httpx", (), {"Client": lambda *a, **k: FakeClient()}))
    client = auth.AuthenticatedClient(config, env_name)
    resp = client.post("https://api.example.com/resource")
    assert calls["request"] == 2
    client.close()
