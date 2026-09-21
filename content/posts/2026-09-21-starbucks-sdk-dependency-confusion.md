---
title: A package labelled itself "SECURITY RESEARCH." GitHub flagged it as malware anyway.
description: On 20 September 2026 someone published starbucks-sdk to npm, described it in the registry as a dependency-confusion proof of concept, and shipped a preinstall script that phones home. The advisory that followed didn't care about the label.
date: 2026-09-21
tags: supply chain, npm, case study, dependency confusion
---

On 20 September 2026, a single-version npm package called `starbucks-sdk` was published by a
maintainer whose npm username is `atulnagu123`. The package's own `description` field, visible to
anyone who queries the registry, reads:

```
SECURITY RESEARCH - Dependency Confusion PoC
```

The `author` field says `Security Researcher`. Less than a day later, GitHub's Advisory Database
published [GHSA-6m74-h462-fr23](https://github.com/advisories/GHSA-6m74-h462-fr23), classifying
`starbucks-sdk` as malware, credited to Amazon Inspector and the OpenSSF Package Analysis project.

The label didn't matter. The behaviour did.

## What dependency confusion is

Large organisations often depend on internal packages that live only on a private registry —
things named like `starbucks-sdk`, `internal-auth-lib`, or `acme-billing-utils`, never published
publicly. Dependency confusion is the trick of publishing a *public* package under that exact
name. If a build is misconfigured to check the public registry first, or a developer's local
config resolves the public name before the private one, the attacker's version installs instead
of the real one. Alex Birsan's original research on this technique, in 2021, got him bug bounties
from Apple, Microsoft, PayPal and dozens of other companies — by doing exactly this, safely,
against real corporate namespaces.

`starbucks-sdk` fits that shape: a plausible internal-sounding name at a company big enough to
have one, published by someone identifying as a researcher.

## What the package actually does

You don't need to trust an advisory summary to check this — the registry serves the full package
metadata, and the tarball, over plain HTTPS:

```bash
curl -s https://registry.npmjs.org/starbucks-sdk | jq '.time, .maintainers, .versions."1.0.0".description'
```

That returns one published version, one maintainer, created `2026-09-20T00:29:17Z`. Pulling the
tarball and reading `callback.js` — the file wired up as the package's `preinstall` script — shows
this:

```js
const info = {
    hostname: os.hostname(),
    user: os.userInfo().username,
    platform: os.platform(),
    cwd: process.cwd(),
    time: new Date().toISOString(),
    secrets: Object.keys(process.env).filter(k => /token|secret|key|pass|auth|api|aws/i.test(k)).slice(0,10)
};
```

That object — hostname, username, platform, working directory, and the **names** (not the values)
of up to ten environment variables matching a credential-shaped pattern — gets POSTed to the
Telegram Bot API, using a bot token and chat ID hardcoded directly in the file, the moment `npm
install` runs. No confirmation, no opt-out. The advisory's own description matches this exactly:
"install-time reconnaissance and exfiltration of installer/build-host identity and
credential-shaped environment variable names to an attacker-controlled Telegram channel."

One detail worth being precise about, because the advisory prose doesn't spell it out: the script
sends variable *names*, not their contents. A run on a host with `AWS_SECRET_ACCESS_KEY` set would
report that the key exists and is called that — not the key itself. That's reconnaissance, not a
completed credential theft. It still tells whoever is reading the Telegram channel exactly which
machines are worth attacking next, and by what name to ask for the secret.

## Why the "research" label didn't save it

OpenSSF's Package Analysis project and Amazon Inspector don't parse the `description` field for
disclaimers. They run the package, or sandbox its install scripts, and watch what happens:
outbound network calls to endpoints that aren't declared anywhere, environment enumeration,
process spawning. `starbucks-sdk` did all three of the things a real credential-stealer does. That
it also introduced itself as research changes the intent, not the behaviour — and every automated
scanner in this space, ours included, can only ever see the behaviour. A README is not a control.

This is worth sitting with if you assume "I'd recognise a proof of concept when I see one." You
wouldn't, not from the name, not from installing it, and in this case not even from the file that
was supposedly there to explain itself — the tarball ships no README at all
(`"readme":"ERROR: No README data found!"` in the registry response). The only place the
disclaimer exists is a metadata field nothing in the npm install path displays to you.

## Why this looks like the packages we check for

Strip away the "research" framing and the shape of `starbucks-sdk` is the same shape as a genuine
targeted attack: a single version, published hours before anyone looked at it, one maintainer with
no history, a name chosen to resemble something a specific company would plausibly use internally.
Age and adoption are exactly the two signals that are visible the moment a package like this lands
in a pull request — before any advisory exists to tell you it's bad, and, as this case shows,
regardless of whether the author ever meant harm.

## What this doesn't tell you

We don't know whether `atulnagu123` had any engagement or authorisation from Starbucks to test
their namespace, or whether this was an unsolicited scan of a name that seemed plausible. Birsan's
original research had explicit scope and disclosure agreements with each target; nothing in the
registry metadata or the advisory says whether this did. We don't know if the Telegram channel
received data from any real machine — the package could have sat unused, or been installed by
dozens of build systems, and the public record doesn't say which. And we don't know how many other
`*-sdk`-named dependency-confusion probes are sitting on the registry right now under a similar
"research" label, un-flagged, because nobody has run them yet. This is one advisory, for one
package, read the same day it was published.
