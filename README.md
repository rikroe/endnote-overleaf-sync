# Overleaf File Upload
A Python script to upload a file to an Overleaf instance by calling the public REST and Websocket APIs.

## Installation
For now, clone this repository and install the requirements from `requirements.txt`. This script requires Python>=3.7.

## Usage
Run with `python overleaf-upload.py`. See below for arguments.

```
Usage: overleaf-file-upload.py [OPTIONS]

  Upload a file to an Overleaf project.

Options:
  --host TEXT      URL (with https://) of your Overleaf instance  [required]
  --user TEXT      Overleaf username  [required]
  --password TEXT  Overleaf password  [required]
  --project TEXT   Project name (case sensitive)  [required]
  --file FILE      File to upload  [required]
  --folder PATH    Subfolder in project (case sensitive)
  --help           Show this message and exit.
```

After upload, the script will print the JSON response of the API (provided no HTTP exception occurred).

```jsonc
// success
{"success":true,"entity_id":"641f2cf7cc5b0c00a04b28e6","entity_type":"doc"}

// error
{"success":false}
```