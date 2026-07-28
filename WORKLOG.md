# Worklog

## 2026-07-28 22:25

### Files changed

- `date_utils.py`
- `database.py`
- `server.py`
- `ui.py`
- `ui_dispatch.py`
- `ui_purchase.py`
- `ui_temp_log.py`
- `test_fixes.py`
- `setup.bat`
- `run.bat`
- `build.bat`
- `PROJECT_STATUS.md`

### Root cause

Dispatch and desktop preview paths still calculated available stock from all stock movements instead of stock movements up to the document date. Date parsing also allowed invalid non-empty date strings to fall through or become today in some paths, which could create incorrect documents silently. The Windows developer scripts recreated or reinstalled dependencies too often and did not clearly distinguish missing Python Launcher from missing Python 3.10. PyInstaller one-file/windowed builds were blocked by Windows Defender on this machine.

### Fix implemented

- Introduced strict date normalization behavior for validation paths.
- Added database helpers for stock as of a reference date, available FEFO lots as of a date, and fund balances as of a date.
- Updated dispatch allocation to use historical stock and to keep the global negative-stock invariant.
- Updated desktop dispatch lot/fund/cart preview to call the same database helper logic.
- Added mobile API validation for purchase date, dispatch date and expiry date, returning HTTP 400 for invalid business input.
- Added clear UI error handling for invalid purchase, dispatch, report and temperature-log dates.
- Added `setup.bat`, made `run.bat` reuse setup, and made `build.bat` avoid reinstalling dependencies unless needed.
- Changed PyInstaller build to onedir console mode because Defender blocked onefile/windowed resource embedding.

### Commands executed

- `.venv\Scripts\python.exe -m py_compile date_utils.py database.py server.py ui_dispatch.py ui_purchase.py`
- `.venv\Scripts\python.exe -m unittest -v test_fixes.py`
- `.venv\Scripts\python.exe -m compileall .`
- `.venv\Scripts\python.exe -c "import date_utils, database, server, ui_dispatch, ui_purchase, ui_temp_log; print('imports ok')"`
- `cmd /c setup.bat`
- `git diff --check -- date_utils.py database.py server.py ui.py ui_dispatch.py ui_purchase.py ui_temp_log.py test_fixes.py run.bat build.bat setup.bat PROJECT_GOAL.md`
- `cmd /c "echo. | build.bat"`

### Results

- `test_fixes.py`: 23 tests run, 23 passed.
- `compileall`: passed.
- Import smoke test: passed.
- `setup.bat`: passed.
- First PyInstaller one-file/windowed attempt failed with WinError 225 from Windows Defender.
- Onedir/windowed attempt also failed with WinError 225.
- Onedir/console build passed and produced `dist/QuanLyKho/QuanLyKho.exe`.

### Remaining risks

- Build has a console window because Defender blocked the GUI bootloader in this environment.
- Clean-machine Windows execution is not verified here.
- Real-data UAT and inventory reconciliation still need to be performed with a copied database.

## 2026-07-28 22:35

### Files changed

- `server.py`
- `test_fixes.py`
- `.github/workflows/tests.yml`
- `PROJECT_STATUS.md`
- `WORKLOG.md`

### Root cause

Mobile authentication and invalid-date behavior had database-level tests and simplified token tests, but not enough evidence that the actual HTTP request handler enforced the same rules. Some mobile GET/POST endpoints also opened a `DB()` instance without an explicit close path.

### Fix implemented

- Added `finally` close handling for DB-backed mobile GET endpoints.
- Added date validation and DB close handling for mobile temperature logging.
- Added real local `HTTPServer` tests for `/api/auth`, protected URL rejection, invalid mobile dispatch date rejection, and IP-bound token invalidation.
- Added a Windows GitHub Actions workflow that installs dependencies, runs `unittest discover`, and compiles source files.

### Commands executed

- `.venv\Scripts\python.exe -m py_compile server.py test_fixes.py`
- `.venv\Scripts\python.exe -m unittest -v test_fixes.py`
- `.venv\Scripts\python.exe -m unittest discover -v`
- `.venv\Scripts\python.exe -m compileall date_utils.py database.py server.py ui.py ui_dispatch.py ui_purchase.py ui_temp_log.py test_fixes.py`
- `.venv\Scripts\python.exe -c "import date_utils, database, server, ui_dispatch, ui_purchase, ui_temp_log; print('imports ok')"`
- `cmd /c "echo. | build.bat"`

### Results

- `test_fixes.py`: 25 tests run, 25 passed.
- `unittest discover`: 25 tests run, 25 passed.
- Compile source files: passed.
- Import smoke test: passed.
- Build: passed and produced `dist/QuanLyKho/QuanLyKho.exe`.

### Remaining risks

- GitHub Actions workflow was added locally but has not run on GitHub in this environment.
- Clean-machine Windows execution remains unverified.
- Real-data UAT and inventory reconciliation still need to be performed with a copied database.

## 2026-07-28 22:45

### Files changed

- `server.py`
- `mobile_templates.py`
- `test_fixes.py`
- `scripts/verify_release.py`
- `UAT_CHECKLIST.md`
- `build.bat`
- `PROJECT_STATUS.md`
- `WORKLOG.md`

### Root cause

The mobile print preview URLs opened with `window.open()` relied on cookies for authentication. Cookies can work in the same browser session, but the project goal explicitly requires protected URLs opened by `window.open()` to carry a token. Release artifact checks were also manual instead of represented as a repeatable command.

### Fix implemented

- Server auth now accepts token from `Authorization`, cookie, or protected URL query string, while preserving IP binding and expiry checks.
- Mobile print `window.open()` URLs now call `withAuthToken(...)` and append the current token.
- Added tests proving print URLs reject missing auth and accept a valid query token.
- Added a template regression test so protected print URLs do not regress to raw `window.open(url)`.
- Added `scripts/verify_release.py` to validate the built release folder.
- Added `UAT_CHECKLIST.md` and copied it into release docs.

### Commands executed

- `.venv\Scripts\python.exe -m py_compile server.py mobile_templates.py test_fixes.py`
- `.venv\Scripts\python.exe -m unittest -v test_fixes.py`
- `.venv\Scripts\python.exe -m unittest discover -v`
- `.venv\Scripts\python.exe -m compileall date_utils.py database.py server.py mobile_templates.py ui.py ui_dispatch.py ui_purchase.py ui_temp_log.py test_fixes.py scripts\verify_release.py`
- `cmd /c "echo. | build.bat"`
- `.venv\Scripts\python.exe scripts\verify_release.py`

### Results

- `test_fixes.py`: 27 tests run, 27 passed.
- `unittest discover`: 27 tests run, 27 passed.
- Compile source files: passed.
- Build: passed and produced `dist/QuanLyKho/QuanLyKho.exe`.
- Release artifact verifier: passed.

### Remaining risks

- Clean-machine Windows execution is still not verified in this environment.
- Real-data UAT and inventory reconciliation still require a copied database and user-side run.
- Build remains onedir console mode because Defender blocked onefile/windowed bootloader generation.

## 2026-07-28 23:05

### Files changed

- `ui.py`
- `test_fixes.py`
- `PROJECT_STATUS.md`

### Fix implemented

- Added `Xuất Excel…` to the main `Báo cáo XNT` tab.
- The exported workbook includes title, date range, fund-source filter, DD-MM-YYYY dates, formatted quantity columns, frozen header row, autofilter, column widths and a total row.
- Added a regression test that exports a real XNT workbook and verifies the generated `.xlsx` contents.

### Commands executed

- `.venv\Scripts\python.exe -m py_compile ui.py`
- `.venv\Scripts\python.exe -m py_compile ui.py test_fixes.py`
- `.venv\Scripts\python.exe -m unittest -v test_fixes.py`
- `cmd /c "echo. | build.bat"`
- `.venv\Scripts\python.exe scripts\verify_release.py`

### Results

- `test_fixes.py`: 28 tests run, 28 passed.
- Build: passed and produced `dist/QuanLyKho/QuanLyKho.exe`.
- Release artifact verifier: passed.
