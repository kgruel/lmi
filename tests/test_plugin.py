import click
from click.testing import CliRunner

from lmi.plugins import PluginManager, hookimpl


def test_registers_command():
    @click.group()
    def testgroup():
        """Test plugin command group."""

    @testgroup.command()
    def hello():
        """Say hello from test plugin!"""
        click.echo("Hello from test plugin!")

    class TestPlugin:
        @hookimpl
        def register_commands(self, cli, context):
            cli.add_command(testgroup)

    # Create a fresh PluginManager and register the test plugin
    pm = PluginManager()
    pm.pm.register(TestPlugin(), name="test_plugin")

    # Create a dummy CLI and context
    @click.group()
    def cli():
        pass

    class DummyContext:
        pass

    pm.register_plugins(cli, DummyContext())
    runner = CliRunner()
    result = runner.invoke(cli, ["testgroup", "hello"])
    assert result.exit_code == 0
    assert "Hello from test plugin!" in result.output
