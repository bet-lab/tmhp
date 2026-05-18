# D3 v7 custom bundle

`d3.v7.custom.min.js` is a self-hosted cherry-pick of D3 v7 covering only
the modules used by the interactive docs layer. It exposes one global
`d3` symbol.

## Modules

The bundle uses **explicit named re-exports** rather than `export *`, so
Rollup's tree-shaker can drop unused d3-scale entry points (`scaleTime`,
`scaleUtc`) and their `d3-time` / `d3-time-format` transitive dependencies.
The d3-scale dependency is on **v4**; tree-shaking is what trims the bundle,
not the major-version pin (v3 has the same `d3-time` transitives).

Symbols re-exported, by source module:

- `d3-array`: `extent`, `max`, `bisector`
- `d3-axis`: `axisBottom`, `axisLeft`
- `d3-scale` (v4): `scaleLinear`, `scaleLog`, `scaleOrdinal`
- `d3-selection`: `select`, `selectAll`, `pointer`
- `d3-shape`: `line`, `area`, `curveCatmullRom`
- `d3-transition`: `transition`
- `d3-format`: `format`

`d3-color` and `d3-interpolate` are not directly re-exported; Rollup
still bundles the parts of them that d3-scale depends on internally. If
a future widget calls those symbols directly, add them to `entry.js`.

## Rebuilding

The build is documented in
`docs/superpowers/plans/2026-05-18-docs-interactive-ux.md` (Task 2,
Step 2). Re-run that recipe to regenerate when bumping D3.

## Why self-hosted

CDN-hosted JS adds an external network dependency that is not present
elsewhere in the published docs. See the design doc, §A.3.
