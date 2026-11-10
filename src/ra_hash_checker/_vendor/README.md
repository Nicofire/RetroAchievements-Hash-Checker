# Vendored rcheevos

Source: [RetroAchievements/rcheevos](https://github.com/RetroAchievements/rcheevos)

Pinned commit: `eea6461f172d37d36b0d56568f13a505e0a9fd86`.

The upstream license is preserved unchanged in `rcheevos/LICENSE`.
Upstream headers, hash sources and the selected synthetic hash tests are unchanged.
Only the compatibility, core-hash, ROM, DISC, sector-reader and MD5 source units
are compiled. ROM and DISC are enabled; encrypted-content and ZIP-content hashing
are disabled. Arcade ZIP/7z filename hashing does not require ZIP-content support.
There is no runtime download and no Python reimplementation of upstream structs.

The small Python C bridge lives in `../native/bridge.c`. The optional CMake
`RA_BUILD_TESTS` target runs the upstream ROM, DISC, general hash and sector-reader
test suites with synthetic data, not commercial ROMs.

## Checking and Updating

Run the maintenance [script](../../../scripts/vendor_rcheevos.py) from the
repository root with Python 3.11+. It uses only the standard library, requires
internet access to GitHub, and is never run during application startup or builds.

```bash
python scripts/vendor_rcheevos.py --check
```

The default mode is also `--check`. It downloads the pinned upstream archive and
compares all 22 selected files, including the license and synthetic tests, without
writing anything. Only CRLF/LF line-ending differences are ignored, to accommodate
Git's Windows checkout conversion. Missing, changed, and unexpected local files
are reported individually. The Python `ENGINE_COMMIT` and this document's pin must
agree. Exit codes: `0` for a match, `1` for file differences, and `2` for invalid
arguments, inconsistent metadata, download failures, or invalid archives.

Both the original `src/rhash` / `test/rhash` layout and the newer
`src/hash` / `src/util` / `test/hash` layout are supported. The script selects a
fixed manifest from the archive layout; CMake selects the matching source paths.
Missing files still fail validation and are never silently skipped.

To update, replace `FULL_COMMIT_SHA` with an explicitly reviewed, full 40-character
upstream commit SHA. Branch names, tags, and abbreviated hashes are not accepted.

```bash
python scripts/vendor_rcheevos.py --update FULL_COMMIT_SHA
python scripts/vendor_rcheevos.py --check
```

Updating overwrites the selected files, including any local edits to them, and
updates both commit references. Review or save local edits before running it.
All selected archive entries are downloaded and validated before the first write;
unexpected local files stop the update and are never deleted automatically. The
script does not extract the whole archive or import upstream build files.
When switching layouts, it downloads both commits and removes obsolete files
only if they belong to the currently pinned manifest.

Review the resulting diff, rebuild the native extension, and run the Python and
upstream C tests described in [Development](../../../README.md#development).
Updates do not guarantee compatibility: new upstream dependencies may require
deliberate changes to the script's `FILES` / `MODERN_FILES` manifests and CMake.
