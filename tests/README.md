# Checks for the sales and saving fixes

Run these from the repository folder:

```sh
node tests/flash-sales.js
node tests/save-tabs.js
node tests/session-restore.js
node tests/sales-links.js
python -m pip install openpyxl
python tests/flash-export.py
```

- The app checks need Node.js. The spreadsheet check also needs Python and openpyxl.
- The checks use the code inside `index.html`, invented entries, and the historical sales files already in this repository. They do not connect to Supabase or change live records.
- The sales checks include $1 and $2 tickets, refunds, separate sales channels, and older feeds that label scheduled flash games as “Strips.” The August 4 example contains 360 advance-sale tickets worth $400.
- The spreadsheet check creates the actual Excel workbook and compares its advance sales and differences with the app. It checks older saved files too, and verifies that a shortage is reported as a failed check.
- The saving check opens independent copies of the app with shared browser storage. It delays one save, edits the other copy, and checks that recovering those edits cannot replace newer saved work without a warning.
- The remaining checks cover opening older nights without carrying over money, preserving current saved entries, and retaining each night's original sales links.

Build 264 contains five separately recorded fixes. The main app is still `index.html`; the test files are for checking changes and do not need to be loaded by the website.
