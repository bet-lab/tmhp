# D3 v7 custom bundle

`d3.v7.custom.min.js` is a self-hosted cherry-pick of D3 v7 covering only
the modules used by the interactive docs layer. It exposes one global
`d3` symbol.

## Modules

- d3-array, d3-axis, d3-color, d3-format, d3-interpolate
- d3-scale, d3-selection, d3-shape, d3-transition

## Rebuilding

The build is documented in
`docs/superpowers/plans/2026-05-18-docs-interactive-ux.md` (Task 2,
Step 2). Re-run that recipe to regenerate when bumping D3.

## Why self-hosted

CDN-hosted JS adds an external network dependency that is not present
elsewhere in the published docs. See the design doc, §A.3.
