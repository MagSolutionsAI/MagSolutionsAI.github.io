---
title: "pull_request_target in the wild: 60 public workflows, 6 exploitable, and the fixes that actually work"
description: We checked 60 public GitHub Actions workflows that use pull_request_target. Most that look dangerous are not. One that explicitly declared its risk was, and our own rule missed it until today.
date: 2026-10-02
tags: security, github actions, ci, open source
---

`pull_request_target` is the GitHub Actions trigger behind a steady stream of
security advisories titled some variant of "secrets exfiltration via
pull_request_target". It runs in the context of the base repository, with its
secrets and a token that can write, even when the pull request comes from a
stranger's fork. On its own that is fine. It becomes a takeover when the
workflow also checks out the contributor's code **and runs it**.

We ship a rule for exactly that combination. Before trusting it, we measured it
on real public workflows: twice, two weeks apart. The results say more about the
fixes people use than about the bug.

## What makes it exploitable

Three ingredients, all of them needed:

1. the `pull_request_target` trigger;
2. a checkout of the pull request's own code (`ref: ${{ github.event.pull_request.head.sha }}` or `.head.ref`);
3. a step that **executes** that code: install scripts, a build, the test suite.

With all three, anyone who can open a pull request runs their code with your
token and secrets. Remove any one and the attack is gone.

## Measurement 1, 18 September 2026: our rule was wrong half the time

We sampled 30 public workflows that use `pull_request_target`. The rule fired on
15. On review, **8 of the 15 were false**:

- **7 used `environment:`**, the mitigation GitHub documents: the job waits for a
  human to approve it before any contributor code runs. Among them were
  dbt-labs and puppetlabs, who had it right and had commented it in their own
  files.
- **1 declared `allow-unsafe-pr-checkout: true`** and ran its scripts from a
  second, trusted checkout of the default branch kept in a separate folder
  (cpprefjp/site). The contributor's code is read as data, never executed.

Had we opened issues from that first run, we would have told seven well-known
projects they had a critical bug they did not have. We fixed the rule first.
After the fix it fired on 8; we confirmed 5 by hand and still judged 3 false.

## Measurement 2, 2 October 2026: a fresh sample, and our own miss

A new random sample of 30 public workflows, one per repository. **6 of them
check out the pull request's code.** Reading each one by hand:

- **3 never run it with privileges.** The privileged trigger only fires when the
  pull request is closed, the checkout is the base branch, or the head branch
  only appears in a concurrency group name.
- **2 are gated by a maintainer.** In ecmwf's cfgrib and thermofeel, a pull
  request from a fork only runs once a maintainer adds an `approved-for-ci`
  label.
- **1 is exploitable.** It checks out the pull request's code, runs `dotnet
  build` and the tests on it, and grants the token `contents: write` and
  `pull-requests: write`. Anyone who opens a pull request can push to that
  repository. We are not naming it.

That last one had written `allow-unsafe-pr-checkout: true`, and **our rule stayed
silent because of it.** After the cpprefjp case we had treated that line as a
mitigation. It is not one: `actions/checkout` v7 requires it precisely so that
you acknowledge the risk. Declaring a risk does not remove it. We fixed the rule
today: the declaration now only silences it when nothing is executed, or when
what runs comes from a trusted checkout of the base branch.

Across the two samples: **6 exploitable workflows out of 60 (10%)**, and roughly
as many that looked dangerous and were safe.

## The fixes we saw working in real repositories

- **Use `pull_request` instead.** If the job needs no secrets, the restricted
  context removes the problem entirely.
- **Gate the job behind an `environment:`** that requires approval (dbt-labs,
  puppetlabs).
- **Make fork pull requests wait for a maintainer label** (ecmwf).
- **Read the contributor's code, run your own.** Check out the base branch into
  a separate folder and execute only from there (cpprefjp/site).
- **Split it in two:** a `pull_request` workflow builds and uploads artifacts, and
  a `workflow_run` workflow with privileges consumes only those artifacts.

## Check your own repositories in one minute

```bash
grep -rln "pull_request_target" .github/workflows/
grep -rn "github.event.pull_request.head" .github/workflows/
```

If a file shows up in both, read what runs after the checkout. If it installs,
builds or tests the contributor's code, and there is no environment, no
maintainer gate and no separate trusted checkout, treat it as exposed: rotate
the secrets that workflow can reach and fix the trigger.

## What this doesn't tell you

Sixty workflows is a sample, not a census, and GitHub code search does not
return a uniform random slice of every repository. The 10% figure says that
the mistake is real and common enough to check for, not how common it is
across GitHub. We judged each case by reading the workflow, not by running an
exploit. Where a repository offers a private channel for vulnerability reports,
we use it; we do not publish who is exposed.
