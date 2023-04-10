from pathlib import Path
from typing import Optional

import requests


def export(user: str, password: str, file: Optional[str] = None):
    """Export all EndNote refrences in BibTex format."""

    s = requests.Session()
    s.headers.update(
        {
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://access.clarivate.com/login?app=endnote",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/111.0.0.0 Safari/537.36"
            ),
        }
    )

    # Login
    print("Logging in...")
    r_login_authorize = s.post(
        "https://access.clarivate.com/api/authorize",
        json={
            "loginid": user,
            "password": password,
            "loginAccount": "",
            "app": "endnote",
        },
    )
    r_login_authorize.raise_for_status()

    r_login_redirect = s.get(f"https://access.clarivate.com/api/session/endnote/{r_login_authorize.json()['code']}")
    r_login_redirect.raise_for_status()

    r_login_cookie = s.get(
        r_login_redirect.json()["enRedirectUrl"],
    )
    r_login_cookie.raise_for_status()

    # Export all references to Bibtex
    print("Exporting to BibTex...")
    s.headers.pop("Referer")
    r_export = s.post(
        "https://www.myendnoteweb.com/EndNoteWeb.html",
        params={"func": "export citations 2"},
        data={
            "RefName": "e Referenzen in meiner Bibliothek",
            "RefSource": "0",
            "BibFormat": "BibTeX Export.ens",
            "export citations 2.x": "Speichern",
        },
    )
    r_export.raise_for_status()
    result = r_export.text

    if file:
        Path(file).write_text(result)
        result = None

    print("Done.")
    return result
