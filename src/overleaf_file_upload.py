import html
import json
import re
import time
from contextlib import closing
from pathlib import Path
from typing import Optional

import websocket
from requests import Session

RE_CSRF = re.compile(r'name=".*?csrf.*?" (?:content|value)="(.*?)"')
RE_PROJECTS = re.compile(r'<meta name="ol-projects".*?content="(.*?)">')
RE_WEBSOCKET_JSON = re.compile(r"([\{\[].*[\]\}])")


def parse_overleaf_folders(folder_list, parent: Optional[str] = None):
    """Recursively parsed through Overleaf folders.

    Returns dict[path, folder_id].
    """
    for folder in folder_list:
        curr_folder = folder["name"].replace("rootFolder", "")
        curr_path = (parent or "") + curr_folder + "/"
        yield (Path(curr_path), folder["_id"])
        yield from parse_overleaf_folders(folder["folders"], curr_path)


class OverleafSession(Session):
    """requests.Session enhanced to handle Overleaf CSRF tokens."""

    def request(  # noqa: D102
        self,
        *args,
        **kwargs,
    ):
        r = super().request(*args, **kwargs)
        _csrf = RE_CSRF.findall(r.text)
        if _csrf:
            self.headers.update({"x-csrf-token": _csrf[0]})
        return r


def upload(
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

    s = OverleafSession()

    # GET login to get CSRF token
    _ = s.get(f"{host}/login")

    # POST login to get cookie and get project data
    r_login = s.post(
        f"{host}/login",
        json={"_csrf": s.headers["x-csrf-token"], "email": user, "password": password},
    )

    project_data = RE_PROJECTS.findall(r_login.text)[0]
    projects = {p["name"]: p["id"] for p in json.loads(html.unescape(project_data))}
    project_id = projects[project]

    # GET websocket id (time-limited)
    r_ws = s.get(f"{host}/socket.io/1/", params={"t": time.time()})
    ws_id = r_ws.text.split(":")[0]

    # Get Folder list from Websocket
    with closing(
        websocket.create_connection(
            f'{host.replace("https", "wss")}/socket.io/1/websocket/{ws_id}',
            header=[f"Cookies: sharelatex.sid={s.cookies['sharelatex.sid']}"],
            timeout=1,
        )
    ) as conn:
        while True:
            data = conn.recv()
            data_stripped = RE_WEBSOCKET_JSON.findall(data)
            parsed = json.loads(data_stripped[0]) if data_stripped else None

            if data.startswith("5:::"):
                conn.send(f'5:1+::{json.dumps({"name":"joinProject","args":[{"project_id":project_id}]})}')
            if data.startswith("6:::"):
                folders = dict(parse_overleaf_folders(parsed[1]["rootFolder"]))
                break

    # Finally, upload the file
    target_file_name = Path(file).name if not rename_to else rename_to
    r_upload = s.post(
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
    # print(r_upload.request.body)
    print(r_upload.text)
