"""Gera os SVGs desktop/intermediário/mobile e o painel de uso a partir do agregado.

Uso:
  python scripts/build_assets.py                 regenera os SVGs
  python scripts/build_assets.py --check         confere SVGs e textos alternativos do README
Os banners são vetoriais, sem foto embutida ou arquivo de imagem auxiliar.
O GitHub serve os SVGs com `default-src 'none'; style-src 'unsafe-inline'; sandbox`, então
nada aqui pode depender de fontes, scripts ou recursos externos.
"""

import argparse
import math
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
BANNER_ALT = ("Jordy Fontoura: engenheiro de IA, com RAG, agentes e MCP; "
              "desenvolvedor desde 2018; TypeScript, Python e Rust")
FOCUS_ALT = ("O que construo: busca (RAG, pgvector), LLMs (Vercel AI SDK), "
             "ferramentas (tool calling, MCP) e agentes de conversa")
STAGES = [
    # (rótulo, detalhe, fórmula decorativa)
    ("Busca", "RAG · pgvector", "sim(q, d)"),
    ("LLMs", "Vercel AI SDK", "p(y | x)"),
    ("Ferramentas", "tool calling · MCP", "f(args)"),
    ("Agentes", "conversacionais", "π(a | s)"),
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
    .signal {{ fill: none; stroke: #76e4bb; stroke-width: 2; stroke-opacity: 0.8; stroke-dasharray: 12 8; animation: flow 4.8s linear 1; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -160; }} }}
    @media (prefers-reduced-motion: reduce) {{ .signal {{ animation: none; }} }}
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


def banner_art(width, height, compact=False):
    """Terminal vetorial com um campo neural; texto nunca depende da animação."""
    cx, cy = (440, 450) if compact else (735, 208) if width == 900 else (930, 208)
    radius = 105 if compact else 94 if width == 900 else 128
    parts = []
    points = []
    for ring, count in ((0.48, 8), (1, 16)):
        for i in range(count):
            angle = i * math.tau / count
            points.append((cx + math.cos(angle)*radius*ring,
                           cy + math.sin(angle)*radius*ring))
    for i, (x, y) in enumerate(points):
        nx, ny = points[(i+5) % len(points)]
        parts.append(f'<path class="mesh" d="M{x:.1f},{y:.1f} L{nx:.1f},{ny:.1f}"/>')
        parts.append(f'<circle class="neuron" style="animation-delay:{i*.035:.3f}s" cx="{x:.1f}" cy="{y:.1f}" r="3"/>')
    parts.append(f'<circle class="orbit" cx="{cx}" cy="{cy}" r="{radius+14}"/>')
    parts.append(f'<path class="packet" d="M{cx-radius-14},{cy} H{cx+radius+14}"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="28" fill="#102a24" stroke="#76e4bb"/>')
    parts.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" class="core">IA</text>')
    name_size = 46 if compact else 64
    lines = (f'<text x="40" y="112" class="name">Jordy Fontoura<tspan fill="#76e4bb">.</tspan></text>'
             '<text x="40" y="156" class="role">Engenharia de IA aplicada</text>'
             '<text x="40" y="200" class="body">RAG · agentes · MCP</text>'
             '<text x="40" y="238" class="body">TypeScript · Python · Rust</text>'
             '<text x="40" y="288" class="caption">Programando desde 2018.</text>') if compact else (
             '<text x="56" y="142" class="name">Jordy Fontoura<tspan fill="#76e4bb">.</tspan></text>'
             '<text x="58" y="190" class="role">Engenharia de IA aplicada</text>'
             '<text x="58" y="242" class="body">RAG · agentes · MCP</text>'
             '<text x="58" y="281" class="body">TypeScript · Python · Rust</text>'
             '<text x="58" y="334" class="caption">Desenvolvendo software desde 2018.</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Jordy Fontoura</title>
  <desc id="desc">{BANNER_ALT}. Rede neural animada em um terminal; movimento termina em menos de cinco segundos.</desc>
  <defs>{card_defs(width, height, 0.8, width)}</defs>
  <style>
    .name {{ font:700 {name_size}px {SANS}; fill:#fafafa; letter-spacing:-2px; }}
    .role {{ font:500 30px {SANS}; fill:#e4e4e7; }}
    .body {{ font:400 30px {SANS}; fill:#a1a1aa; }}
    .caption {{ font:400 28px {SANS}; fill:#a1a1aa; }}
    .terminal,.core {{ font:500 26px ui-monospace,Consolas,monospace; fill:#76e4bb; }}
    .mesh {{ stroke:#76e4bb; stroke-opacity:.17; fill:none; }}
    .neuron {{ fill:#76e4bb; opacity:.65; animation:activate 3.8s ease-in-out 1 both; }}
    .orbit {{ fill:none; stroke:#76e4bb; stroke-opacity:.6; stroke-dasharray:2 12; animation:orbit 4.8s linear 1 forwards; }}
    .packet {{ fill:none; stroke:#76e4bb; stroke-width:2; stroke-dasharray:12 320; animation:transfer 4.8s ease-out 1 forwards; opacity:0; }}
    @keyframes orbit {{ to {{ stroke-dashoffset:-168; }} }}
    @keyframes transfer {{ 0% {{ stroke-dashoffset:332; opacity:0; }} 15%,75% {{ opacity:.8; }} 100% {{ stroke-dashoffset:0; opacity:0; }} }}
    @keyframes activate {{ 0%,100% {{ opacity:.65; }} 45% {{ opacity:1; }} }}
    @media (prefers-reduced-motion:reduce) {{ .neuron,.orbit,.packet {{ animation:none; }} }}
  </style>
  <g clip-path="url(#card)">
    {card_background(width,height)}
    <path d="M0,52 H{width}" stroke="#27272a"/>
    <circle cx="24" cy="26" r="4" fill="#52525b"/><circle cx="40" cy="26" r="4" fill="#52525b"/><circle cx="56" cy="26" r="4" fill="#76e4bb"/>
    <text x="80" y="32" class="terminal">jordy / laboratório de IA</text>
    {''.join(parts)}
    {lines}
    <text x="40" y="{height-24}" class="terminal">&gt; contexto → ferramentas → produto</text>
  </g>
  {card_border(width,height)}
</svg>
'''


def banner():
    return banner_art(1200, 410)


def focus():
    """Cartão "O que construo": etapas ligadas pelo caminho em destaque da rede do banner."""
    width, height = 1200, 180
    xs, cy = [180, 460, 740, 1020], 72
    extra = f"""
    .stage {{ font: 700 22px {SANS}; fill: {COLOR["foreground"]}; letter-spacing: -0.5px; }}
    .detail {{ font: 400 20px {SANS}; fill: {COLOR["muted"]}; }}"""
    parts = []
    # Linhas que entram pela borda esquerda e saem pela direita, como no banner.
    for dy in (-10, 0, 10):
        parts.append(f'<path class="flow" d="M-10,{cy + dy * 3} C80,{cy + dy * 3} 70,{cy + dy} {xs[0] - 26},{cy + dy}"/>')
        parts.append(f'<path class="flow flow-out" d="M{xs[-1] + 26},{cy + dy} C{width - 70},{cy + dy} '
                     f'{width - 80},{cy + dy * 3} {width + 10},{cy + dy * 3}"/>')
    # Malha discreta entre etapas vizinhas, sob o caminho principal.
    for a, b in zip(xs, xs[1:]):
        for dy1 in (-12, 12):
            for dy2 in (-12, 12):
                parts.append(f'<line class="edge" x1="{a + 26}" y1="{cy + dy1}" x2="{b - 26}" y2="{cy + dy2}" stroke-opacity="0.45"/>')
    parts.append(f'<path class="signal" d="M{xs[0]},{cy} H{xs[-1]}"/>')
    for x, (stage, detail, formula) in zip(xs, STAGES):
        parts.append(f'<text class="eq" x="{x}" y="34" font-size="15" text-anchor="middle">{formula}</text>')
        parts.append(f'<circle class="ring" cx="{x}" cy="{cy}" r="26" stroke-dasharray="3 6"/>')
        parts.append(f'<circle class="node" cx="{x}" cy="{cy}" r="18"/>')
        parts.append(f'<circle cx="{x}" cy="{cy}" r="3" fill="{COLOR["foreground"]}"/>')
        parts.append(f'<text class="stage" x="{x}" y="128" text-anchor="middle">{stage}</text>')
        parts.append(f'<text class="detail" x="{x}" y="156" text-anchor="middle">{detail}</text>')
    body = "\n    ".join(parts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">O que construo</title>
  <desc id="desc">{FOCUS_ALT}, em etapas conectadas no estilo do banner.</desc>
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


def banner_medium():
    """Versão horizontal para a coluna do perfil em tablets e notebooks."""
    return banner_art(900, 410)


def banner_mobile():
    # Mesmo layout vertical nos tamanhos menores: nenhum texto invade o campo neural.
    return banner_art(600, 630, compact=True)


def focus_mobile(medium=False):
    """As quatro áreas em duas colunas, com conexões fora dos rótulos."""
    width, height = (760 if medium else 600), 420
    left, right = (200, 560) if medium else (160, 440)
    extra = f'''
    .mobile-stage {{ font: 700 32px {SANS}; fill: {COLOR['foreground']}; }}
    .mobile-detail {{ font: 400 25px {SANS}; fill: {COLOR['muted']}; }}'''
    parts = [f'<path class="signal" d="M{left},68 H{right} M{left},268 H{right}"/>']
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
  <title id="title">O que construo</title>
  <desc id="desc">{FOCUS_ALT}. Versão {'intermediária' if medium else 'de celular'}, em duas linhas na ordem de leitura.</desc>
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
    # Cada regra é conferida contra os elementos que ela anima, sem depender do nome.
    reduced = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{\s*([^{}]+)\{\s*animation:\s*none;\s*\}\s*\}", svg)
    disabled = set(re.findall(r"\.([\w-]+)", reduced[1])) if reduced else set()
    document = xml.dom.minidom.parseString(svg)
    for selectors, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", svg):
        animation = re.search(r"(?:^|;)\s*animation:\s*([^;]+)", declarations)
        if not animation or animation[1].strip() == 'none':
            continue
        classes = set(re.findall(r"\.([\w-]+)", selectors))
        if not classes or not classes <= disabled:
            found.append(f"{name}: toda animação deve respeitar movimento reduzido")
        delays = [0.0]
        for element in document.getElementsByTagName('*'):
            if classes.intersection(element.getAttribute('class').split()):
                delays.extend(float(v) for v in re.findall(r"animation-delay:([\d.]+)s", element.getAttribute('style')))
        value = animation[1].strip()
        duration = re.search(r"([\d.]+)s", value)
        if not duration or 'infinite' in value or not re.search(r"\s1(?:\s|$)", value) or float(duration[1]) + max(delays) >= 5:
            found.append(f"{name}: animação deve executar uma vez e terminar antes de cinco segundos")
    if len(svg.encode("utf-8")) > MAX_BYTES:
        found.append(f"{name}: maior que {MAX_BYTES} bytes")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {"banner.svg": banner(), "focus.svg": focus(),
               "banner-mobile.svg": banner_mobile(), "focus-mobile.svg": focus_mobile(),
               "banner-medium.svg": banner_medium(), "focus-medium.svg": focus_mobile(True)}
    # A seleção pelo picture também cobre navegadores que não propagam a preferência ao SVG.
    outputs.update({name.replace('.svg', '-still.svg'): re.sub(r'animation:[^;]+;', 'animation:none;', svg)
                    for name, svg in list(outputs.items())})
    errors = [p for name, svg in outputs.items() for p in problems(name, svg)]
    readme = README.read_text(encoding="utf-8")
    for name, alt in (("banner.svg", BANNER_ALT), ("focus.svg", FOCUS_ALT)):
        if f'src="assets/{name}" alt="{alt}"' not in readme:
            errors.append(f"README.md: alt de assets/{name} difere do texto do gerador")
        sources = '\n'.join(f'  <source media="(max-width: {limit}px)" srcset="assets/{name.replace(".svg", "-"+variant+".svg")}">'
                            for limit, variant in ((480, 'mobile'), (1279, 'medium')))
        still_sources = '\n'.join(
            f'  <source media="(prefers-reduced-motion: reduce) and (max-width: {limit}px)" srcset="assets/{name.replace(".svg", "-"+variant+"-still.svg")}">'
            for limit, variant in ((480, 'mobile'), (1279, 'medium')))
        still_sources += f'\n  <source media="(prefers-reduced-motion: reduce)" srcset="assets/{name.replace(".svg", "-still.svg")}">'
        expected = '<picture>\n'+still_sources+'\n'+sources+f'\n  <img src="assets/{name}" alt="{alt}" width="880">'
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
