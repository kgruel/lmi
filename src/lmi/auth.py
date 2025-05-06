"""Authentication and token management for lmi CLI (OAuth2, token caching, refresh)."""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

TOKEN_CACHE_DIR = Path.home() / ".cache" / "lmi" / "tokens"

logger = logging.getLogger(__name__)

def get_token_cache_path(env_name: str) -> Path:
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return TOKEN_CACHE_DIR / f"{env_name}.json"

def load_cached_token(env_name: str) -> dict[str, Any] | None:
    path = get_token_cache_path(env_name)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            try:
                token = json.load(f)
                if not is_token_expired(token):
                    logger.debug(f"Loaded valid cached token for {env_name}")
                    return token
                logger.info(f"Cached token for {env_name} expired")
            except Exception as e:
                logger.warning(f"Failed to load cached token: {e}")
    return None

def save_token(env_name: str, token: dict[str, Any]) -> None:
    path = get_token_cache_path(env_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(token, f)
    logger.debug(f"Saved token to cache for {env_name}")

def is_token_expired(token: dict[str, Any]) -> bool:
    import time
    expires_at = token.get("expires_at")
    if expires_at is None:
        # Fallback: check expires_in and issued_at
        issued_at = token.get("issued_at", 0)
        expires_in = token.get("expires_in", 0)
        expires_at = issued_at + expires_in
    return time.time() >= expires_at

def acquire_token(config: dict[str, str], grant_type: str = "client_credentials") -> dict[str, Any]:
    """Acquire a new OAuth2 token using the specified grant type."""
    data = {"grant_type": grant_type}
    if grant_type == "client_credentials":
        data["client_id"] = config["OAUTH_CLIENT_ID"]
        data["client_secret"] = config["OAUTH_CLIENT_SECRET"]
    elif grant_type == "password":
        data["client_id"] = config["OAUTH_CLIENT_ID"]
        data["client_secret"] = config["OAUTH_CLIENT_SECRET"]
        data["username"] = config["OAUTH_USERNAME"]
        data["password"] = config["OAUTH_PASSWORD"]
    else:
        raise ValueError(f"Unsupported grant_type: {grant_type}")
    token_url = config["OAUTH_TOKEN_URL"]
    logger.info(f"Requesting new token from {token_url} using {grant_type}")
    with httpx.Client(timeout=10) as client:
        resp = client.post(token_url, data=data)
        resp.raise_for_status()
        token = resp.json()
        # Add expiry calculation
        import time
        token["issued_at"] = int(time.time())
        if "expires_in" in token:
            token["expires_at"] = token["issued_at"] + int(token["expires_in"])
        return token

def get_token(config: dict[str, str], env_name: str) -> dict[str, Any]:
    token = load_cached_token(env_name)
    if token:
        return token
    grant_type = config.get("OAUTH_GRANT_TYPE", "client_credentials")
    token = acquire_token(config, grant_type=grant_type)
    save_token(env_name, token)
    return token

class AuthenticatedClient:
    def __init__(self, config: dict[str, str], env_name: str):
        self.config = config
        self.env_name = env_name
        self.token = get_token(config, env_name)
        self.client = httpx.Client(timeout=10)
        self.client.headers["Authorization"] = f"Bearer {self.token['access_token']}"

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        resp = self.client.request(method, url, **kwargs)
        if resp.status_code == 401:
            logger.warning("401 Unauthorized: refreshing token and retrying once")
            # Discard cache and retry
            save_token(self.env_name, {})  # Invalidate cache
            self.token = acquire_token(self.config, self.config.get("OAUTH_GRANT_TYPE", "client_credentials"))
            self.client.headers["Authorization"] = f"Bearer {self.token['access_token']}"
            resp = self.client.request(method, url, **kwargs)
        return resp

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def close(self):
        self.client.close()
