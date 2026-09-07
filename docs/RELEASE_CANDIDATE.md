# Release Candidate Checklist

This checklist defines the H3 release boundary for the Windows build of QuanLyKho.
The automated CI gates must be green before any manual acceptance or distribution.

## Automated gates

The Windows workflow must pass all of the following on the exact release head:

- install the pinned application dependencies on Python 3.10;
- run `pip-audit` with no known vulnerabilities in `requirements.txt`;
- run the complete unit/reliability/security test suite;
- compile all production, hardening, UI and test modules;
- launch the real desktop app from source through `ui_smoke_check.py`;
- build `dist/QuanLyKho` using `build_release.py`;
- fail the build if the offline QR asset, offline docs, `libzbar-64.dll` or `libiconv.dll` are missing;
- generate `RELEASE_INFO.json` and `SHA256SUMS.txt`;
- verify every file in the SHA-256 manifest;
- load the packaged zbar/iconv DLL pair on Windows;
- launch `QuanLyKho.exe` from the packaged directory with an isolated temporary `LOCALAPPDATA`;
- verify that the packaged app creates a SQLite database with the expected schema version and `PRAGMA integrity_check=ok`;
- terminate the packaged process, reopen the same per-user database with the packaged executable, and verify the database again;
- upload the exact tested `dist/QuanLyKho` directory as the CI release-candidate artifact on PRs and on `main`.

## Manual clean-Windows acceptance

Perform these checks on the exact CI artifact or an equivalent local build produced by the same `build_release.py` script. Use copied/non-production data until the release is accepted.

- Copy the whole `QuanLyKho` folder to a Windows machine that does not rely on the repository `.venv`.
- Start `QuanLyKho.exe` directly; Python/pip must not be required on the target workstation.
- Close and reopen the application; the same per-user database must load normally.
- Confirm offline help opens from the bundled `docs/index.html`.
- Confirm the camera/barcode workflow is available on a workstation with a supported camera/scanner.
- Create a test purchase with lot, expiry date and funding source.
- Dispatch stock by FEFO and confirm the earliest eligible non-expired lot is selected.
- Attempt to dispatch more than available stock and confirm the operation is rejected without partial writes.
- Run a known historical-stock lookup and compare it with source records.
- Create a manual backup, add a disposable test transaction, restore the backup and confirm the disposable transaction disappears.
- Run an XNT report and open both Excel and PDF output.
- Start the mobile LAN server on a trusted network, authenticate from a phone using the displayed PIN and verify a protected page cannot be opened from a fresh private session without authentication.
- Compare final stock by product, lot, expiry date and funding source against the copied source records.

## Release artifact integrity

- Keep the entire `QuanLyKho` directory together; do not distribute only `QuanLyKho.exe`.
- Archive `RELEASE_INFO.json` and `SHA256SUMS.txt` with the release.
- If any distributed file changes after the manifest was generated, rebuild the release rather than editing the artifact in place.
- Record the source Git commit SHA from `RELEASE_INFO.json` with the accepted release.

## Security boundary

- Mobile access remains plain HTTP and is intended only for a trusted local network; H1.1/H1.2 do not claim TLS transport security.
- Admin PIN/session controls protect application actions, but the Windows account/filesystem remains part of the trust boundary.
- Backup/restore and UAT should be performed on copied data until the exact release candidate has been accepted.

A release is considered an accepted Windows release candidate only when the automated gates are green on the exact source head and the applicable manual checks above have been completed on the packaged artifact.
