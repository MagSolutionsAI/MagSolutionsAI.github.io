---
title: How to check whether a package actually exists before you install it
description: A practical guide to verifying Python and npm dependencies against the live registries — the exact commands, what the responses mean, and the check most people forget after the first one passes.
date: 2026-09-01
tags: how-to, PyPI, npm, supply chain
---

Your assistant suggested a dependency. Before it reaches a build server, you want to know two
things: does this package exist, and has it existed long enough to be trustworthy? Both are
answerable in a few seconds, with no tooling beyond `curl`.

## Python: does the name resolve on PyPI

```
curl -sI https://pypi.org/pypi/requests/json
```

Read the status code:

| Status | Meaning |
|---|---|
| `200` | The package exists on PyPI |
| `404` | **The package does not exist.** Nothing is going to fix this at install time |
| `5xx` or timeout | PyPI is unreachable. Unverified — this is not the same as safe |

That third row matters more than it looks. When a registry check fails for network reasons, the
honest answer is "unknown", not "fine". Any tooling that silently downgrades an unreachable
registry to a pass is telling you something it does not know.

## npm: the same question

```
curl -sI https://registry.npmjs.org/express
```

Same reading of the status code. Note that scoped packages need URL encoding — `@scope/name`
becomes `@scope%2Fname`.

## The check people skip: how old is it

If the package resolves, you are not finished. A *claimed* slopsquat resolves perfectly — that
is the point of claiming it. What separates a real dependency from a freshly registered trap is
history, and history is in the full JSON response rather than the headers:

```
curl -s https://pypi.org/pypi/PACKAGE/json | python -m json.tool | head -40
```

Two fields are worth your attention:

- **The earliest `upload_time_iso_8601` across releases.** This is roughly when the name started
  existing. Days or weeks is a very different risk profile from years.
- **The release count and version history.** A package with one version, published recently, that
  nothing else depends on, is a package with no track record — whatever its contents.

For npm the equivalent lives in the `time` object of the registry response, with `created` giving
you the first publication.

There is no universal threshold, but a reasonable default: anything published in the **last 90
days with negligible adoption** is unproven and gets a human look before it enters a build.
That is not an accusation, it is a queue.

## Local and internal packages: the false positive to expect

If you script this check, one thing will bite you immediately: not every line in a requirements
file is a name that should resolve against a public registry.

```
-e .
./libs/internal-utils
git+https://github.com/yourorg/internal-lib.git
some-package @ file:///opt/wheels/some_package.whl
```

None of these are looked up on PyPI by `pip`. They are local paths, VCS references and direct
URLs. A naive checker queries the registry for `internal-utils`, gets a 404, and reports a
phantom dependency inside your own monorepo. In npm the equivalent protocols are `workspace:`,
`file:`, `link:` and `portal:`.

We learned this one in the field rather than in theory: a scan across public pull requests
produced exactly two "phantom" findings, and both turned out to be internal packages from the
same repository being installed by path. Any check that does not exclude these will cry wolf on
its first day in a real monorepo, and a scanner that cries wolf gets ignored — which is worse
than not having one.

## Doing this on every pull request

The manual version is fine for a dependency you are personally adding. It does not survive
contact with a team, because the failure mode is not "the check is hard", it is "nobody
remembers to run it at 6pm on a Friday".

That is the entire argument for automating it at the pull request boundary rather than in a
developer's terminal: the check has to happen where merging happens, not where good intentions
happen.
