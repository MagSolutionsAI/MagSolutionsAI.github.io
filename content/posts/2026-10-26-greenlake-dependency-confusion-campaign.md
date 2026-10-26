---
title: One npm account, 14 packages, four scopes: a dependency-confusion campaign built to look like someone's internal SDK
description: Between 23 and 25 October 2026, the npm account "wiseke" published 14 packages across four scopes, including @greenlake/auth and @sxm-web/client-sdk-core. GitHub reviewed all of them as malware the same week, days after the first one went live.
date: 2026-10-26
tags: supply chain, npm, case study, malware
---

Between 21:23 UTC on 23 October 2026 and 14:28 UTC on 25 October 2026, an npm account called
`wiseke` published 14 packages across four scopes: `@greenlake`, `@sxm-web`, `@drone-js-ext` and
`@ppa-web-components`. On 26 October, GitHub's Advisory Database reviewed all of them as malware,
including [`@greenlake/auth`](https://github.com/advisories/GHSA-pfqf-544g-rvp9),
[`@greenlake/context-pane`](https://github.com/advisories/GHSA-pmfr-35rg-27xm),
[`@greenlake/mfe-login-url`](https://github.com/advisories/GHSA-968q-w3j5-w6rq) and
[`@sxm-web/client-sdk-core`](https://github.com/advisories/GHSA-j5p5-hcm3-6gx9). Each advisory
describes the same package, published under a different scoped name.

Scoped names like `@greenlake/auth` or `@greenlake/mfe-login-url` read like the internal packages
of a real micro-frontend codebase — an auth module, a context pane, a login-URL helper for a
federated UI. That's the point of dependency confusion: if an organisation has an internal package
under a given scope and a build or CI step ever resolves that scope against the public registry
instead of (or before) the private one, npm installs whichever version is public — in this case,
one the attacker controls.

## What the advisories say it does

All four advisories describe identical behaviour, classified `CWE-506`, Embedded Malicious Code:

- The package calls itself a "Compatibility shim" and its README describes an "authorized
  dependency-confusion test" — a label the package itself supplies, not something GitHub verified.
- Each affected version ships a `postinstall` script running `node beacon.cjs`, and `index.js`
  runs the same code again on import.
- The code sends the machine's hostname, install path and current working directory over **plain
  HTTP** to `185.158.107.175:8787`.
- `index.js` exports a Proxy that returns no-op functions for everything, so a build that imports
  the package keeps compiling instead of throwing on a missing export — nothing crashes to draw
  attention to it.
- GitHub's advisories note that this `index.js` is byte-identical to `ph-common` (MAL-2026-1809),
  which beacons to the same IP and port — the same toolkit reused across more than one campaign.

Both `@sxm-web/client-sdk-core` and `@greenlake/context-pane` list a version string of `13.3.7` —
not a plausible result of normal semantic versioning, but a number chosen to look like a mature,
long-maintained package rather than something published an hour earlier.

## Checking the timeline against the registry directly

The advisories give a publication window; the registry's own `time` field confirms how fast the
first package in the batch went from created to malicious:

```
$ curl -s https://registry.npmjs.org/@greenlake/auth | python3 -c "
import json, sys
print(json.load(sys.stdin)['time'])
"
{'created': '2026-10-23T21:23:50.663Z', 'modified': '2026-10-23T21:26:05.976Z',
 '0.0.0-stage': '2026-10-23T21:23:50.663Z', '0.1.0': '2026-10-23T21:25:28.491Z',
 '3.0.0': '2026-10-23T21:26:05.660Z'}
```

`@greenlake/auth` went from its first stub version to the malicious `3.0.0` release in under three
minutes. The package has existed, in total, for less time than it would take to read its own
README.

Querying the registry today shows npm has already intervened on some of the names:

```
$ curl -s https://registry.npmjs.org/@greenlake/auth | python3 -c "
import json, sys
print(json.load(sys.stdin)['dist-tags'])
"
{'latest': '0.0.0-stage'}
```

`latest` now points back to the harmless stub version that was published first, which is how npm
quietly neutralises a scope without deleting the historical record the advisory refers to.
`@sxm-web/client-sdk-core` still resolves `latest` to `13.3.7` — the malicious version — at the
time of writing, which is a reminder that an advisory existing is not the same as a registry
already being clean.

## Where this fits on the pull request

Nothing about this campaign depends on a typo. The names aren't misspellings of real packages;
they're scopes an attacker is betting some organisation uses internally, published with inflated
version numbers to look established rather than new. That makes two of the signals a pull request
check can act on: a dependency that didn't exist a week ago, and a lockfile addition with no
matching entry in whatever private registry the scope is supposed to belong to. A `postinstall`
script that runs on every install is a third, independent of whether the name looks suspicious at
all.

On a pull request that adds one of these as a dependency, that's what MagAudit marks as critical,
with the file and line of the lockfile change — whether that would have stopped the merge depends
on whether the team made the check required in their own branch protection settings. It's also
exactly the kind of thing a general-purpose AI code reviewer, reading the diff for logic and style,
has no particular reason to flag: the new line in `package.json` is syntactically fine, and nothing
about `"@greenlake/auth": "^3.0.0"` looks wrong without checking the registry against it.

## What this doesn't tell you

The advisories don't say who, if anyone, actually installed these packages, so we don't know
whether the beacon ever fired against a real organisation's machine, or how many of the other ten
packages in the batch we haven't individually checked follow the identical pattern — we're
confident they do, based on GitHub's description of all 14 as one campaign, but we only opened the
four advisories above. We also don't know who operates `185.158.107.175`, whether `wiseke` is a
single person or a shared tooling account, or whether the real targets are the four named scopes or
unrelated organisations that happen to use similarly named internal packages. The "authorized
dependency-confusion test" label in the README is the account's own claim; nothing in the
advisories or the registry confirms or denies it, and a real authorised test wouldn't normally
need to hide its network calls behind a no-op Proxy.
