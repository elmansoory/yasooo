---
name: Excel import feature design
description: Key decisions and gotchas for the monthly Excel upload/import feature (roster/payments/attendance-grid parsing and DB diff/commit)
---

## Sheet classification, not filename/month matching
Classify each sheet by header shape (which columns exist, in what order) rather than
hardcoding month names or sheet titles. Real monthly files vary: some attendance grids
have a literal Off-ice/On-ice/Coach label row, others don't (detect dynamically per sheet).

**Why:** the club's exported files are hand-maintained and drift in small structural ways
month to month; hardcoding names/positions breaks on the next file the owner sends.

## Column-finder must not use `x or y` fallback chains
`_find_col(...) or _find_col(...)` silently breaks when a legitimately-matched column
index is `0` (falsy), e.g. a name column that happens to be the first column.
**How to apply:** always check `is not None` for anything that returns a column index/position,
never truthiness.

## Attendance-grid names must never auto-create members
Grid cells (e.g. bare first names in an "off-ice" column) are sometimes just a coach's
first name, not a real member. Only roster/payment sheet rows are allowed to create new
members; attendance-only names that don't match anyone become an "unmatched" list shown
to the user for manual review, never silently inserted.

## New members created in the same import must still match their own attendance rows
When building the diff/preview, the "already exists" lookup must include members staged
to be *created* in this same import (keyed by normalized name, with a null/placeholder id),
not just members already in the DB — otherwise attendance for a brand-new member gets
wrongly bucketed as "unmatched" and the owner has to upload the same file twice to get
their attendance recorded.

## Testing DB writes safely without touching the real SQLite file
When the app hardcodes a relative DB path (e.g. `sqlite3.connect('skating_database.db')`),
don't swap/overwrite that file while the live workflow might have it open. Instead, copy the
whole app+src tree into a scratch directory, `chdir` there, and run Streamlit's
`streamlit.testing.v1.AppTest` against the copy — full page-render and commit-flow testing
(including `FileUploader.upload(filename, bytes, mime_type)`) with zero risk to production data.
