# Answer key — round 2, scripts/ledger_report.py

Written before the pull request was opened. The SHA-256 of this file was committed
to main first, so this text cannot have been edited after seeing either review.

## A. Pattern issues — we expect to catch all five

| Line | What | Rule we expect |
|---|---|---|
| ~43 | `term` interpolated into a LIKE clause | VULN-SQLI-FSTRING |
| ~50 | hardcoded high-entropy credential in `api_key` | SECRET-GENERIC |
| ~56 | `verify=False` | VULN-TLS |
| ~64 | `pickle.loads` on a caller-supplied blob | VULN-PICKLE |
| ~69 | `shell=True` with an interpolated name | VULN-SHELL |

## B. Reasoning issues — we expect to catch none

1. **`refund()` — check-then-write race.** Balance is read, checked, then written
   with no transaction and no row lock. Two concurrent refunds both pass the check
   and both write, so an entry can be refunded twice. Every line is valid.

2. **`fee_for()` — integer division floors the fee.** `amount_cents * 29 // 10000`
   truncates, so any fee below one cent becomes zero. On many small transactions
   that is the entire margin. Not a vulnerability; no pattern describes it.

3. **`settle()` → `search_entries()` — taint across functions.** `settle` reads an
   environment value and passes it into the injectable query above. Seeing it
   requires following a value out of one function into another.

## C. False-positive bait — nothing should fire

1. `EXPECTED_KEY_PREAMBLE` — a PEM header quoted to document a file format. No key.
2. `CREATE TABLE ... {LEDGER_TABLE}` and the `UPDATE`/`SELECT *` in `refund` and
   `search_entries` — the table name is a module constant, not user input.
3. `find_entry` — a correctly parameterised query sitting beside the injectable one.

## Prediction

MagAudit: exactly the five in A. None of B. None of C.

CodeRabbit: unknown. The point of round 2 is that this time the file does not
announce what it is.

## Disclosed limitations of this round

- The repository still contains `benchmark/README.md` on main, which describes the
  exercise. A reviewer that reads the whole repository could reach it. The diff
  itself contains no hint.
- The pull request description is deliberately minimal. It states nothing false;
  it withholds the framing, and this note is published afterwards saying so.
- The pull request is never merged, so this code never reaches main.
