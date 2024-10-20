import asyncio
from pathlib import Path
from typing import Optional

import httpx


async def export(user: str, password: str, file: Optional[str] = None):
    """Export all EndNote references in BibTex format."""

    # Create a session
    async with httpx.AsyncClient(follow_redirects=True) as s:
        s.headers.update(
            {
                "Upgrade-Insecure-Requests": "1",
                "Referer": f"https://access.clarivate.com/login?app=endnote&loginId={user}",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/111.0.0.0 Safari/537.36"
                ),
            }
        )

        # Login
        print("Logging in...")
        r_login_authorize = await s.post(
            "https://access.clarivate.com/api/authorize",
            json={
                "loginid": user,
                "password": password,
                "loginAccount": "",
                "app": "endnote",
            },
        )
        r_login_authorize.raise_for_status()

        r_login_redirect = await s.get(
            f"https://access.clarivate.com/api/session/endnote/{r_login_authorize.json()['code']}"
        )
        r_login_redirect.raise_for_status()

        r_login_cookie = await s.get(
            r_login_redirect.json()["enRedirectUrl"],
        )
        r_login_cookie.raise_for_status()

        # Export all references to Bibtex
        print("Exporting to BibTex...")
        s.headers["Referer"] = "https://www.myendnoteweb.com/EndNoteWeb.html?func=export%20citations&"
        r_export = await s.post(
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
            await asyncio.to_thread(Path(file).write_text, result)
            result = None

        print("Done.")
        return result


if __name__ == "__main__":
    from dotenv import dotenv_values

    config = dotenv_values(".env")
    asyncio.run(export(config["ENDNOTE_USER"], config["ENDNOTE_PASSWORD"], "bibtex_endnote.bib"))
