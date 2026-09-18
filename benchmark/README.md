# Same pull request, two reviewers

This folder exists to answer one question with evidence instead of claims:
**given the exact same diff, what does each automated reviewer actually say?**

We run [MagAudit](https://github.com/apps/magaudit-agent). The comparison runs a second
reviewer on the same repository, so both see every pull request opened here at the same
moment, on identical input. Nothing below is a result until a run is linked at the
bottom of this page — right now there are none.

## The rule we set ourselves before running it

**The result gets published whatever it says.** If CodeRabbit catches things we miss —
and it will, see below — that goes on the page with everything else. A benchmark you
only publish when you win is not a benchmark, it is an advertisement with a table in it.

## How the fixtures are chosen

Three kinds, deliberately:

**1. Things we expect to catch.** Patterns our rules cover, taken from behaviour we have
actually observed in public repositories — not invented to flatter us.

**2. Things we expect to miss.** A bug that needs following a value across two files. A
logic error that is perfectly valid code. A design decision that is wrong for reasons no
pattern can express. **We cannot see any of these**, and a reviewer built on a language
model can. Leaving them out would rig the test.

**3. Correct code that looks wrong.** A PEM header quoted in a comment. A parameterised
query whose table name is a module constant. A test fixture credential. Nothing should
fire on these — this is where noise shows up, and noise is what makes teams uninstall.

## What is not here

No real credentials, and no credential in a real provider's format either — not even a
fake one.

That second part is deliberate and worth explaining, because it removes a category from
the test. A string shaped like a live Stripe or AWS key, pushed to a public repository,
gets picked up by GitHub's own free secret scanning and forwarded to that provider for
validation. It would cost the provider a lookup, and it would attach a public
"leaked credential" signal to this repository — which, for someone selling credential
detection, would be a self-inflicted wound rather than a measurement.

So the credential in the fixture has no provider prefix at all. It has to be caught on
entropy and context or not at all, which is the harder half of the problem and the half
where scanners actually differ. **The easy half — `AKIA…`, `ghp_…`, `sk_live_…` — is
not tested here, and on a public repository GitHub already blocks it for free.** If
that is all you need, you do not need us for it.

Same rule as
[`evidence/`](https://github.com/MagSolutionsAI/MagSolutionsAI.github.io/tree/main/evidence).

Nothing in this folder is executed, imported or deployed. It is read by two bots and by
whoever wants to check what they said.

## Our own result, recorded before the comparison ran

Registering this first is the point. A prediction published in advance cannot be tuned
after seeing what the other reviewer found.

Run against `payments.py` on 2026-09-18, MagAudit reports **five findings** and nothing
else:

| Line | Rule | What |
|---|---|---|
| 41 | `VULN-SQLI-FSTRING` | HIGH — user term interpolated into SQL |
| 47 | `SECRET-GENERIC` | HIGH — hardcoded credential, caught on entropy |
| 58 | `VULN-PICKLE` | HIGH — deserialising outside data |
| 63 | `VULN-SHELL` | HIGH — shell built from a caller value |
| 52 | `VULN-TLS` | MEDIUM — certificate verification disabled |

What that list does **not** contain is the part worth reading:

- **The three reasoning bugs are all missed.** The double-refund race in `refund()`, the
  integer-division margin bug in `fee_for()`, the cross-function taint in `settle()`.
  Every line of all three is correct Python. We do not see any of them and we do not
  claim to.
- **The three false-positive baits are all silent**, which is the half we do care about:
  the quoted PEM header, the constant table name interpolated into SQL, and the
  parameterised query next to it. Zero of three fired.

That is the actual shape of the thing: narrow, and quiet inside its lane.

## Results

Each run links the pull request, so you can read both comments yourself rather than take
our summary of them.

_No side-by-side run yet — the first one will be linked here, whatever it says._
