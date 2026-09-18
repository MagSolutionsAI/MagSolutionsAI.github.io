# Same pull request, two reviewers

This folder exists to answer one question with evidence instead of claims:
**given the exact same diff, what does each automated reviewer actually say?**

We run [MagAudit](https://github.com/apps/magaudit-agent). The comparison installs a
second reviewer — CodeRabbit — on this repository, so both see the same pull request at
the same moment, on identical input. CodeRabbit ran on its own defaults throughout; it
says so itself in both runs (`Configuration used: defaults`). We never touched its
settings, and that is the point: a comparison where we configure the other side is worth
nothing.

## The rule we set ourselves before running it

**The result gets published whatever it says.** It did not go our way in the parts that
matter most, and those parts are below with the rest.

---

## Round 1 — we designed the test wrong

Run on 2026-09-18 in [PR #2](https://github.com/MagSolutionsAI/MagSolutionsAI.github.io/pull/2).

Our result was published before the pull request was opened, and it held exactly: five
findings, none of the three reasoning bugs, none of the three false-positive baits.

CodeRabbit reported **"No actionable comments were generated"** — nothing at all.

On the face of it we won. We did not, and the reason is our fault.

The fixture documented itself. Its header announced that it was a deliberately
vulnerable benchmark file, and each bad line carried a comment saying `# WRONG:`.
CodeRabbit read that, understood it, and wrote back: *"intentionally vulnerable benchmark
examples only; they are not imported, executed, or deployed."* For a real pull request
that is the correct call. It declined to raise findings on a file that announced itself
as a test.

Our scanner fired anyway, because it does not read context — it matches patterns.

So round 1 measured something we had not intended to measure, and it is worth writing
down plainly: **CodeRabbit could tell a laboratory fixture from production code. We
could not.** Our workaround for that is asking the customer to maintain an exclusion
file by hand.

The walkthrough it produced also described all three reasoning bugs correctly — the
missing row lock, the integer fee, the value crossing from `settle` into the query —
so it clearly saw them and chose not to report them.

Round 1 is kept here rather than deleted. A benchmark that quietly drops its failed run
is not a benchmark.

---

## Round 2 — the one that counts

Run on 2026-09-18 in [PR #3](https://github.com/MagSolutionsAI/MagSolutionsAI.github.io/pull/3).

Same defects, rewritten with nothing to give them away: no `# WRONG` comments, no header
explaining the exercise, realistic docstrings, in an ordinary `scripts/` path, opened
with an ordinary pull request description.

The answer key was committed as a **SHA-256 hash first**
([`ronda-2.sha256`](ronda-2.sha256), commit `fb5e540`, twelve seconds before the pull
request was opened), so it could not be edited after either review arrived. The key is
now published in full: [`clave-ronda-2.md`](clave-ronda-2.md). Check it yourself:

```bash
sha256sum benchmark/clave-ronda-2.md   # must equal the hash in ronda-2.sha256
```

### What each reviewer found

| Planted defect | MagAudit | CodeRabbit |
|---|---|---|
| Hardcoded credential | ✅ | ❌ |
| `pickle.loads` on outside data | ✅ | ❌ |
| `shell=True` with an interpolated value | ✅ | ❌ |
| TLS verification disabled | ✅ | ✅ |
| SQL built from a variable | ✅ | ✅ |
| Double refund — check-then-write race | ❌ | ✅ |
| Fee truncated to zero by integer division | ❌ | ❌ |
| Three false-positive baits | 0 fired | 0 fired |

**5 of 8 for us, 3 of 8 for them, neither found the eighth.** Neither reviewer raised a
single false positive.

### What that actually means

**Where they beat us, they beat us on the thing we cannot do.** CodeRabbit found that
`refund()` reads a balance, checks it, then writes it with no transaction and no row
lock, so the same entry can be refunded twice. Every line of that function is correct
Python and correct SQL; there is no pattern to match. It also did not stop at the line
for the SQL finding — it followed the value out of `settle()` and into
`search_entries()` across function boundaries, then ran the query in a sandbox to
demonstrate the effect. Its verdict was `Merge Risk: High — can corrupt refund
balances`. That is a class of bug we do not detect and do not claim to.

**Where we beat them, we beat them on severity.** It did not raise the hardcoded
credential, the `pickle.loads`, or the `shell=True`. The last two are textbook remote
code execution.

**The bug neither of us found** is the fee calculation: `amount_cents * 29 // 10000`
floors, so any fee below one cent becomes zero. Across many small transactions that is
the entire margin. It is not a vulnerability and no pattern describes it. It has no
owner in this table, and we are not going to pretend otherwise.

### Asymmetry we have to declare

CodeRabbit could see our findings and we could not see its. Our check run publishes
annotations on the pull request, and CodeRabbit's comment quotes them directly under
`GitHub Check: MagAudit`. It also ran Ruff and OpenGrep. We ran on the diff alone.

This favours us in the read-across — its three findings were reached with our five
already visible, and it still declined to echo them — but it makes the two columns not
strictly comparable, and saying so is cheaper than being caught not saying it.

Other limitations, for completeness:

- The repository already contained this file describing the exercise, so a reviewer
  reading the whole repository could have reached it. The round 2 diff itself contained
  no hint.
- The round 2 pull request description stated nothing false, but deliberately withheld
  the framing. This note is the disclosure.
- One fixture, one language, one run each. This is an illustration of where the two
  tools differ in kind, not a statistical result. Do not read "5 vs 3" as a score.
- Neither pull request was merged. The vulnerable code never reached `main`.
- Timing, since it is measurable and people ask: MagAudit answered in 7 and 4 seconds;
  CodeRabbit in 3 min 44 s and 10 min 28 s. A pattern matcher and a language model doing
  different amounts of work — not a fault of either.

---

## The honest summary

They are not the same kind of tool and this is the clearest demonstration of it we can
produce.

CodeRabbit reasons about the code. It understands intent, follows values between
functions, spots logic that is wrong rather than merely dangerous, and stays quiet when
a file announces that it is a test. That is worth a great deal, and we cannot do it.

We match patterns, on the diff, in seconds, and we publish how often we are wrong. In
round 2 we caught three severe issues it did not raise, and in two rounds we produced
zero false positives on code built specifically to provoke them.

If you are choosing one, the useful question is not which scored higher on one file. It
is whether you want a reviewer that thinks about your code or a gate that will not miss
a committed credential. We are the second thing, we are free on public repositories, and
we would rather tell you that here than have you find out after installing.

## How the fixtures are chosen

Three kinds, deliberately:

**1. Things we expect to catch.** Patterns our rules cover, taken from behaviour we have
actually observed in public repositories — not invented to flatter us.

**2. Things we expect to miss.** A bug that needs following a value across functions. A
logic error that is perfectly valid code. **We cannot see these**, and a reviewer built
on a language model can. Leaving them out would rig the test.

**3. Correct code that looks wrong.** A PEM header quoted in a comment, a constant table
name interpolated into SQL, a parameterised query beside an injectable one. Nothing
should fire on these — this is where noise shows up, and noise is what makes teams
uninstall.

## What is not here

No real credentials, and no credential in a real provider's format either — not even a
fake one.

That second part is deliberate and it removes a category from the test. A string shaped
like a live Stripe or AWS key, pushed to a public repository, is picked up by GitHub's
own free secret scanning and forwarded to that provider for validation. It would cost
the provider a lookup and attach a public "leaked credential" signal to this repository,
which for someone selling credential detection would be a self-inflicted wound rather
than a measurement.

So the credential in the fixture has no provider prefix at all. It has to be caught on
entropy and context or not at all. **The easy half — `AKIA…`, `ghp_…`, `sk_live_…` — is
not tested here, and on a public repository GitHub already blocks it for free.** If that
is all you need, you do not need us for it.

Same rule as
[`evidence/`](https://github.com/MagSolutionsAI/MagSolutionsAI.github.io/tree/main/evidence).
Nothing in this folder is executed, imported or deployed.
