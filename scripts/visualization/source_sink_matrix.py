"""Generate the source/sink family matrix used by the TMHP docs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "source" / "_static" / "source_sink_matrix.svg"


SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 548"
     role="img" aria-labelledby="sourceSinkTitle sourceSinkDesc">
  <title id="sourceSinkTitle">TMHP released source and sink model families</title>
  <desc id="sourceSinkDesc">Released TMHP model classes reuse the same
  refrigerant-cycle core. ASHPB, GSHPB, and WSHPB expose domestic-hot-water
  tank boundaries; ASHP and GSHP expose space-conditioning boundaries with
  cooling selected by positive Q_r_iu and heating by negative Q_r_iu.</desc>
  <style><![CDATA[
    @media (prefers-color-scheme: dark) {
      .panel { fill: #0b1020 !important; stroke: #1e2740 !important; }
      .bg-rect { fill: #0b1020 !important; }
      .title { fill: #eef2f8 !important; }
      .subtitle { fill: #aab4c6 !important; }
      .footnote { fill: #9aa6ba !important; }
      .group-label { fill: #aab4c6 !important; }
      .group-sub { fill: #9aa6ba !important; }
      .src-wash { fill: rgba(251, 191, 36, 0.085) !important; }
      .snk-wash { fill: rgba(45, 212, 191, 0.075) !important; }
      .core-box { fill: #191f3c !important; stroke: #818cf8 !important; }
      .core-title { fill: #bcc4fc !important; }
      .core-sub { fill: #dfe3ff !important; }
      .source-box { fill: #34230f !important; stroke: #f6b34e !important; }
      .source-title { fill: #fbbf24 !important; }
      .source-sub { fill: #fcd9a8 !important; }
      .sink-box { fill: #0c2b29 !important; stroke: #2dd4bf !important; }
      .sink-title { fill: #5eead4 !important; }
      .sink-sub { fill: #b9f4ea !important; }
      .aux-box { fill: #271b46 !important; stroke: #b69bf3 !important; }
      .aux-title { fill: #cbb6fb !important; }
      .aux-sub { fill: #e7ddff !important; }
      .edge-label { fill: #aab4c6 !important; stroke: #0b1020 !important; }
    }
    text {
      font-family: "Inter", -apple-system, BlinkMacSystemFont,
                   "Helvetica Neue", Arial, sans-serif;
    }
    .title { font-size: 25px; font-weight: 700; fill: #0f172a;
             letter-spacing: -0.005em; }
    .subtitle { font-size: 13.5px; fill: #5b6878; }
    .footnote { font-size: 12.5px; fill: #64748b; }
    .group-label { font-size: 11.5px; font-weight: 700; letter-spacing: 0.12em;
                   fill: #5b6878; }
    .group-sub { font-size: 10.5px; font-weight: 500; letter-spacing: 0.02em;
                 fill: #64748b; }
    .box-title { font-size: 16.5px; font-weight: 700; }
    .box-sub { font-size: 11.5px; font-weight: 500; }
    .core-title { font-size: 17px; font-weight: 700; fill: #4f46e5; }
    .core-sub { font-size: 12px; font-weight: 500; fill: #3730a3;
                opacity: 0.92; }
    .edge-label { font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em;
                  fill: #5b6878; paint-order: stroke;
                  stroke: #ffffff; stroke-width: 4px;
                  stroke-linejoin: round; }
    .source-box { fill: #fff8ef; stroke: #f0a73c; stroke-width: 1.5; }
    .source-title { fill: #c2620e; }
    .source-sub { fill: #9a3412; }
    .sink-box { fill: #f0fdfa; stroke: #16b3a3; stroke-width: 1.5; }
    .sink-title { fill: #0f766e; }
    .sink-sub { fill: #115e59; }
    .aux-box { fill: #f6f4ff; stroke: #9d7af0; stroke-width: 1.5; }
    .aux-title { fill: #6d28d9; }
    .aux-sub { fill: #5b21b6; }
    .core-box { fill: #eef2ff; stroke: #6366f1; stroke-width: 1.5; }
    .panel { fill: #ffffff; stroke: #e7eaf0; stroke-width: 1.3; }
    .src-wash { fill: rgba(245, 158, 11, 0.055); }
    .snk-wash { fill: rgba(13, 148, 136, 0.055); }
    .divider { stroke: #6366f1; stroke-width: 1; opacity: 0.28; }
    .flow { fill: none; stroke-width: 2.1; stroke-linecap: round; }
    .flow-src { stroke: url(#gradSrc); marker-end: url(#arrowSrc); }
    .flow-snk { stroke: url(#gradSnk); marker-end: url(#arrowSnk); }
    .flow-aux { stroke: #9d7af0; stroke-width: 1.8;
                stroke-dasharray: 4 4; stroke-linecap: round;
                marker-end: url(#arrowAux); opacity: 0.95; }
    .cycle-glyph { fill: none; stroke: #4f46e5; stroke-width: 2.4;
                   stroke-linecap: round; }
    .cycle-tip { fill: #4f46e5; }
  ]]></style>
  <defs>
    <marker id="arrowSrc" viewBox="0 0 10 10" refX="7.2" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,1 L9,5 L0,9 z" fill="#6366f1"/>
    </marker>
    <marker id="arrowSnk" viewBox="0 0 10 10" refX="7.2" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,1 L9,5 L0,9 z" fill="#16b3a3"/>
    </marker>
    <marker id="arrowAux" viewBox="0 0 10 10" refX="7.2" refY="5"
            markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <path d="M0,1 L9,5 L0,9 z" fill="#9d7af0"/>
    </marker>
    <linearGradient id="gradSrc" x1="262" y1="0" x2="360" y2="0"
                    gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#f0a73c"/>
      <stop offset="1" stop-color="#6366f1"/>
    </linearGradient>
    <linearGradient id="gradSnk" x1="640" y1="0" x2="738" y2="0"
                    gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#6366f1"/>
      <stop offset="1" stop-color="#16b3a3"/>
    </linearGradient>
    <filter id="cardShadow" x="-12%" y="-18%" width="124%" height="140%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="3"
                    flood-color="#1e1b4b" flood-opacity="0.10"/>
    </filter>
    <filter id="coreShadow" x="-18%" y="-22%" width="136%" height="150%">
      <feDropShadow dx="0" dy="3" stdDeviation="6"
                    flood-color="#1e1b4b" flood-opacity="0.16"/>
    </filter>
  </defs>

  <rect class="bg-rect" width="1000" height="548" fill="#ffffff"/>

  <text class="title" x="500" y="50" text-anchor="middle">One refrigerant cycle, released source/sink families</text>
  <text class="subtitle" x="500" y="76" text-anchor="middle">Public classes expose DHW boilers for air, ground, and water; space-conditioning heat pumps for air and ground.</text>

  <!-- zone panels -->
  <rect class="panel" x="48" y="120" width="232" height="322" rx="20"/>
  <rect class="src-wash" x="48" y="120" width="232" height="322" rx="20"/>
  <rect class="panel" x="720" y="120" width="232" height="322" rx="20"/>
  <rect class="snk-wash" x="720" y="120" width="232" height="322" rx="20"/>
  <text class="group-label" x="164" y="150" text-anchor="middle">ENVIRONMENTAL SIDE</text>
  <text class="group-sub" x="164" y="168" text-anchor="middle">source side</text>
  <text class="group-label" x="836" y="150" text-anchor="middle">RELEASED DEMAND BOUNDARY</text>
  <text class="group-sub" x="836" y="168" text-anchor="middle">sink side</text>

  <!-- flow connectors: source -> core -> sink, terminating on the box edges -->
  <path class="flow flow-src" d="M262 227 C 312 232 332 270 360 270"/>
  <path class="flow flow-src" d="M262 303 C 300 303 332 303 360 303"/>
  <path class="flow flow-src" d="M262 379 C 312 374 332 336 360 336"/>
  <path class="flow flow-snk" d="M640 282 C 684 282 704 246 738 246"/>
  <path class="flow flow-snk" d="M640 324 C 684 324 704 360 738 360"/>
  <path class="flow flow-aux" d="M500 448 L500 405"/>

  <!-- interface labels, anchored on the zone seams / source flow -->
  <text class="edge-label" x="320" y="307" text-anchor="middle">source medium</text>
  <text class="edge-label" x="681" y="307" text-anchor="middle">class boundary</text>

  <!-- source family cards -->
  <g class="source">
    <rect class="source-box" fill="#fff8ef" stroke="#f0a73c" stroke-width="1.5" x="66" y="196" width="196" height="62" rx="13" filter="url(#cardShadow)"/>
    <text class="box-title source-title" fill="#c2620e" x="164" y="222" text-anchor="middle">Air</text>
    <text class="box-sub source-sub" fill="#9a3412" x="164" y="242" text-anchor="middle">ASHPB + ASHP</text>
    <rect class="source-box" fill="#fff8ef" stroke="#f0a73c" stroke-width="1.5" x="66" y="272" width="196" height="62" rx="13" filter="url(#cardShadow)"/>
    <text class="box-title source-title" fill="#c2620e" x="164" y="298" text-anchor="middle">Water</text>
    <text class="box-sub source-sub" fill="#9a3412" x="164" y="318" text-anchor="middle">WSHPB only</text>
    <rect class="source-box" fill="#fff8ef" stroke="#f0a73c" stroke-width="1.5" x="66" y="348" width="196" height="62" rx="13" filter="url(#cardShadow)"/>
    <text class="box-title source-title" fill="#c2620e" x="164" y="374" text-anchor="middle">Ground</text>
    <text class="box-sub source-sub" fill="#9a3412" x="164" y="394" text-anchor="middle">GSHPB + GSHP</text>
  </g>

  <!-- shared core (hero) -->
  <g class="core">
    <rect class="core-box" fill="#eef2ff" stroke="#6366f1" stroke-width="1.5" x="360" y="205" width="280" height="200" rx="16" filter="url(#coreShadow)"/>
    <g transform="translate(500 234) scale(1.18) translate(-500 -230)">
      <g class="cycle-glyph">
        <path d="M489.5 226 A 11 11 0 0 1 510.5 226"/>
        <path d="M510.5 234 A 11 11 0 0 1 489.5 234"/>
      </g>
      <path class="cycle-tip" d="M510.5 232 l 3.4 -5.2 l -6.6 0.4 z"/>
      <path class="cycle-tip" d="M489.5 228 l -3.4 5.2 l 6.6 -0.4 z"/>
    </g>
    <text class="core-title" fill="#4f46e5" x="500" y="270" text-anchor="middle">Shared refrigerant-cycle core</text>
    <line class="divider" stroke="#6366f1" stroke-width="1" opacity="0.28" x1="404" y1="284" x2="596" y2="284"/>
    <text class="core-sub" fill="#3730a3" x="500" y="308" text-anchor="middle">CoolProp state points</text>
    <text class="core-sub" fill="#3730a3" x="500" y="330" text-anchor="middle">compressor + heat exchangers</text>
    <text class="core-sub" fill="#3730a3" x="500" y="352" text-anchor="middle">cycle closure and diagnostics</text>
    <text class="core-sub" fill="#3730a3" x="500" y="374" text-anchor="middle">refrigerant swappable at runtime</text>
  </g>

  <!-- released demand boundary cards -->
  <g class="sink">
    <rect class="sink-box" fill="#f0fdfa" stroke="#16b3a3" stroke-width="1.5" x="738" y="196" width="196" height="100" rx="13" filter="url(#cardShadow)"/>
    <text class="box-title sink-title" fill="#0f766e" x="836" y="240" text-anchor="middle">DHW tank</text>
    <text class="box-sub sink-sub" fill="#115e59" x="836" y="262" text-anchor="middle">ASHPB &#183; GSHPB &#183; WSHPB</text>
    <rect class="sink-box" fill="#f0fdfa" stroke="#16b3a3" stroke-width="1.5" x="738" y="310" width="196" height="100" rx="13" filter="url(#cardShadow)"/>
    <text class="box-title sink-title" fill="#0f766e" x="836" y="344" text-anchor="middle">Space conditioning</text>
    <text class="box-sub sink-sub" fill="#115e59" x="836" y="366" text-anchor="middle">ASHP &#183; GSHP</text>
    <text class="box-sub sink-sub" fill="#115e59" x="836" y="386" text-anchor="middle">+ cooling &#183; &#8722; heating</text>
  </g>

  <!-- optional subsystems -->
  <g class="aux">
    <rect class="aux-box" fill="#f6f4ff" stroke="#9d7af0" stroke-width="1.5" x="350" y="448" width="300" height="56" rx="14" filter="url(#cardShadow)"/>
    <text class="box-title aux-title" fill="#6d28d9" x="500" y="474" text-anchor="middle" style="font-size:14.5px">Optional subsystems: STC, PV, ESS, UV</text>
    <text class="box-sub aux-sub" fill="#5b21b6" x="500" y="492" text-anchor="middle">augment the system without replacing the cycle core</text>
  </g>

  <text class="footnote" fill="#64748b" x="500" y="532" text-anchor="middle">Water-source space-conditioning is not a released public API in the current package.</text>
</svg>
"""


def main() -> None:
    OUT.write_text(SVG, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
