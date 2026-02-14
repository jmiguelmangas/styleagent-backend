# ADR-0001: MVP Scope — Capture One only

- Status: Accepted
- Date: 2026-02-14
- Owner: José Miguel Mangas

## Context
StyleAgent is intended to support multiple output targets (Capture One styles, Lightroom presets, DaVinci LUTs).  
For the first delivery we need a focused, shippable MVP that proves value and reduces complexity.

## Decision
The MVP will support **only Capture One** export, generating `.costyle` artifacts.

Out of scope for MVP:
- Lightroom presets
- DaVinci LUT generation
- PRO render / automation / CLI SDK integrations
- Authentication/billing (may be added later)
- Complex frontend UI (optional later)

## Rationale
- Capture One `.costyle` export is the most immediate value for the current workflow.
- Single target reduces risk and keeps architecture simpler.
- Establishes a solid abstraction (StyleSpec → artifact) for later targets.

## Consequences
- The backend data model and API must remain extensible to add targets later.
- Any “target-specific” logic must be isolated behind exporter modules.
- Future work: add additional exporters and target-specific schemas.

## Acceptance criteria (MVP)
- Create style + version with a stored StyleSpec
- Compile/export `.costyle` from the version
- Store and download artifact
- CI green with tests and lint
