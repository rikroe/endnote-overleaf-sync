import asyncio
import os
import tempfile
import time
from pathlib import Path

import bibtexparser
import pandas as pd
import streamlit as st
from bibtexparser import customization
from dotenv import dotenv_values

# Import functions from other files
from endnote_bibtex_export import export as export_endnote
from endnote_bibtex_parser import parse as parse_bibtex
from overleaf_file_upload import upload as upload_file

CONFIG = dotenv_values(".env") | dict(os.environ)
RELEVANT_FIELDS = [
    "ID",
    "type",
    "title",
    "author",
    "year",
    "journal",
    "volume",
    "number",
    "pages",
    "doi",
]

st.set_page_config(
    page_title="BibTeX Viewer",
    page_icon=":book:",
    layout="wide",
)


def login(password: str):
    """Return simple password check."""
    session_password = st.session_state.get("password", "")

    # continue if session password is correct
    if session_password != password:
        # check if password is correct
        if st.query_params.get("password", "") == password:
            st.session_state.password = password
            st.rerun()

        with st.form(key="password_form", border=False):
            entered_password = st.text_input("Passwort:", type="password")
            if session_password:
                st.error("Wrong password. Please try again.")
            if st.form_submit_button("Login"):
                st.session_state.password = entered_password
                # st.rerun()
            st.stop()


@st.cache_data
def load_bibtex(file_path):
    """Load the BibTeX file and return a DataFrame."""
    entries = []
    if not Path(file_path).exists():
        return pd.DataFrame()
    with open(file_path) as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    for entry in bib_database.entries:
        entries.append({k: customization.latex_to_unicode(v) for k, v in entry.items()})
    return pd.DataFrame(entries).fillna("")


@st.cache_data
def search_bibtex(df: pd.DataFrame, search: str):
    """Search loaded BibTeX entries."""
    df = df[df.apply(lambda col: col.str.contains(search.lower(), case=False, na=False), axis=1).any(axis=1)].copy()
    df["abstract"] = df["abstract"].str.replace(
        search, f'<span style="color: red; font-weight: bold;">{search}</span>', case=False
    )
    return df


@st.dialog("Refreshing...")
def latex_refresh():
    """Show dialog while refreshing the BibTeX file."""
    with st.spinner("May take up to 30 seconds..."):
        time.sleep(1)
        c = st.empty()
        try:
            refresh_bibtex(c)
            with c:
                st.success("Refreshed!")
                load_bibtex.clear()
        except Exception as e:
            with c:
                st.error(f"{type(e).__name__}: {str(e)}")


def refresh_bibtex(c):
    """Export from EndNote, parse, and upload to Overleaf as bibtex.bib."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Export from EndNote
        with c:
            asyncio.run(
                export_endnote(
                    CONFIG.get("ENDNOTE_USER"),
                    CONFIG.get("ENDNOTE_PASSWORD"),
                    Path(temp_dir) / "bibtex_endnote.bib",
                    callback=st.info,
                ),
            )
            # st.success("Exported from EndNote")
        # Parse the exported file
        asyncio.run(
            parse_bibtex(Path(temp_dir) / "bibtex_endnote.bib", Path(temp_dir) / "bibtex.bib", remove_notes=True)
        )
        with c:
            st.info("Converted EndNote to Latex")

        # Upload to Overleaf
        with c:
            st.info("Uploading to Overleaf...")
        asyncio.run(
            upload_file(
                host=CONFIG.get("OVERLEAF_HOST"),
                user=CONFIG.get("OVERLEAF_USER"),
                password=CONFIG.get("OVERLEAF_PASSWORD"),
                project=CONFIG.get("OVERLEAF_PROJECT"),
                file=Path(temp_dir) / "bibtex.bib",
            )
        )
        with c:
            st.info("Uploading to Overleaf... Done.")

        # Store bibtex file locally for viewing
        if CONFIG.get("BIBTEX_PATH"):
            bibtex_path = Path(CONFIG.get("BIBTEX_PATH"))
            bibtex_path.parent.mkdir(parents=True, exist_ok=True)
            bibtex_path.write_text((Path(temp_dir) / "bibtex.bib").read_text())


@st.fragment
def viewer():
    """Search and view BibTeX entries."""
    st.subheader("Search and view BibTeX entries")

    # Load and display BibTeX entries
    bib_entries = load_bibtex(CONFIG.get("BIBTEX_PATH"))
    if len(bib_entries) == 0:
        st.error("No BibTeX entries found. Please run the sync.")
        return

    search = st.text_input("Search")

    if search:
        df = search_bibtex(bib_entries, search)
        st.subheader(f"{len(df)} results for '{search}'")
        for entry in df.to_dict(orient="records"):
            with st.expander(f"```{entry.get('ID')}```\n\n**{entry.get('title')}**\n\n{entry.get('author')}"):
                c = st.columns(2)
                with c[0]:
                    st.table({k.title(): entry[k] for k in RELEVANT_FIELDS})
                with c[1]:
                    st.markdown(entry.get("abstract", "*No Abstract.*"), unsafe_allow_html=True)
    else:
        st.info("Enter a search term to display BibTeX entries.")


# Streamlit app
def main():
    """Run the app."""

    st.title("BibTeX Viewer")

    login(CONFIG.get("STREAMLIT_PASSWORD"))

    st.button("Sync from EndNote to Overleaf", on_click=latex_refresh)

    viewer()


if __name__ == "__main__":
    main()
