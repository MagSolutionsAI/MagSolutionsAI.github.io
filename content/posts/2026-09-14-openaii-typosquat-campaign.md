---
title: langgrap, openaii, transfomers, ollamaa — one typo each, one PyPI campaign
description: On 11 September 2026, GitHub reviewed four PyPI malware advisories in one batch, each a single-character typosquat of langgraph, openai, transformers or ollama. The payload includes code written to discourage analysis by AI coding agents.
date: 2026-09-14
tags: supply chain, PyPI, case study, malware
---

On 11 September 2026, GitHub's Advisory Database reviewed four PyPI malware
advisories together. The package names were `langgrap`, `openaii`,
`transfomers` and `ollamaa` — one character off `langgraph`, `openai`,
`transformers` and `ollama`, which is to say one character off four of the
most commonly imported libraries in an AI-adjacent Python project.

## The four packages

| Fake name | Real target | Claimed version | Advisory |
|---|---|---|---|
| `langgrap` | langgraph | 0.2.45 | [GHSA-crjm-2g45-pq97](https://github.com/advisories/GHSA-crjm-2g45-pq97) |
| `openaii` | openai | ≤ 1.55.3 | [GHSA-q5h5-h6mj-vhgv](https://github.com/advisories/GHSA-q5h5-h6mj-vhgv) |
| `transfomers` | transformers | 4.44.2 | [GHSA-2p95-qvc5-6rjq](https://github.com/advisories/GHSA-2p95-qvc5-6rjq) |
| `ollamaa` | ollama | 0.4.2 | [GHSA-9gv4-vfjg-jjrm](https://github.com/advisories/GHSA-9gv4-vfjg-jjrm) |

All four were reviewed the same day and grouped under the same campaign
label, `2026-09-openaii`. The version numbers are a small tell on their own:
`transfomers` claims to be version 4.44.2, but the real `transformers` on
PyPI is at 5.17.0 today, and the real `openai` client is at 3.13.0 against
`openaii`'s claimed 1.55.3. The fake packages were dressed as plausible
*older* releases, not current ones — version numbers a target might not
think to question.

## What the payload does

Each advisory describes the same mechanism: a malicious `.pth` file. A
`.pth` file is not an import — it runs the moment the Python interpreter
starts, for any script in that environment, whether or not anything ever
does `import openaii`. Simply having the package installed is enough.

Per the advisories, the chain from there is consistent across all four:

- downloads a further stage from a remote host
- exfiltrates SSH keys and cloud credentials
- plants cryptocurrency mining software
- installs a persistence mechanism so it survives a reboot
- clears logs to cover its tracks

And one line that's worth reading twice. The `openaii` advisory describes
the payload as including, verbatim, "a simple attempt to discourage
analysis via AI agents." The same phrase appears in the `langgrap`,
`transfomers` and `ollamaa` write-ups. The advisories don't say what the
evasion attempt actually looks like or which tools it targets — but the
authors clearly expected an AI coding assistant, not just a human, to be
one of the things reading the code before it ran.

## A second batch, the same day

The same review cycle also covered `aitextkit-py` and `aitextutils-py`
([GHSA-657v-53xv-3xw9](https://github.com/advisories/GHSA-657v-53xv-3xw9),
[GHSA-hm5j-9gw8-8568](https://github.com/advisories/GHSA-hm5j-9gw8-8568)),
a separate campaign (`2026-09-aitextkit-py`, credited to researcher kam193
via the OpenSSF Malicious Packages Project) using the same downloader
pattern but a different persistence mechanism — a systemd service named
`anymeetly-cameradriver`. Different names, different operator signature,
same day, same general idea: get a plausible-sounding package into an
AI-tooling-heavy install list.

Two unrelated campaigns landing on one day is not evidence of a wave — it's
two data points. We're not going to call it a trend from a sample of two.

## Typosquatting, not slopsquatting — worth being precise about

GitHub's own advisories describe all six packages as typosquatting, and
that's the accurate word here. Nothing in any of the six advisories says an
AI assistant invented these names — they read like ordinary fat-finger
targets (`transfomers`, `ollamaa`) aimed at anyone typing quickly, model or
human. Slopsquatting is the specific case where the name only exists because
a model hallucinated it. These advisories don't establish that, and we're
not going to borrow the more dramatic label just because it fits our own
product better.

What they do share with slopsquatting is the blind spot: none of the six
packages had a CVE or advisory before 11 September, so a scanner that only
checks known vulnerabilities would have reported all of them as clean, right
up until GitHub published. The signal that was available earlier is the one
[we measured two weeks ago](/blog/advisory-window.html): a
package that is very new and has almost no adoption. That's true of a
typosquat and a hallucinated name alike, which is why our own checks —
where we found zero AI-hallucinated package names across 1,778 dependencies
added in real pull requests — look at both.

## Checked first-hand

All four `2026-09-openaii` names are gone from the registry as of this
writing:

```
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/langgrap/json
404
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/openaii/json
404
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/transfomers/json
404
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/ollamaa/json
404
```

Removed and un-installable now. That's the system working, three days after
publication — not evidence of how long they were live before it.

## What this doesn't tell you

The advisories don't give install counts. PyPI's JSON API doesn't expose
download figures at all, and once a package is pulled there's no public
number to check retroactively — we can't tell you whether one person or
ten thousand installed any of these six before takedown.

They don't say which specific AI coding tools the "discourage analysis"
code targeted, or whether the attempt worked against any of them. That
detail simply isn't in the public advisory text.

They don't establish that the two 11 September campaigns share an operator.
Same day, same broad technique, different persistence mechanism and
different credited researcher — that's what the record actually shows, no
more.

And they don't tell you how a developer ended up typing `transfomers`
instead of `transformers` in the first place — copy-paste from a bad
tutorial, a typo in a hand-written `requirements.txt`, or a suggestion from
a tool that got it wrong. The advisories are silent on origin. We'd rather
say that plainly than guess at the more dramatic version.
