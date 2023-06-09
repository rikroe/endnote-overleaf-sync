# Endnote to Overleaf sync
A collection of Python scripts to download a bibliography from EndNote, fix the file format and then bupload a file to an Overleaf instance.

## Installation
For now, clone this repository and install the requirements from `requirements.txt`. This script requires Python>=3.7.

## Usage
### Endnote
Run with `python endnote-cli.py`. See below for arguments.

```
Usage: endnote-cli.py export [OPTIONS]

  Export all EndNote refrences in BibTex format.

Options:
  --user TEXT      Endnote user  [required]
  --password TEXT  Password password  [required]
  --file FILE      Local Bibtex file
  --help           Show this message and exit.
```

```
Usage: endnote-cli.py parse [OPTIONS]

  Parse and homogenize a BibTex from Endnote.

Options:
  --input FILE            Local Bibtex file from Endnote
  --output FILE           Path for output file. Defaults to {input}_parsed.bib
  --remove-notes BOOLEAN  Clear notes field
  --help                  Show this message and exit.
```

### Overleaf upload
Run with `python overleaf-cli.py`. See below for arguments.

```
Usage: overleaf-cli.py [OPTIONS]

  Upload a file to an Overleaf project.

Options:
  --host TEXT       URL (with https://) of your Overleaf instance  [required]
  --user TEXT       Overleaf username  [required]
  --password TEXT   Overleaf password  [required]
  --project TEXT    Project name (case sensitive)  [required]
  --file FILE       File to upload  [required]
  --folder PATH     Subfolder in project (case sensitive)
  --rename-to TEXT  Rename file on Overleaf
  --help            Show this message and exit.
```

After upload, the script will print the JSON response of the API (provided no HTTP exception occurred).

```jsonc
// success
{"success":true,"entity_id":"641f2cf7cc5b0c00a04b28e6","entity_type":"doc"}

// error
{"success":false}
```