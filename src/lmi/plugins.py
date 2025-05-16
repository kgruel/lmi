"""Plugin system for lmi CLI."""

from typing import Any, Optional

import pluggy
from lmi.sso import SSOAuth, SSOToken

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
        self._sso: Optional[SSOAuth] = None

    @property
    def sso(self) -> Optional[SSOAuth]:
        """Get SSO authentication instance.
        
        Returns:
            Optional[SSOAuth]: SSO authentication instance if SSO is configured.
        """
        if self._sso is None:
            try:
                # Only create SSO instance if required config is present
                if all(k in self.config for k in ["OAUTH_SSO_CLIENT_ID", "OAUTH_SSO_AUTHORIZATION_URL", "OAUTH_SSO_TOKEN_URL"]):
                    self._sso = SSOAuth(self.config)
            except Exception as e:
                self.logger.warning(f"Failed to initialize SSO: {e}")
        return self._sso

    def is_sso_authenticated(self) -> bool:
        """Check if user is authenticated via SSO.
        
        Returns:
            bool: True if user is authenticated and token is valid.
        """
        if not self.sso:
            return False
        return bool(self.sso.get_token())

    def get_sso_token(self) -> Optional[SSOToken]:
        """Get current SSO token.
        
        Returns:
            Optional[SSOToken]: Current SSO token if authenticated.
        """
        if not self.sso:
            return None
        return self.sso.get_token()

    def get_sso_status(self) -> dict[str, Any]:
        """Get SSO authentication status.
        
        Returns:
            dict[str, Any]: Status information including login state and token details.
        """
        if not self.sso:
            return {"logged_in": False, "error": "SSO not configured"}
        return self.sso.get_status()

class PluginSpec:
    @hookspec
    def register_commands(self, cli, context: CliContext):
        """Register click command groups with the CLI.
        
        Args:
            cli: Main click CLI group.
            context: CliContext object providing access to configuration, logging,
                    HTTP client, and SSO authentication status.
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
