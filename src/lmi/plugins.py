from typing import Any

import pluggy

hookspec = pluggy.HookspecMarker("lmi")
hookimpl = pluggy.HookimplMarker("lmi")

class CliContext:
    def __init__(self, config: dict[str, str], logger: Any, http_client: Any, global_flags: dict[str, Any]):
        self.config = config
        self.logger = logger
        self.http_client = http_client
        self.global_flags = global_flags

class PluginSpec:
    @hookspec
    def register_commands(self, cli, context: CliContext):
        """Register click command groups with the CLI. Plugins receive the main click CLI group and a CliContext object."""

class PluginManager:
    def __init__(self):
        self.pm = pluggy.PluginManager("lmi")
        self.pm.add_hookspecs(PluginSpec)
        self.pm.load_setuptools_entrypoints("lmi_plugins")

    def register_plugins(self, cli, context: CliContext):
        self.pm.hook.register_commands(cli=cli, context=context)

plugin_manager = PluginManager()
