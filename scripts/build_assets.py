"""Gera os SVGs desktop/intermediário/mobile e o painel de uso a partir do agregado.

Uso:
  python scripts/build_assets.py                 regenera os SVGs
  python scripts/build_assets.py --check         confere SVGs e textos alternativos do README
Os banners são vetoriais, sem foto embutida ou arquivo de imagem auxiliar.
O GitHub serve os SVGs com `default-src 'none'; style-src 'unsafe-inline'; sandbox`, então
nada aqui pode depender de fontes, scripts ou recursos externos.
"""

import argparse
import re
import subprocess
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
MAX_BYTES = 100_000

# Tokens do design system, extraídos do banner (zinc do shadcn). Cada SVG é um cartão
# escuro e opaco: o mesmo arquivo serve aos temas claro e escuro do GitHub.
COLOR = {
    "background": "#09090b",
    "card": "#18181b",
    "border": "#27272a",
    "ring": "#3f3f46",
    "line": "#52525b",
    "subtle": "#71717a",  # só decoração; 4,12:1 sobre o fundo
    "muted": "#a1a1aa",  # texto secundário; 7,76:1
    "signal": "#d4d4d8",
    "foreground": "#fafafa",
}
SANS = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
MATH = '"Cambria Math", "STIX Two Math", "Latin Modern Math", "Times New Roman", Times, serif'
RADIUS = 24
GRID = 24

# Textos: a mesma frase vai para o SVG e para o alt do README.
BANNER_ALT = ("Jordy Fontoura: AI Engineer working with RAG, agents and MCP; "
              "software developer since 2018; TypeScript, Python and Rust")
FOCUS_ALT = ("What I build: retrieval (RAG, pgvector), LLMs (Vercel AI SDK), "
             "tools (tool calling, MCP) and conversational agents")
STAGES = [
    # (rótulo, detalhe, fórmula decorativa)
    ("Retrieval", "RAG · pgvector", "sim(q, d)"),
    ("LLMs", "Vercel AI SDK", "p(y | x)"),
    ("Tools", "tool calling · MCP", "f(args)"),
    ("Agents", "conversational", "π(a | s)"),
]


def style(extra=""):
    return f"""  <style>
    .title {{ font: 700 64px {SANS}; fill: {COLOR["foreground"]}; letter-spacing: -1.5px; }}
    .lead {{ font: 400 32px {SANS}; fill: {COLOR["signal"]}; }}
    .meta {{ font: 500 24px {SANS}; fill: {COLOR["muted"]}; }}
    .eq {{ font-family: {MATH}; font-style: italic; fill: {COLOR["subtle"]}; fill-opacity: 0.75; }}
    .flow {{ fill: none; stroke: url(#flowfade); stroke-width: 1; }}
    .ring {{ fill: none; stroke: {COLOR["border"]}; stroke-width: 1; }}
    .edge {{ stroke: {COLOR["ring"]}; stroke-width: 1; stroke-opacity: 0.8; }}
    .node {{ fill: {COLOR["background"]}; stroke: {COLOR["subtle"]}; stroke-width: 1.5; }}
    .signal {{ fill: none; stroke: {COLOR["signal"]}; stroke-width: 1.5; stroke-opacity: 0.8; }}
    .label {{ font: italic 400 15px {MATH}; fill: {COLOR["muted"]}; }}{extra}
  </style>"""


def card_defs(width, height, glow_cx, flow_x2, flow_dir="right"):
    """Fundo, pontos, brilho e gradiente das linhas, comuns aos cartões."""
    x1, x2 = (0, flow_x2) if flow_dir == "right" else (flow_x2, 0)
    return f"""    <radialGradient id="glow" cx="{glow_cx}" cy="0.5" r="0.45">
      <stop offset="0" stop-color="{COLOR["foreground"]}" stop-opacity="0.06"/>
      <stop offset="1" stop-color="{COLOR["foreground"]}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="flowfade" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">
      <stop offset="0" stop-color="{COLOR["ring"]}" stop-opacity="0"/>
      <stop offset="0.45" stop-color="{COLOR["ring"]}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{COLOR["line"]}" stop-opacity="0.9"/>
    </linearGradient>
    <pattern id="dots" width="{GRID}" height="{GRID}" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="{COLOR["foreground"]}" fill-opacity="0.07"/>
    </pattern>
    <clipPath id="card">
      <rect width="{width}" height="{height}" rx="{RADIUS}"/>
    </clipPath>"""


def card_background(width, height):
    return f"""    <rect width="{width}" height="{height}" fill="{COLOR["background"]}"/>
    <rect width="{width}" height="{height}" fill="url(#dots)"/>
    <rect width="{width}" height="{height}" fill="url(#glow)"/>"""


def card_border(width, height):
    return (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="{RADIUS}" '
            f'fill="none" stroke="{COLOR["border"]}"/>')


def sup(text):
    return f'<tspan dy="-8" font-size="0.7em">{text}</tspan><tspan dy="8">'


def close(markup):
    """Fecha os tspans abertos por sup()."""
    return markup + "</tspan>" * markup.count('<tspan dy="8">')


def banner():
    width, height = 1200, 320
    formulas = [
        # Acima da rede
        (990, 34, 15, "H(X) = −Σ p(x) log p(x)"),
        (892, 64, 16, "softmax(QKᵀ / √d) V"),
        (1112, 64, 16, "P ≠ NP ?"),
        # À direita da rede
        (1104, 96, 16, "max(0, x)"),
        # Abaixo da rede
        (905, 264, 16, "θ ← θ − η ∇L(θ)"),
        (1056, 264, 16, "e" + sup("iπ") + " + 1 = 0"),
        (905, 302, 16, "P(A|B) = P(B|A) P(A) / P(B)"),
    ]
    # Rede neural: camadas com 3, 5, 5 e 2 neurônios.
    layers, net_x, net_cy, net_gap = [3, 5, 5, 2], [900, 980, 1060, 1140], 164, 30

    def layer_nodes(index):
        top = net_cy - net_gap * (layers[index] - 1) / 2
        return [(net_x[index], top + net_gap * i) for i in range(layers[index])]

    nodes = [layer_nodes(i) for i in range(len(layers))]
    edges = [f'<line class="edge" x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}"/>'
             for left, right in zip(nodes, nodes[1:]) for x1, y1 in left for x2, y2 in right]
    circles = [f'<circle class="node" cx="{x}" cy="{y:.1f}" r="7"/>' for layer in nodes for x, y in layer]
    highlight = [nodes[0][1], nodes[1][1], nodes[2][3], nodes[3][1]]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x},{y:.1f}" for i, (x, y) in enumerate(highlight))
    # Linhas de fluxo: saem da borda esquerda, contornam o texto e convergem na entrada da rede.
    inputs = nodes[0]
    flows = []
    for i, y0 in enumerate([16, 30, 42, 276, 290, 304]):
        xe, ye = inputs[0] if i < 2 else inputs[1] if i in (2, 3) else inputs[2]
        flows.append(f'<path class="flow" d="M-10,{y0} H770 C850,{y0} 830,{ye:.1f} {xe - 8},{ye:.1f}"/>')
    equations = "\n".join(f'    <text class="eq" x="{x}" y="{y}" font-size="{size}">{close(text)}</text>'
                          for x, y, size, text in formulas)
    extra = f'''
    .title {{ font: 700 72px {SANS}; fill: {COLOR['foreground']}; letter-spacing:-1.5px; }}
    .lead {{ font: 400 36px {SANS}; fill: {COLOR['signal']}; }}
    .meta {{ font: 500 30px {SANS}; fill: {COLOR['muted']}; }}'''
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Jordy Fontoura</title>
  <desc id="desc">{BANNER_ALT}. Text on the left; neural network and formulas from computing, mathematics and physics on the right.</desc>
  <defs>
{card_defs(width, height, 0.7, 900)}
  </defs>
{style(extra)}
  <g clip-path="url(#card)">
{card_background(width, height)}
    {"".join(flows)}
{equations}
    {"".join(edges)}
    <path class="signal" d="{path}"/>
    {"".join(circles)}
    {"".join(f'<circle cx="{x}" cy="{y:.1f}" r="3" fill="{COLOR["foreground"]}"/>' for x, y in highlight)}
    <text class="label" x="{net_x[0] - 10}" y="{net_cy - net_gap * 2 - 20}">y = σ(Wx + b)</text>
  </g>
  {card_border(width, height)}
  <text class="title" x="64" y="100">Jordy Fontoura</text>
  <text class="lead" x="68" y="154">AI Engineer · RAG, agents, MCP</text>
  <text class="lead" x="68" y="201">Software developer since 2018.</text>
  <text class="meta" x="68" y="256">TypeScript · Python · Rust</text>
</svg>
"""


def focus():
    """Cartão "What I build": etapas ligadas pelo caminho em destaque da rede do banner."""
    width, height = 1200, 320
    xs, cy = [180, 460, 740, 1020], 128
    extra = f"""
    .stage {{ font: 700 40px {SANS}; fill: {COLOR["foreground"]}; letter-spacing: -0.5px; }}
    .detail {{ font: 400 28px {SANS}; fill: {COLOR["muted"]}; }}"""
    parts = []
    # Linhas que entram pela borda esquerda e saem pela direita, como no banner.
    for dy in (-14, 0, 14):
        parts.append(f'<path class="flow" d="M-10,{cy + dy * 4} C80,{cy + dy * 4} 70,{cy + dy} {xs[0] - 48},{cy + dy}"/>')
        parts.append(f'<path class="flow flow-out" d="M{xs[-1] + 48},{cy + dy} C{width - 70},{cy + dy} '
                     f'{width - 80},{cy + dy * 4} {width + 10},{cy + dy * 4}"/>')
    # Malha discreta entre etapas vizinhas, sob o caminho principal.
    for a, b in zip(xs, xs[1:]):
        for dy1 in (-18, 18):
            for dy2 in (-18, 18):
                parts.append(f'<line class="edge" x1="{a + 30}" y1="{cy + dy1}" x2="{b - 30}" y2="{cy + dy2}" stroke-opacity="0.45"/>')
    parts.append(f'<path class="signal" d="M{xs[0]},{cy} H{xs[-1]}"/>')
    for x, (stage, detail, formula) in zip(xs, STAGES):
        parts.append(f'<text class="eq" x="{x}" y="{cy - 64}" font-size="22" text-anchor="middle">{formula}</text>')
        parts.append(f'<circle class="ring" cx="{x}" cy="{cy}" r="46" stroke-dasharray="3 6"/>')
        parts.append(f'<circle class="node" cx="{x}" cy="{cy}" r="30"/>')
        parts.append(f'<circle cx="{x}" cy="{cy}" r="5" fill="{COLOR["foreground"]}"/>')
        parts.append(f'<text class="stage" x="{x}" y="{cy + 112}" text-anchor="middle">{stage}</text>')
        parts.append(f'<text class="detail" x="{x}" y="{cy + 154}" text-anchor="middle">{detail}</text>')
    body = "\n    ".join(parts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">What I build</title>
  <desc id="desc">{FOCUS_ALT}, drawn as connected nodes in the style of the profile banner.</desc>
  <defs>
{card_defs(width, height, 0.5, 260)}
    <linearGradient id="flowfadeout" gradientUnits="userSpaceOnUse" x1="{width}" y1="0" x2="{width - 260}" y2="0">
      <stop offset="0" stop-color="{COLOR["ring"]}" stop-opacity="0"/>
      <stop offset="0.45" stop-color="{COLOR["ring"]}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{COLOR["line"]}" stop-opacity="0.9"/>
    </linearGradient>
  </defs>
{style(extra + '''
    .flow-out { stroke: url(#flowfadeout); }''')}
  <g clip-path="url(#card)">
{card_background(width, height)}
    {body}
  </g>
  {card_border(width, height)}
</svg>
"""


def banner_mobile(medium=False):
    """Texto primeiro, com rede abaixo no celular ou ao lado na versão intermediária."""
    width, height = (760, 300) if medium else (600, 380)
    net_x, net_y = (540, 150) if medium else (350, 325)
    layers = [3, 4, 4, 2]
    nodes = [[(net_x+i*58, net_y+(j-(size-1)/2)*14) for j in range(size)]
             for i, size in enumerate(layers)]
    edges = ''.join(f'<line class="edge" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
                    for left, right in zip(nodes, nodes[1:]) for x1,y1 in left for x2,y2 in right)
    circles = ''.join(f'<circle class="node" cx="{x}" cy="{y}" r="3.5"/>' for layer in nodes for x,y in layer)
    extra = f'''
    .mobile-name {{ font: 700 52px {SANS}; fill: {COLOR['foreground']}; letter-spacing:-1px; }}
    .mobile-role {{ font: 500 34px {SANS}; fill: {COLOR['foreground']}; }}
    .mobile-topic {{ font: 400 30px {SANS}; fill: {COLOR['signal']}; }}
    .mobile-meta {{ font: 400 30px {SANS}; fill: {COLOR['muted']}; }}'''
    decoration = '''<path class="flow" d="M-10,16 H470 C510,16 510,136 536.5,136"/>
    <path class="flow" d="M-10,284 H470 C510,284 510,164 536.5,164"/>
    <text class="eq" x="540" y="96" font-size="20">y = σ(Wx + b)</text>
    <text class="eq" x="540" y="220" font-size="18">xᵀAx</text>''' if medium else '''<path class="flow" d="M-10,280 H270 C320,280 310,311 346.5,311"/>
    <path class="flow" d="M-10,290 H258 C308,290 310,325 346.5,325"/>
    <path class="flow" d="M-10,300 H246 C296,300 310,339 346.5,339"/>
    <text class="eq" x="40" y="335" font-size="20">y = σ(Wx + b)</text>
    <text class="eq" x="40" y="359" font-size="18">xᵀAx</text>'''
    layout = 'Intermediate layout with a neural network beside the text' if medium else 'Compact mobile layout with text above a small neural network'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Jordy Fontoura</title>
  <desc id="desc">{BANNER_ALT}. {layout}.</desc>
  <defs>
{card_defs(width, height, 0.7, 350)}
  </defs>
{style(extra)}
  <g clip-path="url(#card)">
{card_background(width, height)}
    {decoration}
    {edges}{circles}
  </g>
  {card_border(width, height)}
  <g>
    <text class="mobile-name" x="40" y="76">Jordy Fontoura</text>
    <text class="mobile-role" x="40" y="122">AI Engineer</text>
    <text class="mobile-topic" x="40" y="162">RAG · agents · MCP</text>
    <text class="mobile-meta" x="40" y="213">Software developer since 2018.</text>
    <text class="mobile-meta" x="40" y="255">TypeScript · Python · Rust</text>
  </g>
</svg>
'''


def focus_mobile(medium=False):
    """As quatro áreas em duas colunas, com conexões fora dos rótulos."""
    width, height = (760 if medium else 600), 420
    left, right = (200, 560) if medium else (160, 440)
    bend = width - 26
    extra = f'''
    .mobile-stage {{ font: 700 32px {SANS}; fill: {COLOR['foreground']}; }}
    .mobile-detail {{ font: 400 25px {SANS}; fill: {COLOR['muted']}; }}'''
    parts = [f'<path class="signal" d="M{left},68 H{right} M{left},268 H{right}"/>',
             f'<path class="edge" fill="none" d="M{right+32},68 H{bend-20} Q{bend},68 {bend},88 V248 Q{bend},268 {bend-20},268 H{right+32}"/>']
    for (x,y), (stage,detail,formula) in zip([(left,68),(right,68),(left,268),(right,268)], STAGES):
        parts.extend([
            f'<text class="eq" x="{x}" y="{y-36}" font-size="20" text-anchor="middle">{formula}</text>',
            f'<circle class="ring" cx="{x}" cy="{y}" r="32" stroke-dasharray="3 6"/>',
            f'<circle class="node" cx="{x}" cy="{y}" r="20"/>',
            f'<circle cx="{x}" cy="{y}" r="3.5" fill="{COLOR["foreground"]}"/>',
            f'<text class="mobile-stage" x="{x}" y="{y+64}" text-anchor="middle">{stage}</text>',
            f'<text class="mobile-detail" x="{x}" y="{y+102}" text-anchor="middle">{detail}</text>',
        ])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">What I build</title>
  <desc id="desc">{FOCUS_ALT}. {'Intermediate' if medium else 'Mobile'} layout in two rows and two columns.</desc>
  <defs>
{card_defs(width, height, 0.5, 260)}
  </defs>
{style(extra)}
  <g clip-path="url(#card)">
{card_background(width, height)}
    {''.join(parts)}
  </g>
  {card_border(width, height)}
</svg>
'''


def problems(name, svg):
    """Restrições do GitHub e orçamento de tamanho."""
    found = []
    xml.dom.minidom.parseString(svg)
    for pattern in (r"<script", r"<foreignObject", r"<image", r"@import", r"@font-face", r"url\((?!#)",
                    r'href="(?!#)'):
        if re.search(pattern, svg):
            found.append(f"{name}: contém {pattern}")
    if re.search(r"https?://(?!www\.w3\.org/2000/svg\")", svg):
        found.append(f"{name}: referência externa")
    if len(svg.encode("utf-8")) > MAX_BYTES:
        found.append(f"{name}: maior que {MAX_BYTES} bytes")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {"banner.svg": banner(), "focus.svg": focus(),
               "banner-mobile.svg": banner_mobile(), "focus-mobile.svg": focus_mobile(),
               "banner-medium.svg": banner_mobile(True), "focus-medium.svg": focus_mobile(True)}
    errors = [p for name, svg in outputs.items() for p in problems(name, svg)]
    readme = README.read_text(encoding="utf-8")
    for name, alt in (("banner.svg", BANNER_ALT), ("focus.svg", FOCUS_ALT)):
        if f'src="assets/{name}" alt="{alt}"' not in readme:
            errors.append(f"README.md: alt de assets/{name} difere do texto do gerador")
        sources = '\n'.join(f'  <source media="(max-width: {limit}px)" srcset="assets/{name.replace(".svg", "-"+variant+".svg")}">'
                            for limit, variant in ((480, 'mobile'), (1011, 'medium')))
        expected = '<picture>\n'+sources+f'\n  <img src="assets/{name}" alt="{alt}" width="880">'
        if expected not in readme:
            errors.append(f"README.md: fontes responsivas ou largura de assets/{name} incorretas")
    if args.check:
        for name, svg in outputs.items():
            path = ASSETS / name
            if not path.exists() or path.read_text(encoding="utf-8") != svg:
                errors.append(f"assets/{name} desatualizado; rode python scripts/build_assets.py")
    else:
        ASSETS.mkdir(exist_ok=True)
        for name, svg in outputs.items():
            (ASSETS / name).write_text(svg, encoding="utf-8", newline="\n")
            print(f"assets/{name}: {len(svg.encode('utf-8'))} bytes")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    result = subprocess.run([sys.executable, '-I', str(ROOT/'scripts/build_usage.py'), *(['--check'] if args.check else [])])
    if result.returncode:
        return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
