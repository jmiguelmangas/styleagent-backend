# ADR-0002: Capture One Export Strategy — Template patching

- Status: Accepted
- Date: 2026-02-14
- Owner: José Miguel Mangas

## Context
Capture One `.costyle` is an XML-like format. Generating valid files from scratch can be brittle across Capture One versions, because:
- root structure and attributes (e.g., Engine version) may vary
- some keys or ordering may be expected by the application
- the format includes tags beyond simple key/value entries

We need a robust approach for MVP.

## Decision
For MVP, the exporter will use a **template patching strategy**:
1) Start from a known-good baseline `.costyle` template
2) Parse entries (`<E K="..." V="..."/>`)
3) Overwrite only keys present in `StyleSpec.captureone.keys`
4) Apply SafePolicy removals (e.g., lens/WB keys)
5) Write back deterministically, preserving template order where possible

## Rationale
- Highest probability that Capture One will accept the output.
- Enables incremental adoption of additional keys without reverse-engineering full format.
- Keeps export deterministic and testable.

## Consequences
- A baseline template must exist:
  - stored in repo (default template), or
  - configurable later (user-provided template upload)
- The writer must preserve enough of the original structure for compatibility.
- Unit tests should focus on:
  - correct key patching
  - correct safe key removal
  - deterministic output (stable SHA-256)

## Alternatives considered
### A) Generate from scratch
- Pros: No dependency on a template file
- Cons: Higher risk of invalid files; more reverse engineering

### B) Use Capture One CLI/SDK
- Pros: likely most compatible
- Cons: increases operational complexity; out of MVP scope

## Safe policy link
Template patching must always apply the default SafePolicy:
- remove `LensLightFallOff`
- remove `WhiteBalance`, `WhiteBalanceTemperature`, `WhiteBalanceTint`
