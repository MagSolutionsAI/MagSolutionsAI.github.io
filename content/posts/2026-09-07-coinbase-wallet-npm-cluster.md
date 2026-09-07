---
title: Thirteen npm packages, 48 seconds, one fake wallet SDK
description: On 7 September 2026, GitHub's Advisory Database flagged 13 npm packages named after Coinbase's wallet infrastructure as malware. Registry timestamps show all 13 were published within 48 seconds of each other.
date: 2026-09-07
tags: supply chain, npm, case study, malware
---

On the morning of 7 September 2026, GitHub's Advisory Database published malware advisories for
13 npm packages, one after another: `base-account-core`, `base-app-data`, `scw-core`, `scw-mobile`,
`cb-wallet-env`, `cb-wallet-analytics`, `cb-wallet-data`, `cb-wallet-http`, `cb-wallet-metadata`,
`cb-wallet-solana-provider`, `cb-wallet-store`, `wallet-cds-web`, and `wallet-engine-signing`. Every
name reads like something you'd find inside a wallet product's internal toolchain — a core library,
a mobile variant, a Solana provider, a signing engine. None of them is a package anyone was
supposed to install.

## What the names are doing

Coinbase's actual wallet SDK is `@coinbase/wallet-sdk`, a scoped package that's been on npm since
March 2022. None of the 13 flagged packages use that scope, or any scope at all. What they share
instead is a naming convention — `cb-wallet-` prefixes, `scw-` prefixes (a plausible shorthand for
"smart contract wallet" or "smart wallet"), and `base-app-`/`base-account-` prefixes — that mimics
how a real company organises internal packages for a wallet product, without being any package
that company actually publishes.

That distinction matters more than it sounds. A typosquat depends on a developer mistyping a name
they already know. This is closer to guessing: if you were integrating wallet infrastructure and
saw `cb-wallet-http` or `wallet-engine-signing` suggested to you — by a teammate, a Stack Overflow
answer, or an AI assistant scaffolding an integration — nothing about the name looks wrong. It
looks like exactly the kind of internal-sounding dependency a larger SDK would split itself into.

Each advisory carries the same boilerplate GitHub uses across its malware reports, classified as
[CWE-506, embedded malicious code](https://github.com/advisories/GHSA-vgm8-2vf8-769j): "Any
computer that has this package installed or running should be considered fully compromised,"
with instructions to rotate all secrets and keys from a separate, uncompromised machine. None of
the 13 advisories names a researcher, a discovering organisation, or an attack narrative beyond
that template. That's normal for GitHub's malware feed — most entries are this terse — but it
means the interesting part isn't the advisory text. It's the registry data underneath it.

## Forty-eight seconds

Querying `registry.npmjs.org` for each package name returns a `time.created` field precise to the
millisecond. Lined up in order:

| Package | Created (UTC) |
|---|---|
| `base-account-core` | 04:54:59.919 |
| `base-app-data` | 04:55:04.459 |
| `cb-wallet-analytics` | 04:55:08.327 |
| `cb-wallet-data` | 04:55:12.500 |
| `cb-wallet-env` | 04:55:16.997 |
| `cb-wallet-http` | 04:55:20.821 |
| `cb-wallet-metadata` | 04:55:24.805 |
| `cb-wallet-solana-provider` | 04:55:28.754 |
| `cb-wallet-store` | 04:55:32.789 |
| `scw-core` | 04:55:36.704 |
| `scw-mobile` | 04:55:40.513 |
| `wallet-cds-web` | 04:55:44.436 |
| `wallet-engine-signing` | 04:55:48.234 |

Thirteen packages, published roughly four seconds apart, start to finish in 48.3 seconds. That
cadence is not a person running `npm publish` thirteen times. It's a script working through a
prepared list of names, and it's the kind of detail an advisory's prose never mentions because
it isn't in GitHub's data — it only shows up if you go and query the registry directly for each
name involved.

You can reproduce this yourself against any package:

```
curl -s https://registry.npmjs.org/scw-core | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d['time']['created'], list(d['versions']))"
```

Running it today against all 13 returns the same thing for each: a single version,
`0.0.1-security`, and an empty maintainers list. That's the registry's placeholder state after a
package is pulled — the original code is gone, but the name, and the creation timestamp, stay on
the record.

## Why a name-only check wouldn't have caught this in time

Every one of these 13 names is syntactically fine. None of them typosquats an existing package
character-for-character, so a Levenshtein-distance check against `@coinbase/wallet-sdk` wouldn't
flag `wallet-engine-signing` — it isn't close enough in spelling to trip that kind of comparison.
What connects the 13 is adoption and timing, not spelling: brand-new names, published in a tight
burst, with zero history, imitating an ecosystem's naming pattern rather than one specific
package's name.

That's the case for checking a dependency's registry metadata at the point you add it, not just
its spelling against a known-package list. A package published minutes or hours ago, with no
prior versions and no maintainer history, is a different risk category from one that's been
downloaded for years — regardless of how legitimate its name sounds. None of these 13 would have
shown up on a scanner that only compares names against a blocklist of known-bad strings, because
on the morning they were published, none of them was on any blocklist yet.

## What this doesn't tell you

GitHub's advisories don't say how the 13 packages were distributed, whether any of them were
pulled into a real build, or who published them — there's no credited researcher, no linked
writeup, and no campaign name grouping them together the way some GHSA entries do. The naming
pattern is our own observation from reading the list, not a claim GitHub makes; we don't know
whether the person behind it was specifically targeting Coinbase integrators or casting a wider
net with a name-generation script. The 48-second publishing window is exact, because it comes
straight from npm's own timestamps, but it tells you how the packages were published, not who
published them or why. Treat the mechanism as established and the motive as open.
