"""SSO authentication for lmi CLI using OAuth 2.0 Authorization Code Grant with PKCE."""

import base64
import hashlib
import json
import logging
import os
import secrets
import webbrowser
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Event, Thread
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

import keyring
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc7636 import create_s256_code_challenge

logger = logging.getLogger(__name__)

# Keyring service name for storing SSO tokens
KEYRING_SERVICE = "lmi-cli-sso"
KEYRING_USERNAME = "sso-tokens"

@dataclass
class SSOToken:
    """Container for SSO tokens."""
    access_token: str
    refresh_token: Optional[str]
    id_token: Optional[str]
    expires_at: int
    token_type: str = "Bearer"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SSOToken":
        """Create an SSOToken from a dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            expires_at=data["expires_at"],
            token_type=data.get("token_type", "Bearer"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        import time
        return time.time() >= self.expires_at

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

class SSOAuth:
    """Handles SSO authentication using OAuth 2.0 Authorization Code Grant with PKCE."""

    def __init__(self, config: dict[str, str]) -> None:
        """Initialize SSO authentication.

        Args:
            config: Configuration dictionary containing OAuth settings.
        """
        self.config = config
        self.client_id = config["OAUTH_SSO_CLIENT_ID"]
        self.auth_url = config["OAUTH_SSO_AUTHORIZATION_URL"]
        self.token_url = config["OAUTH_SSO_TOKEN_URL"]
        self.scopes = config.get("OAUTH_SSO_SCOPES", "openid profile email offline_access").split()
        self.redirect_uri = "http://localhost:0/callback"  # Port will be assigned dynamically

    def _generate_code_verifier(self) -> str:
        """Generate a code verifier for PKCE."""
        return secrets.token_urlsafe(64)

    def _get_stored_token(self) -> Optional[SSOToken]:
        """Retrieve stored SSO tokens from keyring."""
        try:
            data = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if data:
                return SSOToken.from_dict(json.loads(data))
        except Exception as e:
            logger.warning(f"Failed to retrieve stored token: {e}")
        return None

    def _store_token(self, token: SSOToken) -> None:
        """Store SSO tokens in keyring."""
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, json.dumps(token.to_dict()))
        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            raise

    def _clear_stored_token(self) -> None:
        """Clear stored SSO tokens from keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception as e:
            logger.warning(f"Failed to clear stored token: {e}")

    def login(self) -> SSOToken:
        """Perform interactive SSO login.

        Returns:
            SSOToken: The obtained SSO tokens.

        Raises:
            RuntimeError: If login fails.
        """
        # Check for existing valid token
        if token := self._get_stored_token():
            if not token.is_expired:
                logger.info("Using existing valid SSO token")
                return token
            if token.refresh_token:
                try:
                    return self._refresh_token(token)
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")

        # Generate PKCE values
        code_verifier = self._generate_code_verifier()
        code_challenge = create_s256_code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)

        # Start local server for callback
        server = HTTPServer(("localhost", 0), SSOCallbackHandler)
        port = server.server_address[1]
        callback_uri = f"http://localhost:{port}/callback"

        # Construct authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": callback_uri,
            "scope": " ".join(self.scopes),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        auth_url = f"{self.auth_url}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"

        # Open browser and wait for callback
        logger.info("Opening browser for SSO login...")
        webbrowser.open(auth_url)

        # Wait for callback
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            # Wait for callback with timeout
            if not server.RequestHandlerClass.done.wait(timeout=300):  # 5 minutes timeout
                raise RuntimeError("SSO login timed out")

            handler = server.RequestHandlerClass
            if handler.error:
                raise RuntimeError(f"SSO login failed: {handler.error}")
            if not handler.auth_code or not handler.state:
                raise RuntimeError("Invalid callback response")
            if handler.state != state:
                raise RuntimeError("State mismatch - possible CSRF attack")

            # Exchange code for tokens
            client = OAuth2Client(
                client_id=self.client_id,
                token_endpoint=self.token_url,
                token_endpoint_auth_method="none",  # Public client
            )
            token_data = client.fetch_token(
                self.token_url,
                grant_type="authorization_code",
                code=handler.auth_code,
                code_verifier=code_verifier,
                redirect_uri=callback_uri,
            )

            # Create and store token
            import time
            token = SSOToken(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                id_token=token_data.get("id_token"),
                expires_at=int(time.time()) + int(token_data.get("expires_in", 3600)),
                token_type=token_data.get("token_type", "Bearer"),
            )
            self._store_token(token)
            return token

        finally:
            server.shutdown()
            server.server_close()

    def _refresh_token(self, token: SSOToken) -> SSOToken:
        """Refresh an expired token.

        Args:
            token: The expired token to refresh.

        Returns:
            SSOToken: The new token.

        Raises:
            RuntimeError: If refresh fails.
        """
        if not token.refresh_token:
            raise RuntimeError("No refresh token available")

        client = OAuth2Client(
            client_id=self.client_id,
            token_endpoint=self.token_url,
            token_endpoint_auth_method="none",
        )
        try:
            token_data = client.refresh_token(
                self.token_url,
                refresh_token=token.refresh_token,
            )
            import time
            new_token = SSOToken(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", token.refresh_token),
                id_token=token_data.get("id_token", token.id_token),
                expires_at=int(time.time()) + int(token_data.get("expires_in", 3600)),
                token_type=token_data.get("token_type", "Bearer"),
            )
            self._store_token(new_token)
            return new_token
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            self._clear_stored_token()
            raise RuntimeError("Failed to refresh token") from e

    def logout(self) -> None:
        """Log out by clearing stored tokens."""
        self._clear_stored_token()

    def get_token(self) -> Optional[SSOToken]:
        """Get current SSO token, refreshing if necessary.

        Returns:
            Optional[SSOToken]: The current token, or None if not logged in.
        """
        if token := self._get_stored_token():
            if token.is_expired and token.refresh_token:
                try:
                    return self._refresh_token(token)
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    return None
            return token
        return None

    def get_status(self) -> dict[str, Any]:
        """Get current SSO login status.

        Returns:
            dict[str, Any]: Status information including login state and token details.
        """
        token = self.get_token()  # This already handles expired tokens with refresh
        if not token:
            return {"logged_in": False}

        import time
        # Consider a token logged out if it's expired and has no refresh token
        is_logged_in = not (token.is_expired and not token.refresh_token)
        return {
            "logged_in": is_logged_in,
            "expires_at": token.expires_at,
            "expires_in": max(0, token.expires_at - int(time.time())),
            "has_refresh_token": bool(token.refresh_token),
            "has_id_token": bool(token.id_token),
        } 