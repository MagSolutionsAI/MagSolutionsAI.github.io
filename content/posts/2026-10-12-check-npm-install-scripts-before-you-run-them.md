---
title: How to read a package's install scripts before npm runs them
description: npm executes preinstall, install and postinstall scripts automatically — before you've looked at a single line of the package. The registry publishes those scripts in its own metadata, so you can read them without installing anything.
date: 2026-10-12
tags: how-to, npm, supply chain, security
---

You're about to add a dependency. Before `npm install` finishes, it may already have run
arbitrary JavaScript on your machine — not because the package is malicious, but because
that's how npm's install lifecycle works. [npm's own documentation](https://docs.npmjs.com/cli/v10/using-npm/scripts)
lists the order: `preinstall`, then `install`, then `postinstall`, all run after the package
lands in `node_modules` and before `npm install` returns control to you.

Most of the time that's harmless — a native module compiling itself, a CLI tool downloading
a binary. Sometimes it's the thing a dependency-confusion or typosquat package relies on:
the credential-stealing code we covered in [the Coinbase wallet cluster](/blog/coinbase-wallet-npm-cluster.html)
and in [starbucks-sdk](/blog/starbucks-sdk-dependency-confusion.html) both ran the moment
`npm install` finished, via a `postinstall` hook, with no further action from anyone.

The useful part: you don't need to run the install to see the scripts. The npm registry
stores the full `package.json` for every published version, scripts included, and serves it
as plain JSON.

## The command

```
curl -s https://registry.npmjs.org/<package> | \
  python3 -c "import json,sys; d=json.load(sys.stdin); v=d['dist-tags']['latest']; \
  print(d['versions'][v].get('scripts'))"
```

Run against five real packages, today:

```
$ curl -s https://registry.npmjs.org/left-pad | ...
None

$ curl -s https://registry.npmjs.org/husky | ...
None

$ curl -s https://registry.npmjs.org/puppeteer | ...
{'postinstall': 'node install.mjs', ...}

$ curl -s https://registry.npmjs.org/cypress | ...
{'postinstall': 'node dist/index.js --exec install', ...}

$ curl -s https://registry.npmjs.org/core-js | ...
{'postinstall': 'node -e "try{require(\'./postinstall\')}catch(e){}"'}
```

No install, no sandbox, no five minutes waiting for a tarball — one HTTP request per
package.

## Reading what the script actually does

A `postinstall` entry by itself tells you nothing about intent. All three packages above
run one, and all three are doing something ordinary.

Puppeteer's `install.mjs` [says exactly what it's for](https://unpkg.com/puppeteer@25.13.0/install.mjs)
in its own header comment: "the `puppeteer` package runs this script during the installation
process" to fetch a supported browser build. Cypress does the same for its own binary. Both
are well-known, well-documented reasons for a package to act during install — and both would
trip a rule that simply flags "has a postinstall script" as a finding, which is why that rule
on its own is not good enough.

Core-js is the clearer case for actually reading the file instead of guessing from the
command. [Its postinstall script](https://unpkg.com/core-js@3.50.0/postinstall.js) checks a
handful of environment variables — `CI`, `ADBLOCK`, `DISABLE_OPENCOLLECTIVE` — and, when none
of them are set, prints a one-time terminal banner asking for project funding, then writes a
marker file to `os.tmpdir()` so it won't repeat. No network call, no credential read, no file
outside `/tmp`. Unwelcome if you didn't expect it; not a threat.

Compare that to what you'd want to see from a script in a package you've never heard of,
published a few days ago: a request to an unfamiliar host, a read of `process.env` passed
anywhere outside `console.log`, or a write to a path like `~/.aws` or `~/.ssh`. None of that
appears in any of the five packages above — which is exactly the point of checking before you
install, not after.

## The same trick works on age

The registry's `time` field is in the same response, free of charge:

```
$ curl -s https://registry.npmjs.org/left-pad | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['time']['created'])"
2014-03-14T09:09:20.762Z
```

A package that's two days old with a `postinstall` script and a handful of downloads is a
different risk profile from one that's ten years old with a script that fetches a browser
binary and [11.4 million downloads in the last seven days](https://api.npmjs.org/downloads/point/last-week/puppeteer)
(checked 12 October 2026). Age and adoption don't prove safety, but a script on a brand-new,
unused name is worth five extra minutes that the same script on `puppeteer` is not.

## What this doesn't tell you

This technique reads what a script *says* it does in source form. It does not execute the
script in a sandbox, does not catch logic that only triggers under specific conditions, and
does not follow code the script downloads and runs afterward — a dropper that fetches its
real payload from a second URL at install time would still look ordinary from this check
alone. It also doesn't tell you anything about a dependency that's one level down: these five
packages are the ones you typed into `package.json` yourself, not the forty-odd others that
came along as transitive dependencies with their own scripts. And none of this is malware
analysis — it's reading source, not behaviour; a tool built to execute packages in isolation
and watch what they actually do, such as Socket, is answering a different and harder
question than the one this command answers.

If you want this check to run on every pull request instead of by hand, that's one of the
things a dependency-age-and-adoption check looks at automatically and flags in the PR.
