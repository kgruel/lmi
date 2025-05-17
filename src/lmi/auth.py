"""Authentication and token management for lmi CLI (OAuth2, token caching, refresh)."""

import base64
import hashlib
import json
import logging
import secrets
import time
import webbrowser
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Event, Thread
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc7636 import create_s256_code_challenge

TOKEN_CACHE_DIR = Path.home() / ".cache" / "lmi" / "tokens"

logger = logging.getLogger(__name__)

@dataclass
class AuthToken:
    """Unified token container for all authentication methods."""
    access_token: str
    expires_at: int
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    issued_at: Optional[int] = field(default_factory=lambda: int(time.time()))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthToken":
        """Create an AuthToken from a dictionary."""
        return cls(
            access_token=data["access_token"],
            expires_at=data.get("expires_at", 0),
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            issued_at=data.get("issued_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "issued_at": self.issued_at,
        }

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return time.time() >= self.expires_at

def get_token_cache_path(env_name: str) -> Path:
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return TOKEN_CACHE_DIR / f"{env_name}.json"

def load_cached_token(env_name: str) -> Optional[AuthToken]:
    path = get_token_cache_path(env_name)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
                token = AuthToken.from_dict(data)
                if not token.is_expired:
                    logger.debug(f"Loaded valid cached token for {env_name}")
                    return token
                logger.info(f"Cached token for {env_name} expired")
            except Exception as e:
                logger.warning(f"Failed to load cached token: {e}")
    return None

def save_token(env_name: str, token: AuthToken) -> None:
    path = get_token_cache_path(env_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(token.to_dict(), f)
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

class SSOCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle the OAuth callback."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.auth_code: Optional[str] = None
        self.state: Optional[str] = None
        self.error: Optional[str] = None
        self.done = Event()
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET request from OAuth callback."""
        try:
            query = parse_qs(urlparse(self.path).query)
            self.auth_code = query.get("code", [None])[0]
            self.state = query.get("state", [None])[0]
            self.error = query.get("error", [None])[0]

            if self.error:
                self.send_error(400, f"Authorization failed: {self.error}")
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication successful!</h1>"
                    b"<p>You can close this window and return to the CLI.</p></body></html>"
                )
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self.send_error(500, str(e))
        finally:
            self.done.set()

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use our logger."""
        logger.debug(f"SSO callback server: {format % args}")

def _acquire_pkce_token(config: dict[str, str], env_name: str) -> Optional[AuthToken]:
    """Acquire a token using PKCE flow.
    
    Args:
        config: Configuration dictionary.
        env_name: Environment name for token caching.
        
    Returns:
        Optional[AuthToken]: The acquired token, or None if acquisition fails.
        
    Raises:
        RuntimeError: If PKCE flow fails.
    """
    client_id = config["OAUTH_CLIENT_ID"]
    auth_url = config["OAUTH_AUTHORIZE_URL"]
    token_url = config["OAUTH_TOKEN_URL"]
    scopes = config.get("OAUTH_SCOPES", "openid profile email offline_access").split()
    
    # Generate PKCE values
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = create_s256_code_challenge(code_verifier)
    state = secrets.token_urlsafe(32)
    
    # Start local server for callback
    server = HTTPServer(("localhost", 0), SSOCallbackHandler)
    port = server.server_address[1]
    callback_uri = f"http://localhost:{port}/callback"
    
    # Store handler instance for waiting
    handler_instance = None
    def handler_factory(*args, **kwargs):
        nonlocal handler_instance
        handler_instance = SSOCallbackHandler(*args, **kwargs)
        return handler_instance
    server.RequestHandlerClass = handler_factory
    
    # Construct authorization URL
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": callback_uri,
        "scope": " ".join(scopes),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    
    # Open browser and wait for callback
    logger.info("Opening browser for SSO login...")
    webbrowser.open(auth_url)
    
    # Wait for callback
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Wait for callback with timeout
        if not handler_instance or not handler_instance.done.wait(timeout=300):  # 5 minutes timeout
            raise RuntimeError("SSO login timed out")
        if handler_instance.error:
            raise RuntimeError(f"SSO login failed: {handler_instance.error}")
        if not handler_instance.auth_code or not handler_instance.state:
            raise RuntimeError("Invalid callback response")
        if handler_instance.state != state:
            raise RuntimeError("State mismatch - possible CSRF attack")
        
        # Exchange code for tokens
        client = OAuth2Client(
            client_id=client_id,
            token_endpoint=token_url,
            token_endpoint_auth_method="none",  # Public client
        )
        token_data = client.fetch_token(
            token_url,
            grant_type="authorization_code",
            code=handler_instance.auth_code,
            code_verifier=code_verifier,
            redirect_uri=callback_uri,
        )
        
        # Create and return token
        issued_at = int(time.time())
        expires_at = issued_at + int(token_data.get("expires_in", 3600))
        return AuthToken(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
            issued_at=issued_at,
        )
    
    finally:
        server.shutdown()
        server.server_close()

def acquire_token(config: dict[str, str], grant_type: str = "client_credentials") -> AuthToken:
    """Acquire a new OAuth2 token using the specified grant type."""
    if grant_type == "authorization_code_pkce":
        token = _acquire_pkce_token(config, config.get("default_environment", "default"))
        if not token:
            raise RuntimeError("Failed to acquire token via PKCE flow")
        return token
        
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
        token_data = resp.json()
        # Add expiry calculation
        issued_at = int(time.time())
        expires_at = issued_at + int(token_data.get("expires_in", 3600))
        return AuthToken(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
            issued_at=issued_at,
        )

def get_token(config: dict[str, str], env_name: str, allow_interactive_for_new: bool = False, force_new: bool = False) -> Optional[AuthToken]:
    """Get a valid token, refreshing or acquiring a new one if necessary.
    
    Args:
        config: Configuration dictionary.
        env_name: Environment name for token caching.
        allow_interactive_for_new: Whether to allow interactive login for new tokens.
        force_new: Whether to force acquisition of a new token.
        
    Returns:
        Optional[AuthToken]: A valid token, or None if acquisition fails.
    """
    if not force_new:
        # Try to load cached token
        token = load_cached_token(env_name)
        if token and not token.is_expired:
            return token
        
        # Try to refresh if we have a refresh token
        if token and token.refresh_token:
            try:
                return _refresh_auth_token(token, config)
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
    
    # Acquire new token
    try:
        grant_type = config.get("OAUTH_GRANT_TYPE", "client_credentials")
        if grant_type == "authorization_code_pkce" and not allow_interactive_for_new:
            logger.warning("PKCE flow requires interactive login, but allow_interactive_for_new is False")
            return None
        
        token = acquire_token(config, grant_type)
        if token:
            save_token(env_name, token)
        return token
    except Exception as e:
        logger.error(f"Failed to acquire token: {e}")
        return None

def _refresh_auth_token(token: AuthToken, config: dict[str, str]) -> AuthToken:
    """Refresh an expired token.
    
    Args:
        token: The expired token to refresh.
        config: Configuration dictionary.
        
    Returns:
        AuthToken: The new token.
        
    Raises:
        RuntimeError: If refresh fails.
    """
    if not token.refresh_token:
        raise RuntimeError("No refresh token available")
    
    data = {
        "grant_type": "refresh_token",
        "client_id": config["OAUTH_CLIENT_ID"],
        "client_secret": config["OAUTH_CLIENT_SECRET"],
        "refresh_token": token.refresh_token,
    }
    
    token_url = config["OAUTH_TOKEN_URL"]
    with httpx.Client(timeout=10) as client:
        resp = client.post(token_url, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        
        issued_at = int(time.time())
        expires_at = issued_at + int(token_data.get("expires_in", 3600))
        return AuthToken(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", token.refresh_token),
            id_token=token_data.get("id_token", token.id_token),
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
            issued_at=issued_at,
        )

class AuthenticatedClient:
    def __init__(self, config: dict[str, str], env_name: str):
        self.config = config
        self.env_name = env_name
        self.token = get_token(config, env_name)
        if not self.token:
            raise RuntimeError("Failed to acquire initial token")
        self.client = httpx.Client(timeout=10)
        self.client.headers["Authorization"] = f"{self.token.token_type} {self.token.access_token}"

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        resp = self.client.request(method, url, **kwargs)
        if resp.status_code == 401:
            logger.warning("401 Unauthorized: refreshing token and retrying once")
            # Try to refresh token
            if self.token and self.token.refresh_token:
                try:
                    self.token = _refresh_auth_token(self.token, self.config)
                    save_token(self.env_name, self.token)
                    self.client.headers["Authorization"] = f"{self.token.token_type} {self.token.access_token}"
                    resp = self.client.request(method, url, **kwargs)
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    # Invalidate cache
                    save_token(self.env_name, AuthToken(
                        access_token="",
                        refresh_token=None,
                        id_token=None,
                        expires_at=0
                    ))
                    raise RuntimeError("Authentication failed and token refresh unsuccessful") from e
            else:
                raise RuntimeError("Authentication failed and no refresh token available")
        return resp

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)
    
    def close(self):
        self.client.close()
