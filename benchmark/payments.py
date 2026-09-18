"""Fixture for comparing automated reviewers. Not executed, not imported.

Contains, on purpose:
  - issues a pattern-based scanner should catch
  - issues only a reasoning reviewer can catch, which ours will miss
  - correct code that superficially looks wrong

Every credential-shaped string here is invented and matches no provider's format.
"""

import os
import pickle
import sqlite3
import subprocess

import requests

# The table name is a module constant. Nothing a user controls reaches the SQL
# below, so interpolating it is not injection. Should NOT fire.
LEDGER_TABLE = "ledger_entries"

# A PEM header quoted to document the format. There is no key here.
# "-----BEGIN RSA PRIVATE KEY-----..."
PEM_HEADER = "-----BEGIN RSA PRIVATE KEY-----"


def open_ledger(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    # Correct: constant table, user value parameterised. Should NOT fire.
    conn.execute(f"CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (id TEXT PRIMARY KEY, cents INTEGER)")
    return conn


def find_entry(conn: sqlite3.Connection, entry_id: str):
    # Correct: parameterised. Should NOT fire.
    return conn.execute(f"SELECT cents FROM {LEDGER_TABLE} WHERE id = ?", (entry_id,)).fetchone()


def search_entries(conn: sqlite3.Connection, term: str):
    # WRONG: the user's term goes straight into the SQL text.
    return conn.execute(f"SELECT * FROM {LEDGER_TABLE} WHERE memo LIKE '%{term}%'").fetchall()


def charge(amount_cents: int, token: str) -> dict:
    # WRONG: a credential committed to source. Deliberately in no provider's
    # format — see the README for why a real-format one is not in this file.
    api_key = "7f3Qb2Kx9Wm4Tz8Rn6Vp1Ly5Hc0Sd"
    # WRONG: TLS verification disabled.
    r = requests.post("https://api.example-psp.com/v1/charges",
                      json={"amount": amount_cents, "source": token},
                      headers={"Authorization": f"Bearer {api_key}"},
                      verify=False, timeout=20)
    return r.json()


def restore_session(blob: bytes):
    # WRONG: deserialising data that arrives from outside.
    return pickle.loads(blob)


def run_report(report_name: str):
    # WRONG: a shell built from a caller-supplied value.
    subprocess.run(f"python reports/{report_name}.py", shell=True, check=False)


# ── Below here: things a pattern cannot see ──────────────────────────────
#
# We expect to miss all three. A reviewer that reasons about the code should
# not. They are here so the comparison is honest.

def refund(conn: sqlite3.Connection, entry_id: str, cents: int) -> bool:
    """Refund an entry.

    The bug: the balance is read, then checked, then written — with no
    transaction and no row lock. Two concurrent refunds both pass the check and
    both write, so the same entry can be refunded twice. Every individual line
    is correct Python and correct SQL.
    """
    row = find_entry(conn, entry_id)
    if not row or row[0] < cents:
        return False
    conn.execute(f"UPDATE {LEDGER_TABLE} SET cents = cents - ? WHERE id = ?", (cents, entry_id))
    conn.commit()
    return True


def fee_for(amount_cents: int) -> int:
    """The bug: integer division floors, so any fee under one cent becomes
    zero. On a million small transactions that is the whole margin. Nothing
    here is a "vulnerability" and no pattern describes it."""
    return amount_cents * 29 // 10000 + 30


def settle(conn: sqlite3.Connection, entry_id: str) -> dict:
    """The bug crosses two functions: `search_entries` above accepts the raw
    term, and this passes a caller value into it. Seeing that requires
    following a value from one function into another — which is exactly what a
    single-line pattern cannot do."""
    memo = os.environ.get("SETTLEMENT_MEMO", "")
    matches = search_entries(conn, memo)
    return {"entry": entry_id, "matched": len(matches)}
