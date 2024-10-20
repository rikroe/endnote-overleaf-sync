import asyncio
from pathlib import Path
from typing import Optional

import bibtexparser
import slugify
from bibtexparser import customization


async def parse(input: Optional[str] = None, output: Optional[str] = None, remove_notes: bool = True):
    """Parse and homogenize a BibTex from Endnote."""

    input_path = Path(input or "")
    output_path = input_path.with_name(f"{input_path.stem}_parsed{input_path.suffix}") if not output else Path(output)

    bib_database = await asyncio.to_thread(bibtexparser.loads, input_path.read_text())

    for entry in bib_database.entries:
        first_author = (entry.get("author") or "").split(",")[0]
        id_components = [
            first_author,
            next(iter([t for t in (entry.get("title") or "").split(" ") if len(t) > 3]), None),
            entry.get("year"),
        ]
        id = " ".join([str(c).lower() for c in id_components if c])
        entry["ID"] = slugify.slugify(id, separator="_")
        entry["key"] = slugify.slugify(id)

        if remove_notes is True and "note" in entry:
            entry.pop("note")

        entry = customization.homogenize_latex_encoding(entry)

    bib_database.add_missing_from_crossref()

    await asyncio.to_thread(output_path.write_text, bibtexparser.dumps(bib_database))


if __name__ == "__main__":
    asyncio.run(parse("bibtex_endnote.bib", "bibtex.bib"))
