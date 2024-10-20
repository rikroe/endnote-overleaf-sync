import asyncio
import html
import json
import re
import time
from contextlib import closing
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
import websocket

RE_CSRF = re.compile(r'name=".*?csrf.*?" (?:content|value)="(.*?)"')
RE_PROJECTS = re.compile(r'<meta name="ol-prefetchedProjectsBlob".*?content="(.*?)">')


def parse_overleaf_folders(folder_list, parent: Optional[str] = None):
    """Recursively parsed through Overleaf folders.

    Returns dict[path, folder_id].
    """
    for folder in folder_list:
        curr_folder = folder["name"].replace("rootFolder", "")
        curr_path = (parent or "") + curr_folder + "/"
        yield (Path(curr_path), folder["_id"])
        yield from parse_overleaf_folders(folder["folders"], curr_path)


class OverleafCSRFAuth(httpx.Auth):
    """httpx.Auth to handle Overleaf CSRF tokens."""

    def __init__(self):
        self.csrf = None

    async def async_auth_flow(self, request: httpx.Request) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """Set CSRF token in request."""
        if self.csrf:
            request.headers.update({"x-csrf-token": self.csrf})

        response: httpx.Response = yield request
        await response.aread()

        if found_csrf := RE_CSRF.findall(response.text):
            self.csrf = found_csrf[0]


class OverleafClient(httpx.AsyncClient):
    """httpx.AsyncClient enhanced to handle Overleaf CSRF tokens."""

    def __init__(self, *args, **kwargs):
        kwargs["auth"] = OverleafCSRFAuth()
        super().__init__(*args, **kwargs)


async def upload(
    host: str,
    user: str,
    password: str,
    project: str,
    file: Path,
    folder: Optional[Path] = None,
    rename_to: Optional[str] = None,
):
    """Upload a file to an Overleaf project."""

    folder = (Path("/") / folder) if folder else Path("/")

    async with OverleafClient() as s:
        # GET login to get CSRF token
        _ = await s.get(f"{host}/login")

        # POST login to get cookie and get project data
        r_login = await s.post(
            f"{host}/login",
            json={"_csrf": s.auth.csrf, "email": user, "password": password},
            follow_redirects=True,
        )

        project_data = RE_PROJECTS.findall(r_login.text)[0]
        projects = {p["name"]: p["id"] for p in json.loads(html.unescape(project_data))["projects"]}
        project_id = projects[project]

        # GET websocket id (time-limited)
        r_ws = await s.get(f"{host}/socket.io/1/", params={"projectId": project_id, "t": time.time()})
        ws_id = r_ws.text.split(":")[0]

        # Get Folder list from Websocket
        with closing(
            websocket.create_connection(
                f'{host.replace("https", "wss")}/socket.io/1/websocket/{ws_id}?projectId={project_id}',
                header=[f"Cookies: overleaf.sid={s.cookies['overleaf.sid']}"],
                timeout=5,
            )
        ) as conn:
            while True:
                ws_data = conn.recv()
                if ws_data.startswith("5:"):
                    data = json.loads(ws_data[2:].strip(":"))["args"][0]["project"]
                    folders = dict(parse_overleaf_folders(data["rootFolder"]))
                    break

        # Finally, upload the file
        target_file_name = Path(file).name if not rename_to else rename_to
        r_upload = await s.post(
            f"{host}/project/{project_id}/upload",
            params={"folder_id": folders[folder]},
            data={
                "relativePath": "null",
                "name": target_file_name,
                "type": "application/octet-stream",
            },
            files={
                "qqfile": (target_file_name, open(file, "rb")),
            },
        )
        print(r_upload.text)


if __name__ == "__main__":
    from dotenv import dotenv_values

    config = dotenv_values(".env")
    asyncio.run(
        upload(
            host=config["OVERLEAF_HOST"],
            user=config["OVERLEAF_USER"],
            password=config["OVERLEAF_PASSWORD"],
            project=config["OVERLEAF_PROJECT"],
            file=Path("bibtex.bib"),
            rename_to="bibtex.bib",
        )
    )
