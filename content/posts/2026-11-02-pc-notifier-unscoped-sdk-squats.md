---
title: Drop the scope, keep the name: six packages squatting Axelar, Solana and OpenZeppelin SDKs in 48 hours
description: Between 1 and 2 November 2026, two npm accounts published axelarjs-sdk, wallet-adapter-base, sol-wallet-adapter and contracts-upgradeable — unscoped copies of real scoped SDK names, each running the same preinstall beacon. Three of the four still resolve to the malicious version today.
date: 2026-11-02
tags: supply chain, npm, case study, malware
---

Between 01:24 UTC on 1 November 2026 and 02:33 UTC on 2 November 2026, two npm accounts —
`cutekitten05` and `bigdevin55` — published a cluster of packages built around one idea: take a
real, scoped SDK name and republish it without the scope. [`axelarjs-sdk`](https://github.com/advisories/GHSA-69w5-x7cm-v78h)
copies `@axelar-network/axelarjs-sdk`. [`wallet-adapter-base`](https://github.com/advisories/GHSA-r89f-jjgp-3q97)
copies `@solana/wallet-adapter-base`. [`sol-wallet-adapter`](https://github.com/advisories/GHSA-j62h-2r3r-ggh9)
copies `@project-serum/sol-wallet-adapter`. [`contracts-upgradeable`](https://github.com/advisories/GHSA-v7f8-27g9-qx88)
copies `@openzeppelin/contracts-upgradeable`. GitHub's Advisory Database reviewed all four as
malware on 2 November, crediting the OpenSSF malicious-packages project (records MAL-2026-18456,
18459, 18452 and 18451).

The same accounts also published two packages under their own names —
[`cutekitten-test`](https://github.com/advisories/GHSA-pw4j-9v86-8c3g), whose README claims it is
"a security test package for a school project," and [`bigbob22-test`](https://github.com/advisories/GHSA-j2hf-rv9p-8jvr),
with an empty README. Every one of the six ships the identical script.

## One script, six names

Each advisory describes the same `CWE-506` behaviour: the package "has no functional code." A
`preinstall` script runs `node preinstall.js` during `npm install`, and the script sends the
machine's hostname, OS username and local time to a Discord webhook the advisories label "PC
Notifier." None of the six does anything else — no real SDK, no stub exports, nothing to make a
build keep working. If a project actually tries to import `axelarjs-sdk` expecting the Axelar
client, it breaks immediately; the only "feature" that reliably works is the beacon firing on
install.

That's a smaller ambition than campaigns that ship a working no-op shim to avoid crashing the
build. This one doesn't bother. Whoever is behind it isn't trying to stay resident in a dependency
tree — they just want the install to happen once.

## Checking the registry directly

The advisories give affected versions; the registry's own `time` and `dist-tags` fields show what
state each name is in right now:

```
$ curl -s https://registry.npmjs.org/wallet-adapter-base | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['time'])
print(d['dist-tags'])
"
{'created': '2026-11-01T21:32:11.699Z', 'modified': '2026-11-01T21:33:07.093Z',
 '0.0.0-stage': '2026-11-01T21:32:11.699Z', '1.0.0': '2026-11-01T21:33:06.920Z'}
{'latest': '1.0.0'}
```

`wallet-adapter-base` went from a stub to its only real release, `1.0.0` — the version the advisory
names as malicious — in under a minute, and `latest` still points there. Running the same query
against `sol-wallet-adapter` and `contracts-upgradeable` shows the same thing: `latest` resolves to
`1.0.7` and `1.0.0` respectively, both the versions the advisories flag. `npm install
wallet-adapter-base` today still pulls the beacon.

`axelarjs-sdk` is the exception. Its registry record now shows a single version, `0.0.0-stage`,
with a `created` timestamp of `2026-11-02T02:30:26Z` — after the account's original `1.0.1` release
the advisory describes. `cutekitten-test` and `bigbob22-test` show an `unpublished` block in their
`time` field instead of a current version at all. That's npm's usual pattern after a takedown: pull
the malicious release and leave an empty placeholder, or remove the name's history outright, rather
than simply flagging it. It also means "reviewed as malware" and "no longer installable" are two
different facts, and as of this writing only two of the six packages have both.

## Where this fits on the pull request

Nothing here depends on a misspelling. `axelarjs-sdk` isn't a typo of `@axelar-network/axelarjs-sdk`
— it's the same name with the scope removed, which is exactly the string a developer might type
from memory, or that an AI assistant might generate if it drops the scope while filling in an
import. The same is true for `wallet-adapter-base` against `@solana/wallet-adapter-base`. Neither
requires the attacker to guess anything; the real package's own name is the bait.

On a pull request that adds one of these as a dependency, that's two independent signals a check
can act on without knowing anything about Discord webhooks: a package name a few hours or days old
with no history, and a `preinstall` script that runs code before anything else in the project does.
That's what MagAudit marks as critical on the lockfile line — whether it would have stopped the
merge depends on whether the team has made the check required in their own branch protection
settings. A general-purpose AI reviewer reading the diff has little reason to flag it: `"wallet-adapter-base": "^1.0.0"`
is syntactically ordinary, and nothing about the line itself resolves against the registry.

## What this doesn't tell you

The advisories don't say who received the beacons, whether the Discord webhook had an audience
beyond its operator, or why a six-package campaign bothers squatting real SDK names at all when
the payload collects nothing more sensitive than a hostname and username — that's a long way from
the credential or session-token theft seen in other campaigns we've written about. We also don't
know whether `cutekitten05` and `bigdevin55` are the same person, or whether "security test package
for a school project" is a genuine excuse, a decoy, or an attempt to pre-empt exactly the kind of
writeup this is. We opened the four squat advisories and the two self-named ones directly; we
haven't independently confirmed the OpenSSF OSV records beyond what each GitHub advisory cites, and
we didn't attempt to resolve or contact the webhook endpoint.
