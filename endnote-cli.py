from typing import Optional

import click

from src import endnote_bibtex_export, endnote_bibtex_parser


@click.group()
def cli():
    """CLI to export and parse a EndNote library to BibTex."""
    pass


@cli.command()
@click.option("--user", required=True, help="Endnote user")
@click.option("--password", prompt=True, hide_input=True, required=True, help="Password password")
@click.option(
    "--file",
    help="Local Bibtex file",
    type=click.Path(exists=False, dir_okay=False, resolve_path=True),
    default="bibtex.bib",
)
def export(user: str, password: str, file: Optional[str] = None):
    """Export all EndNote refrences in BibTex format."""
    return endnote_bibtex_export.export(user=user, password=password, file=file)


@cli.command()
@click.option(
    "--input",
    help="Local Bibtex file from Endnote",
    type=click.Path(exists=False, dir_okay=False, resolve_path=True),
    default="bibtex.bib",
)
@click.option(
    "--output",
    help="Path for output file. Defaults to {input}_parsed.bib",
    type=click.Path(exists=False, dir_okay=False, resolve_path=True),
)
@click.option("--remove-notes", help="Clear notes field", type=click.BOOL, default=True)
def parse(input: Optional[str] = None, output: Optional[str] = None, remove_notes: bool = True):
    """Parse and homogenize a BibTex from Endnote."""
    return endnote_bibtex_parser.parse(input=input, output=output)


if __name__ == "__main__":
    cli()
