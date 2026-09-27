---
title: What is slopsquatting, and why your scanner cannot see it
description: Attackers no longer wait for you to mistype a package name. They register the names your AI assistant invents. Here is how the attack works and why CVE-based tooling is blind to it by design.
date: 2026-09-03
tags: slopsquatting, supply chain, AI security
---

A developer asks an AI assistant for code that uploads a file to an S3 bucket. The assistant
returns twelve confident lines, including an import of a helper library. The library sounds
plausible. It has the naming conventions of a real package. It does not exist.

Six months ago, that was a broken build and an annoyed developer. Today it can be a compromised
build server, because somebody registered that exact name and put an install script inside it.

That attack has a name now: **slopsquatting**.

## The difference from typosquatting

Typosquatting bets on human error. An attacker registers `reqeusts` and waits for someone to
fat-finger `requests`. It works, but it scales badly: the attacker is guessing at the space of
plausible typos, and most typos are never made.

Slopsquatting bets on machine error instead, and machine error turns out to be a much better
thing to bet on for one specific reason:

> Hallucinated package names repeat. Research measuring this found that a substantial share of
> invented names come back consistently when the same prompt is issued again — roughly 43% in the
> study that named the phenomenon. That reproducibility is the whole attack.

A typo is random. A hallucination is a *prediction* the model keeps making. An attacker does not
have to guess which invented name is worth registering — they can ask the model repeatedly,
write down what it invents, and register the names that keep coming back. The model then sends
them a stream of victims, for free, indefinitely.

## How common is this

**Correction — 27 September 2026.** An earlier version said the study examined "2.23 million code
samples" and that 19.7% of them contained a non-existent package. 2.23 million is the number of
package names, and 19.7% is the share of those names. It also multiplied that rate by pull
requests, which it does not describe. Both are corrected below.

The study that put numbers on it ([Spracklen et al., USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen))
generated 576,000 code samples with 16 models. Of the 2.23 million package names in them,
**19.7% did not exist** — an average of at least 5.2% for commercial models and 21.7% for
open-source ones. A [2026 measurement of frontier models](https://arxiv.org/abs/2605.17062) puts
the rate between 4.6% and 6.1%.

Note what that rate counts: package names a model suggests, not pull requests that reach you.
An invented dependency usually breaks `pip install` or `npm install` within a minute, so it
rarely survives to be committed. As of 27 September 2026 our own daily sweep of public pull
requests had confirmed none ([live count](https://api.magsolutionsai.com/measurement)). The
dangerous moment is earlier: when a developer or a coding agent runs the install command a model
suggested, and the name has already been registered by someone else. You need to be right every
time. The attacker needs you to be wrong once.

## Why the tools you already pay for miss it

This is the part that surprises people, and it is not a bug in those tools. It is what they are
for.

Snyk, Dependabot, `npm audit` and every other conventional dependency scanner answer one
question: *does this package have a known vulnerability?* To answer it, they look the package up
in a vulnerability database — CVEs, advisories, disclosure history.

A package name registered five minutes ago has:

- no CVE
- no advisory
- no disclosure history
- no download history to look suspicious against

So the scanner queries its database, finds nothing, and reports nothing. **Silence gets read as
safety.** The tool did its job correctly and told you nothing useful, because you asked it the
wrong question.

The right question is not "is this package known to be malicious?" It is "**does this package
exist at all, and if it does, has it existed for longer than this attack has?**"

## Existence is not enough either

Here is the trap in the obvious fix. If you just check whether a package exists, you catch the
easy case — the pure hallucination that nobody has claimed yet — and you miss the dangerous one.

A *claimed* slopsquat exists. It resolves. It installs. `pip` is perfectly happy. The registry
returns HTTP 200 and a version number.

What distinguishes it is not existence but **history**: it was published recently, it has
almost no adoption, and nothing depends on it. A package that has been on PyPI for six years
with millions of downloads is a different kind of object from one uploaded last Tuesday with
forty downloads, even though both return 200.

Any check worth running has to look at both.

## The reproducible version of this check

You do not need a vendor to verify existence. For Python:

```
curl -sI https://pypi.org/pypi/PACKAGE_NAME/json
```

HTTP 404 means the package does not exist. For npm:

```
curl -sI https://registry.npmjs.org/PACKAGE_NAME
```

That single fact — 404 or 200 — is not a heuristic, a model output or a confidence score. It is
an oracle. It cannot produce a false positive, because either the registry has the name or it
does not.

Then check the age and adoption of anything that does resolve. The full JSON response from PyPI
includes upload timestamps per release; anything published within the last 90 days with
negligible downloads deserves a human look before it reaches a build server.

## What this means in practice

The uncomfortable summary: the security tooling most teams rely on was designed for a world
where the packages in your manifest were chosen by a person who had heard of them. That
assumption quietly stopped being true, and nothing in the tool chain announced the change.

The check itself is cheap — one HTTP request per dependency. The hard part is doing it on every
pull request, before merge, without asking developers to remember.
