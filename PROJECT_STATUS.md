# Project Status

## Current phase

Release candidate verification completed on the current development machine.

## Completed

- Audited `PROJECT_GOAL.md` against inventory, date, mobile API, backup and build paths.
- Added strict shared date validation so invalid user-entered dates are rejected instead of silently becoming today.
- Added historical stock helpers in the database layer.
- Updated dispatch FEFO, manual lot selection, fund-source allocation and desktop preview to use stock as of the document date.
- Updated mobile purchase/dispatch API date validation.
- Added real HTTP handler tests for mobile auth, protected URLs, IP-bound tokens and invalid mobile dispatch dates.
- Added tokenized print URLs for mobile `window.open()` flows and verified protected print URLs through the real HTTP handler.
- Added release artifact verifier and UAT checklist.
- Added Windows GitHub Actions test workflow.
- Added formatted Excel export for the main XNT report tab.
- Improved negative-stock invariant messages with product, lot, fund source and balance.
- Improved Windows setup/build scripts.
- Built a Windows release folder at `dist/QuanLyKho`.

## Tests executed

- `.venv\Scripts\python.exe -m py_compile date_utils.py database.py server.py ui_dispatch.py ui_purchase.py`
- `.venv\Scripts\python.exe -m unittest -v test_fixes.py`
- `.venv\Scripts\python.exe -m py_compile ui.py test_fixes.py`
- `.venv\Scripts\python.exe -m compileall .`
- `.venv\Scripts\python.exe -c "import date_utils, database, server, ui_dispatch, ui_purchase, ui_temp_log; print('imports ok')"`
- `cmd /c setup.bat`
- `cmd /c "echo. | build.bat"`
- `.venv\Scripts\python.exe scripts\verify_release.py`

## Tests passing

- `test_fixes.py`: 28 tests passing.
- `compileall`: completed successfully.
- Import smoke test: completed successfully.
- Build: completed successfully after switching to onedir console bootloader.
- Release artifact verifier: completed successfully.

## Tests failing

- None in automated tests run in this environment.

## Build status

PASS. Output: `dist/QuanLyKho/QuanLyKho.exe`.

The latest build includes the formatted Excel export button for the main XNT report tab.

The release folder includes `docs/index.html`, visible `static/html5-qrcode.min.js`, and packaged `pyzbar/libzbar-64.dll`.

`scripts/verify_release.py` passed against `dist/QuanLyKho`.

## Remaining blockers

- Not verified on a clean Windows machine without Python.
- Not UAT-verified against a copied real production database.
- Current build uses `--console` because Windows Defender blocked PyInstaller GUI bootloader/resource embedding with WinError 225 on this machine.

## Next action

Run manual UAT on a copied database and test `dist/QuanLyKho` on one clean Windows workstation.
