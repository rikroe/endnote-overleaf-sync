from pathlib import Path
from typing import Optional

import click

from src import overleaf_file_upload


@click.command()
@click.option("--host", required=True, help="URL (with https://) of your Overleaf instance")
@click.option("--user", required=True, help="Overleaf username")
@click.option("--password", prompt=True, hide_input=True, required=True, help="Overleaf password")
@click.option("--project", required=True, help="Project name (case sensitive)")
@click.option(
    "--file", required=True, help="File to upload", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option("--folder", help="Subfolder in project (case sensitive)", type=click.Path())
@click.option("--rename-to", help="Rename file on Overleaf", type=click.STRING)
def upload_cli(
    host: str,
    user: str,
    password: str,
    project: str,
    file: Path,
    folder: Optional[Path] = None,
    rename_to: Optional[str] = None,
):
    """Upload a file to an Overleaf project."""
    overleaf_file_upload.upload(
        host=host, user=user, password=password, project=project, file=file, folder=folder, rename_to=rename_to
    )


if __name__ == "__main__":
    upload_cli()
