# bin — personal script collection

- bin dir in my home folder

## Layout

The ~1.2k Python scripts are **folderized by functionality**: every script that does the
same job as another one lives in the same sub-directory (e.g. all Zstandard compressors in
`compress_zstd/`, all "strip comments from Python files" tools in `strip_comments_python/`,
all wheel repackers in `wheel_build_repack/`).

- 162 folders, 1234 scripts grouped.
- Scripts whose job is unique in the collection stay in the repo root
  (`fix_html_md_broken_links.py`, `gitignore_updater.py`, `rm_from_archive.py`,
  `update_summary.py`) — no folder is created for a single member.
- The old extension-less symlinks that mirrored each `*.py` name
  (`20most -> .../bin/20most.py`) were removed; they pointed at absolute Termux paths and
  were broken duplicates of the script names.

Full folder → script listing: **[SCRIPT_INDEX.md](SCRIPT_INDEX.md)**

Folders are sorted by size in that index, so the biggest clusters (the ones with the most
overlap / near-duplicates) come first.
