---
title: The package that never existed and got 30,000 downloads
description: In 2024 a researcher registered huggingface-cli, a name AI models kept recommending but which was never real. Three months later it had over 30,000 downloads — including from a major tech company's public documentation.
date: 2026-09-02
tags: slopsquatting, case study, supply chain
---

The clearest demonstration that slopsquatting works was not an attack. It was a researcher
proving a point, and the result was worse than most people expected.

## What happened

Bar Lanyado, a researcher at Lasso Security, noticed that AI coding assistants kept recommending
a Python package called `huggingface-cli`. The recommendation was plausible: Hugging Face is a
real and widely used platform, and plenty of tools ship a companion CLI package with exactly
that naming pattern.

The package did not exist. The real one is `huggingface_hub`.

So he registered `huggingface-cli` on PyPI as an empty placeholder — no functionality, no
payload, nothing but a claim on the name — and waited to see whether anyone would install
something that, until that moment, only existed inside a language model's output.

**In roughly three months it was downloaded more than 30,000 times.**

## The part that should worry you

Downloads alone could be explained away as scanners, mirrors and CI noise. The finding that
cannot be explained away is where the name turned up: in **public documentation and README
files belonging to large technology companies**, including one belonging to Alibaba.

That is the mechanism working end to end. Somebody asked a model how to do something. The model
invented a package. The developer copied the command into a README. The README was published.
Now the invented name has a citation — and the next developer who finds that README has every
reason to trust it, because it is on a real company's repository, not in a chat window.

The hallucination stopped being a model output and became documentation. At that point it
propagates without the model's help at all.

## Why an empty package is the dangerous version

Lanyado's package did nothing. That is what made it a demonstration rather than an incident.

A real attacker registering that same name has a `setup.py` that runs on install. Not on import
— **on install**. The victim does not have to call a single function or even successfully run
their program. `pip install -r requirements.txt` in a CI pipeline is enough, and CI pipelines
typically run with credentials that a laptop does not have: registry tokens, cloud roles,
deployment keys.

The uncomfortable arithmetic: the attacker does not need the victim to be careless. They need
one dependency file, in one repository, to contain a name that a machine invented and a human
did not verify.

## Why nothing caught it

Consider what the standard tooling would have seen at each stage.

| Stage | What a scanner sees | Result |
|---|---|---|
| Before registration | Name not in any vulnerability DB | Nothing to report |
| After registration, empty | New package, no CVE, no advisory | Nothing to report |
| After registration, malicious | Still no CVE until someone discovers and files one | Nothing to report |

At no point does a CVE-based scanner have anything to say, and the window between "attacker
registers the name" and "someone files an advisory" is exactly the window in which the attack
works. By the time there is a CVE, the compromise already happened somewhere.

The only check that fires *before* the package is registered is the one that asks whether the
name exists at all. That check would have flagged `huggingface-cli` on day zero — not because
it was known to be bad, but because it was not known to be anything.

## What to take from this

Three things this case establishes that were previously arguments rather than evidence:

1. **AI-invented package names reach production repositories.** Not hypothetically — they were
   found in the public documentation of companies with serious engineering organisations.
2. **The names persist and spread beyond the model.** Once a hallucinated command is copied into
   a README, an issue comment or a Stack Overflow answer, it has a life of its own.
3. **Registering the name is trivially cheap.** The barrier to becoming the owner of a name that
   thousands of developers will type is a free account and a few minutes.

The corresponding defence is equally unglamorous: verify that every dependency you are about to
add is a package that actually existed before your assistant mentioned it, and treat anything
recently published with near-zero adoption as unproven rather than fine.
