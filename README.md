# ai-sdlc-pilot

A real, small product built end to end by [ai-sdlc](https://github.com/Shashank2577/ai-sdlc).

This repository exists to prove something the control plane could not prove about
itself: that it can build software that is **not** the control plane. Until this
repo existed, every capability ai-sdlc claimed — the deployment ladder, the QA
veto, the sign-off gate, engineering memory — had only ever run against a
repository with no runtime, no users and nothing to deploy. That is a degenerate
case, and four requirements read "satisfied" against it having never actually run.

## What it is

A small status page generator. It reads a plain-text list of services and their
last-known state, and renders a single self-contained HTML page. No framework, no
build step, no dependencies beyond the standard library — the point is to be real
enough to exercise a full lifecycle, not to be impressive.

Real means: it has tests that can fail, a deployable artifact, a definition of
done that blocks a merge, and a production gate that waits for a person.

## How work reaches this repository

Nobody commits here directly. Work items live in the control plane; a dispatched
agent session branches, commits with traceability trailers, and opens a pull
request here. The Definition of Done check runs in this repository and blocks a
merge that fails it.

See `CONVENTIONS.md` for the commit trailers every change carries.
