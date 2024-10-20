import asyncio
from pathlib import Path
from typing import Optional

import bibtexparser
import numpy as np
import pandas as pd
import slugify
from bibtexparser import customization


async def parse(input: Optional[str] = None, output: Optional[str] = None, remove_notes: bool = True) -> str | None:
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

        if remove_notes is True:
            entry.pop("note", None)
            entry.pop("keywords", None)

        entry = customization.homogenize_latex_encoding(entry)

    bib_database_df = pd.DataFrame(bib_database.entries)
    bib_database_df["key"] = bib_database_df["key"].astype(str)
    bib_database_df["doi"] = bib_database_df["doi"].astype(str)

    duplicate_keys = bib_database_df["key"].duplicated(keep=False)

    bib_database_df["key"] = np.where(
        duplicate_keys,
        bib_database_df.apply(lambda x: "-".join([c for c in [x["key"], x["doi"]] if c]), axis=1),
        bib_database_df["key"],
    )
    bib_database_df["ID"] = bib_database_df["key"].str.replace("-", "_")

    bib_database.entries = [{k: v for k, v in x.items() if v == v} for x in bib_database_df.to_dict(orient="records")]

    bib_database.add_missing_from_crossref()

    if not output:
        return bibtexparser.dumps(bib_database)

    await asyncio.to_thread(output_path.write_text, bibtexparser.dumps(bib_database))

    return None


if __name__ == "__main__":
    asyncio.run(parse("bibtex_endnote.bib", "bibtex.bib"))
