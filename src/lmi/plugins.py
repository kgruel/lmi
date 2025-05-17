"""Plugin system for lmi CLI."""

from typing import Any, Optional

import pluggy
from lmi import auth
from lmi.auth import AuthToken

hookspec = pluggy.HookspecMarker("lmi")
hookimpl = pluggy.HookimplMarker("lmi")

class CliContext:
    def __init__(self, config: dict[str, str], logger: Any, http_client: Any, global_flags: dict[str, Any]):
        """Context object passed to plugins.
        
        Args:
            config: Configuration dictionary.
            logger: Logger instance.
            http_client: Authenticated HTTP client.
            global_flags: Global CLI flags including 'output' (output format, e.g., 'json').
        """
        self.config = config
        self.logger = logger
        self.http_client = http_client
        self.global_flags = global_flags
        self._auth_token: Optional[AuthToken] = None

    @property
    def auth_token(self) -> Optional[AuthToken]:
        """Get current authentication token.
        
        Returns:
            Optional[AuthToken]: Current authentication token if available.
        """
        if self._auth_token is None:
            try:
                # Only get token if required config is present
                if "OAUTH_GRANT_TYPE" in self.config:
                    self._auth_token = auth.get_token(self.config, "default", allow_interactive_for_new=False)
            except Exception as e:
                self.logger.warning(f"Failed to get auth token: {e}")
        return self._auth_token

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.
        
        Returns:
            bool: True if user is authenticated and token is valid.
        """
        if not self.auth_token:
            return False
        return not self.auth_token.is_expired

    def get_auth_status(self) -> dict[str, Any]:
        """Get authentication status.
        
        Returns:
            dict[str, Any]: Status information including login state and token details.
        """
        if not self.auth_token:
            return {"logged_in": False, "error": "Authentication not configured"}
        
        return {
            "logged_in": not self.auth_token.is_expired,
            "token_type": self.auth_token.token_type,
            "expires_at": self.auth_token.expires_at,
            "has_refresh_token": bool(self.auth_token.refresh_token),
            "has_id_token": bool(self.auth_token.id_token)
        }

class PluginSpec:
    @hookspec
    def register_commands(self, cli, context: CliContext):
        """Register click command groups with the CLI.
        
        Args:
            cli: Main click CLI group.
            context: CliContext object providing access to configuration, logging,
                    HTTP client, and authentication status.
        """
        """Register click command groups with the CLI. Plugins receive the main click CLI group and a CliContext object.
        Plugins should use context.global_flags['output'] and the format_output utility for output formatting.
        """

class PluginManager:
    def __init__(self):
        self.pm = pluggy.PluginManager("lmi")
        self.pm.add_hookspecs(PluginSpec)
        self.pm.load_setuptools_entrypoints("lmi_plugins")

    def register_plugins(self, cli, context: CliContext):
        self.pm.hook.register_commands(cli=cli, context=context)

plugin_manager = PluginManager()
