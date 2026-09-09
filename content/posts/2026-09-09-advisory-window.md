---
title: We measured how late a malware advisory arrives. Sometimes 95 days.
description: Across the 100 most recent npm malware advisories, 30% arrived more than a day after the package was published. 95% of those packages were under 30 days old when the advisory landed.
date: 2026-09-09
tags: security, supply chain, npm, measurement
---

Every dependency scanner that works from known vulnerabilities has the same blind
spot, and it is not a bug: **it cannot warn you about something nobody has
reported yet.** Between the moment an attacker publishes a malicious package and
the moment an advisory exists, every one of those tools reports the package as
fine, because from their point of view it genuinely is.

The interesting question is how long that window lasts. We could not find
anyone publishing the number, so we measured it.

## Method

We took the 100 most recent malware advisories for npm from the
[GitHub Advisory Database](https://github.com/advisories), pulled the affected
package name from each, and asked the npm registry when that package was first
published. The window is the difference between those two dates.

Both APIs are public. The whole measurement is two HTTP calls per advisory, and
you can reproduce it without our help:

```bash
# When did the advisory land?
gh api "advisories?type=malware&ecosystem=npm&per_page=100&sort=published&direction=desc"

# When was the package first published?
curl -s https://registry.npmjs.org/PACKAGE | jq -r '.time.created'
```

## What we found

| Measure | Value |
|---|---|
| Median window | **0 days** |
| Window longer than one day | **30% of advisories** |
| Longest window observed | **95 days** (`unifi-credential-server`) |
| Packages under 30 days old when the advisory landed | **95%** |

Four of the 100 packages had already been removed from the registry, so the
window could not be computed for those.

### The median is the good news

Most npm malware is flagged the same day it appears. GitHub's malware feed is
faster than we expected, and that deserves saying plainly — it is the part of
this that works.

### The tail is the problem

Thirty of the hundred sat on the registry for more than a full day. The worst,
`unifi-credential-server`, was available for **95 days**. During that time,
every CVE-based scanner in the world would have told you it was clean, and
every one of them would have been right by its own definition.

### The line that matters most

**95% of these packages were less than 30 days old when the advisory arrived.**

Read that together with the row above it. The signal that identifies these
packages is not a vulnerability record, which does not exist yet. It is that the
package is days old and almost nobody is using it — and both of those facts are
visible from the registry the instant the dependency appears in a pull request.

## What this does not mean

It does not mean advisory-based scanning is useless. Dependabot, Snyk and
GitHub's own tooling catch enormous amounts of real risk, including the 70% of
these cases where the advisory was effectively immediate.

It also does not mean age alone is a good signal. Most new packages are just new.
In our own weekly sweeps of public pull requests, a rule combining recent
publication with near-zero adoption fires on roughly **one in every 290**
dependencies that real developers add. Useful precisely because it is rare.

And it does not mean we are the only ones looking at this. [Socket](https://socket.dev)
built a whole company on behavioural analysis of packages, and they do more of it
than we do.

## Why we published the number that hurts

We also measure things that work against us. Across 1,778 dependencies added in
real public pull requests we found **zero** AI-hallucinated packages — the attack
much of this industry writes about, including us, is rarer than the headlines
suggest. A package that does not exist makes `pip install` fail and your CI go
red, for free, without anybody selling you anything.

We would rather be the vendor whose numbers you can check than the one whose
claims you have to take on faith. Both figures here are reproducible against
public APIs, and if you get a different answer we would like to know.
