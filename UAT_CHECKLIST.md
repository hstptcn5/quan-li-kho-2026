# UAT Checklist

Use this checklist on a copied database and one clean Windows workstation.

## Clean Machine

- Copy the whole `dist/QuanLyKho` folder.
- Confirm the target machine does not need Python, pip or a virtual environment.
- Run `QuanLyKho.exe`.
- Confirm the application opens and the database status bar is visible.
- Confirm `Trợ giúp > Hướng dẫn sử dụng` opens `docs/index.html`.

## Inventory Accuracy

- Create or use a copied product with two batches and two fund sources.
- Purchase stock dated before the dispatch date.
- Dispatch by FEFO and confirm the earliest non-expired batch is selected.
- Dispatch manually from one fund source and confirm the other source is unchanged.
- Try dispatching more than available stock and confirm it is rejected.

## Historical Stock

- Purchase 10 units on `01-01-2026`.
- Dispatch 4 units on `01-02-2026`.
- Check stock as of `22-01-2026`; it should still show 10 units.
- Try to dispatch stock dated before its purchase date and confirm it is rejected.

## Mobile

- Start the mobile server.
- Log in with the displayed PIN.
- Search a product and open the print preview.
- Confirm printed/preview URLs open after login.
- Try opening a print URL without login in a private browser tab and confirm it is rejected.

## Backup And Restore

- Create a manual backup.
- Add one test product or transaction.
- Restore the backup.
- Confirm the test product or transaction is gone.
- Confirm the app still queries stock and reports after restore.

## Reports

- Run XNT report for a known month.
- Open advanced report note details.
- Export the report file and confirm it opens.

## Acceptance

- Compare total stock by product, batch, expiry date and fund source against the copied source records.
- Record any mismatch with product name, batch, fund source, software stock and expected stock.
