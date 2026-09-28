---
title: One dropper, five PyPI names — one of them a typosquat of a real Claude Code tool
description: On 27 September 2026, GitHub reviewed five PyPI malware advisories sharing one payload and one blockchain command server. One of the five, claudedashbord, is a one-letter-off copy of a real, published Claude Code dashboard tool.
date: 2026-09-28
tags: supply chain, PyPI, case study, malware
---

On 27 September 2026, GitHub's Advisory Database reviewed five PyPI packages as malware, all
published to the registry that same day, all tied to one campaign label —
[`2026-09-donutautosellsrc`](https://github.com/advisories/GHSA-28f3-pmhh-qxcm) — and all pointing
at the same final artefact and the same command-and-control address. One of the five names is
[`claudedashbord`](https://github.com/advisories/GHSA-28f3-pmhh-qxcm). A real package called
[`claude-dashboard`](https://pypi.org/project/claude-dashboard/) — "a real-time CLI dashboard for
Claude Code tool events," published once, on 30 December 2025, by a developer named Daniel
Ratmiroff — already existed on PyPI. Drop the hyphen and lose the "a" in "board" and you get the
malicious one.

## The five names

| Package | Advisory | Versions | Published |
|---|---|---|---|
| `claudedashbord` | [GHSA-28f3-pmhh-qxcm](https://github.com/advisories/GHSA-28f3-pmhh-qxcm) | 0.1.0–0.1.3 | 2026-09-27 |
| `donutautosellsrc` | [GHSA-2w77-qp99-3jvq](https://github.com/advisories/GHSA-2w77-qp99-3jvq) | 0.3.7–0.3.9 | 2026-09-27 |
| `donutpromotion` | [GHSA-c2rx-rjgw-p83h](https://github.com/advisories/GHSA-c2rx-rjgw-p83h) | 0.1.0 | 2026-09-27 |
| `coinscan` | [GHSA-78pg-cc9h-7rf3](https://github.com/advisories/GHSA-78pg-cc9h-7rf3) | 0.1.0 | 2026-09-27 |
| `aseity` | [GHSA-pvh9-pfxq-jq5q](https://github.com/advisories/GHSA-pvh9-pfxq-jq5q) | 0.1.0 | 2026-09-27 |

Only one of the five names imitates anything specific. `coinscan`, `donutpromotion` and `aseity`
sound like nothing in particular — generic enough to slip past a skim of a diff. `claudedashbord`
is the exception, and the underlying [OSV record](https://github.com/ossf/malicious-packages/blob/main/osv/malicious/pypi/claudedashbord/MAL-2026-17195.json)
says so directly. Amazon Inspector's write-up, one of two independent analyses attached to that
advisory, states it plainly: "the package name resembles 'Claude dashboard' and appears to be a
lure."

## What actually runs

The advisory pages summarise the payload as obfuscated code that fetches "code hidden in an
image," which sounds like classic steganography. The raw records behind the summary are more
specific, and slightly more mundane: `donutautosellsrc`'s `setup.py` downloads a PNG —
`https://thisisafalsepositive.st/cdn/v2/9f4e7a2c1b8d.png` — then looks for a ZIP local-file header
appended after the image data and extracts it. It's a PNG/ZIP polyglot, not pixel-level
steganography: the file is a valid image and a valid archive stitched together, which is enough to
survive being served from a path that looks like a CDN asset. The extracted archive spawns a
detached Python interpreter against `AppHost/main.py`. `claudedashbord`'s own loader is different
in the details — it drops a `.pth` file that CPython auto-runs on every interpreter startup, which
calls `claudedashbord.telemetry.check()` against a signed manifest on the same domain — but it
lands in the same place: code from `thisisafalsepositive.st` executing on the developer's machine,
not the CI runner.

Both write-ups describe timing and environment gates built to dodge automated analysis:
`claudedashbord` requires a `Documents` or `Downloads` directory to exist under the user's home
folder, waits twelve hours after first install before doing anything, and then throttles itself to
once every six hours. `donutautosellsrc` checks for the same directories and backs off if a
`DAS_STAGED` environment variable is set — the kind of variable a sandbox sets and a real
workstation doesn't. Both behaviours are aimed at the same target: a CI container that installs
and discards the package in seconds never sees the payload fire.

The eventual infostealer — described by a second researcher, Kamil Mańkowski (kam193), across all
five advisories — reads its command-and-control address from
[transaction history on the Polygon blockchain](https://polygonscan.com/address/0x9c0a507300fd902787bb193d80fca5ce6e1bff9a),
rather than a hardcoded domain. Four of the five advisories cite the identical
[VirusTotal hash](https://www.virustotal.com/gui/file/d03c42c275f0dbc617428441508c49ae1adcbbc95af4eeb094bca4e4f8943f3e/detection)
for that final artefact — the same binary, distributed under unrelated package names. A blockchain
address doesn't expire the way a seized domain does, and reading it at runtime means the operator
can point five different lures at a new server without touching any of the five packages again —
except that all five are already gone.

## The check that catches this after the fact

`claudedashbord` no longer resolves. `claude-dashboard` does:

```
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/claudedashbord/json
404
$ curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/claude-dashboard/json
200
```

That's the state today, after GitHub reviewed the report and PyPI pulled the package. It isn't a
check anyone could have run against `claudedashbord` on 27 September, before the advisory existed,
and get a useful answer — the package was live and installable right up until it wasn't. What a
same-day check would have caught is the shape of it: a name one edit-distance from a real,
low-download package, published for the first time that day, with no history behind it. That's a
weaker signal than a confirmed advisory, but it's available before the advisory is, which is the
entire gap this kind of campaign lives in.

## What this doesn't tell you

The advisories don't say how many times any of the five packages were downloaded before removal,
or whether anyone actually installed `claudedashbord` while looking for the real `claude-dashboard`
— we have no download-count source for either package and haven't found one. They don't say who
registered any of the five names, or whether `claudedashbord` was a deliberate, singular choice to
target Claude Code users specifically or one lure among several tried the same day, most of them
generic. The two research write-ups attached to `claudedashbord` and `donutautosellsrc` describe
different loader mechanics — a `.pth`-file auto-executor against a signed manifest in one, a
PNG/ZIP polyglot spawning a detached interpreter in the other — and the public record doesn't
reconcile whether that's two stages of one chain, two researchers each seeing a different version,
or genuinely different code paths that happen to converge on the same final payload. We're citing
both because both are in the primary sources, not because we can tell you which one is the full
picture.
