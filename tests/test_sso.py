"""Tests for SSO authentication."""

import json
import time
from unittest.mock import MagicMock, patch

import keyring
import pytest
from authlib.integrations.httpx_client import OAuth2Client

from lmi.sso import SSOAuth, SSOToken

@pytest.fixture
def sso_config():
    return {
        "OAUTH_SSO_CLIENT_ID": "test-client",
        "OAUTH_SSO_AUTHORIZATION_URL": "https://example.com/auth",
        "OAUTH_SSO_TOKEN_URL": "https://example.com/token",
        "OAUTH_SSO_SCOPES": "openid profile email offline_access",
    }

@pytest.fixture
def mock_token():
    return SSOToken(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        id_token="test-id-token",
        expires_at=int(time.time()) + 3600,
        token_type="Bearer",
    )

def test_sso_token_serialization(mock_token):
    """Test SSOToken serialization and deserialization."""
    data = mock_token.to_dict()
    token2 = SSOToken.from_dict(data)
    assert token2.access_token == mock_token.access_token
    assert token2.refresh_token == mock_token.refresh_token
    assert token2.id_token == mock_token.id_token
    assert token2.expires_at == mock_token.expires_at
    assert token2.token_type == mock_token.token_type

def test_sso_token_expiry(mock_token):
    """Test SSOToken expiry check."""
    assert not mock_token.is_expired
    mock_token.expires_at = int(time.time()) - 1
    assert mock_token.is_expired

def test_sso_auth_init(sso_config):
    """Test SSOAuth initialization."""
    sso = SSOAuth(sso_config)
    assert sso.client_id == sso_config["OAUTH_SSO_CLIENT_ID"]
    assert sso.auth_url == sso_config["OAUTH_SSO_AUTHORIZATION_URL"]
    assert sso.token_url == sso_config["OAUTH_SSO_TOKEN_URL"]
    assert sso.scopes == sso_config["OAUTH_SSO_SCOPES"].split()

def test_sso_token_storage(sso_config, mock_token):
    """Test SSO token storage in keyring."""
    sso = SSOAuth(sso_config)
    
    # Store token
    sso._store_token(mock_token)
    
    # Retrieve token
    stored = sso._get_stored_token()
    assert stored is not None
    assert stored.access_token == mock_token.access_token
    assert stored.refresh_token == mock_token.refresh_token
    assert stored.id_token == mock_token.id_token
    assert stored.expires_at == mock_token.expires_at
    
    # Clear token
    sso._clear_stored_token()
    assert sso._get_stored_token() is None

@patch("lmi.sso.webbrowser.open")
@patch("lmi.sso.HTTPServer")
@patch("lmi.sso.secrets.token_urlsafe")  # Mock the state generation
def test_sso_login_flow(mock_token_urlsafe, mock_server, mock_browser, sso_config, mock_token):
    """Test SSO login flow."""
    # Mock state generation
    expected_state = "test-state"
    mock_token_urlsafe.return_value = expected_state
    
    # Mock server and callback
    mock_handler = MagicMock()
    mock_handler.auth_code = "test-auth-code"
    mock_handler.state = expected_state  # Use the same state
    mock_handler.error = None
    mock_handler.done = MagicMock()
    mock_handler.done.wait.return_value = True
    mock_server.return_value.RequestHandlerClass = mock_handler
    mock_server.return_value.server_address = ("localhost", 12345)
    
    # Mock token exchange
    mock_client = MagicMock(spec=OAuth2Client)
    token_response = {
        "access_token": mock_token.access_token,
        "refresh_token": mock_token.refresh_token,
        "id_token": mock_token.id_token,
        "expires_in": 3600,
        "token_type": mock_token.token_type,
    }
    mock_client.fetch_token.return_value = token_response
    
    # Clear any existing tokens before test
    with patch("lmi.sso.keyring") as mock_keyring:
        mock_keyring.get_password.return_value = None  # Ensure no stored token
        
        with patch("lmi.sso.OAuth2Client", return_value=mock_client):
            sso = SSOAuth(sso_config)
            token = sso.login()
            
            # Verify token values match what we expect
            assert token.access_token == mock_token.access_token, "Access token mismatch"
            assert token.refresh_token == mock_token.refresh_token, "Refresh token mismatch"
            assert token.id_token == mock_token.id_token, "ID token mismatch"
            assert token.token_type == mock_token.token_type, "Token type mismatch"
            
            # Verify browser was opened with correct state
            mock_browser.assert_called_once()
            auth_url = mock_browser.call_args[0][0]
            assert f"state={expected_state}" in auth_url, "State not in auth URL"
            
            # Verify token exchange
            mock_client.fetch_token.assert_called_once()
            call_kwargs = mock_client.fetch_token.call_args[1]
            assert call_kwargs["grant_type"] == "authorization_code"
            assert call_kwargs["code"] == "test-auth-code"
            
            # Verify token was stored
            mock_keyring.set_password.assert_called_once()
            stored_data = json.loads(mock_keyring.set_password.call_args[0][2])
            assert stored_data["access_token"] == mock_token.access_token

@patch("lmi.sso.OAuth2Client")
def test_sso_token_refresh(mock_client_class, sso_config, mock_token):
    """Test SSO token refresh."""
    # Mock refresh response
    new_token = SSOToken(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        id_token="new-id-token",
        expires_at=int(time.time()) + 3600,
        token_type="Bearer",
    )
    mock_client = MagicMock(spec=OAuth2Client)
    mock_client.refresh_token.return_value = {
        "access_token": new_token.access_token,
        "refresh_token": new_token.refresh_token,
        "id_token": new_token.id_token,
        "expires_in": 3600,
        "token_type": new_token.token_type,
    }
    mock_client_class.return_value = mock_client
    
    sso = SSOAuth(sso_config)
    refreshed = sso._refresh_token(mock_token)
    
    assert refreshed.access_token == new_token.access_token
    assert refreshed.refresh_token == new_token.refresh_token
    assert refreshed.id_token == new_token.id_token
    assert refreshed.token_type == new_token.token_type
    
    # Verify refresh call
    mock_client.refresh_token.assert_called_once()
    call_kwargs = mock_client.refresh_token.call_args[1]
    assert call_kwargs["refresh_token"] == mock_token.refresh_token

def test_sso_status(sso_config, mock_token):
    """Test SSO status reporting."""
    sso = SSOAuth(sso_config)
    
    # Not logged in
    with patch.object(sso, "_get_stored_token", return_value=None):
        status = sso.get_status()
        assert not status["logged_in"]
    
    # Logged in with valid token
    with patch.object(sso, "_get_stored_token", return_value=mock_token):
        status = sso.get_status()
        assert status["logged_in"]
        assert status["expires_at"] == mock_token.expires_at
        assert status["has_refresh_token"]
        assert status["has_id_token"]
    
    # Logged in with expired token
    expired_token = SSOToken(
        access_token=mock_token.access_token,
        refresh_token=None,  # No refresh token
        id_token=mock_token.id_token,
        expires_at=int(time.time()) - 1,  # Expired
        token_type=mock_token.token_type,
    )
    with patch.object(sso, "_get_stored_token", return_value=expired_token):
        status = sso.get_status()
        assert not status["logged_in"]  # Should be considered logged out without refresh token 