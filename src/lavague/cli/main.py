import click
import importlib.util
from lavague.version_checker import check_latest_version

class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        try:
            check_latest_version()
        except:
            pass
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name):
        # lazily loading a command, first get the module name and attribute name
        import_path = self.lazy_subcommands[cmd_name]
        modname, cmd_object_name = import_path.rsplit(".", 1)
        # do the import
        mod = importlib.import_module(modname)
        # get the Command object from that module
        cmd_object = getattr(mod, cmd_object_name)
        # check the result to make debugging easier
        if not isinstance(cmd_object, click.BaseCommand):
            raise ValueError(
                f"Lazy loading of {import_path} failed by returning "
                "a non-command object"
            )
        return cmd_object


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "launch": "lavague.cli.commands.launch",
        "build": "lavague.cli.commands.build",
        "eval": "lavague.cli.commands.evaluation",
        "test": "lavague.cli.commands.test",
    },
)
@click.option(
    "--instructions",
    "-i",
    type=click.Path(exists=True),
    required=False,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=False,
)

@click.pass_context
def cli(ctx, instructions, config):
    """Copilot for devs to automate automation"""
    ctx.ensure_object(dict)
    ctx.obj["instructions"] = instructions
    ctx.obj["config"] = config
