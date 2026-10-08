# Operator directory checkpoint — 9 October 2026

Upstream main: 798b77fa1ecfd5469a9df30945f496db3105d0dd, exact tree ddb85a1ab1af426ef0415aed77919ba9eb990a1c.

The 3D scene, continuous wheel zoom, worldwide OSM catalog and six references are already merged (#15–#17); do not restart them.

Checkpoint 1: registered primary-directory parser, fixed-URL robots-aware acquisition and permanent weekly candidate workflow. Ten local parser tests pass. No new directory data has been published yet. The capture workflow writes only a review artifact, never main, and fails closed on schema changes, duplicate codes or empty output. Service coverage is not operating load or available inventory.

Next runnable steps: inspect the first capture artifact, compare extracted rows against the official Equinix colocation availability table, add an explicitly reviewed dated publication, then integrate a searchable operator-directory desk and proposed map matches. Unmatched directory entries must remain visible without fabricated coordinates. Do not add directory-code counts to OSM feature counts. Run fresh backend and Chromium suites, inspect screenshots, and require independent PR CI before merge.
