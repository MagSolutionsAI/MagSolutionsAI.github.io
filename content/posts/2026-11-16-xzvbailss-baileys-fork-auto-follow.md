---
title: A five-day-old fork of a real WhatsApp library, still live, that auto-follows a channel on every connection
description: @xzvbailss/baileys copies the real "baileys" WhatsApp Web library and quietly subscribes the installer's WhatsApp account to a hardcoded channel. GitHub reviewed three of its versions as malware on 16 November 2026; we checked the current release ourselves and the behaviour is still there.
date: 2026-11-16
tags: supply chain, npm, case study, malware
---

On 16 November 2026, GitHub's Advisory Database [reviewed `@xzvbailss/baileys`](https://github.com/advisories/GHSA-grg7-4c3w-pv5j)
as malware. The package is a fork of [Baileys](https://www.npmjs.com/package/baileys), the WebSocket
library most WhatsApp automation tools in Node.js are built on. The fork does what Baileys does —
and then, without telling the user, subscribes their WhatsApp account to a channel the publisher
picked.

The advisory credits OpenSSF's malicious-packages project, record `MAL-2026-19946`.

## What the real package looks like next to the fork

The comparison is the whole story. `baileys` (no scope) has existed since September 2022, has gone
through 64 published versions, is maintained under [`WhiskeySockets/Baileys`](https://github.com/WhiskeySockets/Baileys)
on GitHub, and its `registry.npmjs.org` record still lists that repository URL.

`@xzvbailss/baileys` was created on 11 November 2026 — five days before the advisory. Its
`package.json` `repository` field doesn't point to GitHub at all; it points to a Telegram handle,
`https://t.me/JustRxVz`. Its description is refreshingly candid for a malicious package: "hello I
am Rz, I am a student trying to develop a WhatsApp library via baileys and this is my baileys
xzvbailss." The same maintainer account, `justrxvz`, also owns an unscoped package called
`xzvbailss` — cited in the advisory as a separate malware record, `MAL-2026-18702`.

## What it does, by version

The advisory describes two behaviours, both triggered after a delay so they don't fire during a
quick test install:

- **Versions 1.0.0 and 5.0.0** (both published 11 November, a minute apart): a hardcoded channel
  ID triggers a `FOLLOW` query 2.5 minutes after the socket connects, retried every 5 seconds.
  Errors are swallowed silently.
- **Version 6.0.0** (published a few hours later the same day): the channel ID is now
  base64-encoded and decoded at load. The follow runs on every `connection.update` "open" event,
  after a 90-second delay, with failures logged only at debug level — quieter, and harder to spot
  by reading the diff.

The advisory lists only those three versions as affected. The registry shows six more releases
after them — `6.0.1` through `6.0.9`, all published within a few hours of each other on 13
November, two days after the advisory's sample and three days before it was reviewed.

## We checked the version that's live right now

So we pulled the tarball for `6.0.9`, the version `npm install @xzvbailss/baileys` would install
today, and looked for the behaviour ourselves. It's in `lib/Socket/newsletter.js`:

```js
// XzV Newsletter Auto-Follow: follow one configured newsletter after connection.
const newsletterAutoFollowId = config.newsletterAutoFollowId ?? '120363430764800148@newsletter';
const AUTO_FOLLOW_DELAY = 10_000;
const AUTO_FOLLOW_RETRY_DELAY = 20_000;
const AUTO_FOLLOW_MAX_ATTEMPTS = 3;
```

No base64 this time — the comment names exactly what the code does. A timer fires 10 seconds after
the socket opens, calls the same `FOLLOW` query ID the advisory describes, retries up to three
times 20 seconds apart, and skips itself quietly if the configured ID isn't a well-formed
newsletter JID. The hardcoded channel differs from the one the advisory quotes for `6.0.0`, which
tells us the operator changed the target at least once across the six patch releases — not that the
behaviour ever went away.

In short: GitHub's "affected versions" field is accurate for the versions it reviewed, but the
package kept shipping the same feature after that review window, and nothing currently stops
`npm install @xzvbailss/baileys` from pulling it.

## The family this sits in

The advisory ties `@xzvbailss/baileys` to two other records: `MAL-2026-17342`, a "PhantomSub"
pattern it says matches the same behaviour, and `MAL-2026-18873`, a different package,
`@poucode/baileys`, that the advisory says shares a byte-identical copy of the same `luxu.js` file.
We checked: `@poucode/baileys` exists, was created on 11 October 2026 — a month before the
`xzvbailss` fork — and is also still resolvable, currently at version `2.0.1`. We didn't go further
and compare the two packages' files ourselves; that claim is the advisory's, not something we
re-verified byte for byte.

## Where this fits on the pull request

There's no typo here and no install script. `@xzvbailss/baileys` isn't trying to look like
`baileys` by misspelling it — it's an entirely different, scoped package name, and nobody adds it
to a project by accident. The signal a check can act on isn't the name; it's that the package is
five days old with no history, forked from something 64 releases and four years deep, pointing at a
Telegram handle instead of a repository. That's exactly the "newly published, low-adoption
dependency" pattern MagAudit's check is built to flag on the pull request that adds the dependency
line — whether that stops the merge depends on whether the team has made the check required in
their own branch protection settings, the same as any other check on the PR. A general-purpose AI
reviewer reading `"@xzvbailss/baileys": "^6.0.9"` in a diff has nothing in the line itself to go on;
the age and the fork relationship only show up by querying the registry, which is what a dedicated
check is there to do.

## What this doesn't tell you

The advisory doesn't say what the followed channel publishes, how many accounts the auto-follow has
actually reached, or whether `justrxvz` controls the channel directly or is running this for someone
else. We don't know why the operator moved from a silent 2.5-minute delay to a candidly-commented
10-second one — confidence that reviewers wouldn't catch it, indifference, or simply sloppy
iteration. We didn't check versions `5.0.0` through `6.0.8` individually; our own verification
covers the advisory's description of `1.0.0`/`5.0.0`/`6.0.0` and our own read of `6.0.9`, nothing in
between. And we took the advisory's word for the shared `luxu.js` file with `@poucode/baileys`
rather than diffing the two packages ourselves.
