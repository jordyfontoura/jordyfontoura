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
from runpy import run_path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
MAX_BYTES = 100_000

# Executar o arquivo local permite manter os CLIs isolados com python -I.
COLOR = run_path(str(Path(__file__).with_name('theme.py')))['COLOR']
COMPANION = run_path(str(Path(__file__).with_name('companion.py')))

SANS = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
MATH = '"Cambria Math", "STIX Two Math", "Latin Modern Math", "Times New Roman", Times, serif'
RADIUS = 24
GRID = 24

# Textos: a mesma frase vai para o SVG e para o alt do README.
BANNER_ALT = "Jordy Fontoura. Comecei no RPG Maker aos 10 anos."
def card_defs(width, height, glow_cx, flow_x2, flow_dir="right", include_flow=True):
    """Fundo, pontos, brilho e gradiente das linhas, comuns aos cartões."""
    x1, x2 = (0, flow_x2) if flow_dir == "right" else (flow_x2, 0)
    flow = f'''    <linearGradient id="flowfade" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">
      <stop offset="0" stop-color="{COLOR["ring"]}" stop-opacity="0"/>
      <stop offset="0.45" stop-color="{COLOR["ring"]}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{COLOR["line"]}" stop-opacity="0.9"/>
    </linearGradient>''' if include_flow else ""
    return f"""    <radialGradient id="glow" cx="{glow_cx}" cy="0.5" r="0.45">
      <stop offset="0" stop-color="{COLOR["foreground"]}" stop-opacity="0.06"/>
      <stop offset="1" stop-color="{COLOR["foreground"]}" stop-opacity="0"/>
    </radialGradient>
{flow}

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


def banner_art(width, height, variant='desktop'):
    """Nome, uma lembrança pessoal e a C1; nenhuma informação depende do movimento."""
    mobile = variant == 'mobile'
    name_size, body_size, terminal_size = {
        'desktop': (40, 21, 18), 'medium': (41, 22.1, 20),
        'compact': (44, 22.1, 22), 'mobile': (52, 30, 26),
    }[variant]
    cx, cy, scale = {
        'desktop': (735, 146, 1.65), 'medium': (655, 146, 1.6),
        'compact': (480, 146, 1.4), 'mobile': (300, 286, 1.55),
    }[variant]
    x, name_y = (40, 112) if mobile else (32, 112)
    personal = ('<text x="40" y="166" class="body">Comecei no RPG Maker</text>'
                '<text x="40" y="204" class="body">aos 10 anos.</text>') if mobile else (
                '<text x="32" y="158" class="body">Comecei no RPG Maker</text>'
                '<text x="32" y="188" class="body">aos 10 anos.</text>') if variant=='compact' else (
                '<text x="32" y="158" class="body">Comecei no RPG Maker aos 10 anos.</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Jordy Fontoura</title>
  <desc id="desc">{BANNER_ALT} {COMPANION['DESCRIPTION']}</desc>
  <defs>{card_defs(width, height, 0.8, width, include_flow=False)}</defs>
  <style>
    .name {{ font:700 {name_size}px {SANS}; fill:{COLOR['foreground']}; letter-spacing:-1px; }}
    .body {{ font:400 {body_size}px {SANS}; fill:{COLOR['lead']}; }}
    .terminal {{ font:500 {terminal_size}px ui-monospace,Consolas,monospace; fill:{COLOR['muted']}; }}
{COMPANION['stylesheet'](COLOR)}
    @media (prefers-reduced-motion:reduce) {{ .companion-idle,.companion-antenna,.companion-cursor,.companion-shadow,.companion-aerial,.companion-command,.companion-confirmation,.companion-context,.companion-tools,.companion-product {{ animation:none; }} }}
  </style>
  <g clip-path="url(#card)">
    {card_background(width,height)}
    <path d="M0,48 H{width}" stroke="{COLOR['border']}"/>
    <circle cx="24" cy="24" r="3" fill="{COLOR['line']}"/><circle cx="38" cy="24" r="3" fill="{COLOR['line']}"/><circle cx="52" cy="24" r="3" fill="{COLOR['accent']}"/>
    <text x="76" y="31" class="terminal">~/jordy</text>
    {COMPANION['artwork'](cx,cy,scale)}
    <text x="{x}" y="{name_y}" class="name">Jordy Fontoura.</text>
    {personal}
  </g>
  {card_border(width,height)}
</svg>
'''


def banner():
    return banner_art(900, 264)


def banner_medium():
    return banner_art(800, 264, 'medium')


def banner_compact():
    return banner_art(600, 264, 'compact')


def banner_mobile():
    return banner_art(600, 420, 'mobile')


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
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", svg)
    required = ({'companion-idle','companion-antenna','companion-cursor','companion-shadow','companion-aerial','companion-command','companion-confirmation','companion-context','companion-tools','companion-product'} if name.startswith('banner') else
                {'motion-art'} if name.startswith('project-') else set())
    if '-still.svg' not in name:
        active_classes = set()
        for selectors, declarations in rules:
            animation = re.search(r'(?:^|;)\s*animation:\s*([^;]+)', declarations)
            if animation and animation[1].strip() != 'none':
                active_classes.update(re.findall(r'\.([\w-]+)',selectors))
        element_classes = set().union(*(set(e.getAttribute('class').split())
                                       for e in document.getElementsByTagName('*')))
        active_classes &= element_classes
        if required-active_classes:
            found.append(f'{name}: animação obrigatória ausente: '+', '.join(sorted(required-active_classes)))
    def seconds(value):
        return [float(number) / (1000 if unit == 'ms' else 1)
                for number, unit in re.findall(r"(-?[\d.]+)(ms|s)\b", value)]
    for selectors, declarations in rules:
        animation = re.search(r"(?:^|;)\s*animation:\s*([^;]+)", declarations)
        if not animation or animation[1].strip() == 'none':
            continue
        classes = set(re.findall(r"\.([\w-]+)", selectors))
        if not classes or not classes <= disabled:
            found.append(f"{name}: toda animação deve respeitar movimento reduzido")
        value = animation[1].strip()
        times = seconds(value)
        duration = times[0] if times else None
        delays = [0.0, times[1] if len(times) > 1 else 0.0]
        for rule_selectors, rule_declarations in rules:
            if classes.intersection(re.findall(r"\.([\w-]+)", rule_selectors)):
                delay = re.search(r"animation-delay:\s*([^;]+)", rule_declarations)
                if delay:
                    delays.extend(seconds(delay[1]))
        for element in document.getElementsByTagName('*'):
            if classes.intersection(element.getAttribute('class').split()):
                delay = re.search(r"animation-delay:\s*([^;]+)", element.getAttribute('style'))
                if delay:
                    delays.extend(seconds(delay[1]))
        # Movimento contínuo aprovado pelo usuário: só ornamentos, com alternativa estática.
        continuous = bool(classes) and classes <= {'companion-idle','companion-antenna','companion-cursor','companion-shadow','companion-aerial','companion-command','companion-confirmation','companion-context','companion-tools','companion-product','motion-art'} and 'infinite' in value
        if duration is None or duration <= 0 or (not continuous and
            (not re.search(r"\s1(?:\s|$)", value) or 'infinite' in value or duration + max(delays) >= 5)):
            found.append(f"{name}: apenas ornamentos podem repetir; abertura deve terminar antes de cinco segundos")
    if len(svg.encode("utf-8")) > MAX_BYTES:
        found.append(f"{name}: maior que {MAX_BYTES} bytes")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {"banner.svg": banner(), "banner-mobile.svg": banner_mobile(),
               "banner-medium.svg": banner_medium(), "banner-compact.svg": banner_compact()}
    cards = run_path(str(Path(__file__).with_name('profile_cards.py')))
    card_outputs = cards['outputs'](COLOR, SANS)
    # A seleção pelo picture também cobre navegadores que não propagam a preferência ao SVG.
    outputs.update({name.replace('.svg', '-still.svg'): re.sub(r'animation:[^;]+;', 'animation:none;', svg).replace(COMPANION['DESCRIPTION'], COMPANION['STATIC_DESCRIPTION'])
                    for name, svg in list(outputs.items())})
    outputs.update(card_outputs)
    errors = [p for name, svg in outputs.items() for p in problems(name, svg)]
    readme = README.read_text(encoding="utf-8")
    errors.extend(cards['reference_problems'](readme))
    for name, alt in (("banner.svg", BANNER_ALT),):
        if f'src="assets/{name}" alt="{alt}"' not in readme:
            errors.append(f"README.md: alt de assets/{name} difere do texto do gerador")
        expected=cards['picture'](name.removesuffix('.svg'),alt)
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
    # A versão estática preserva o conteúdo com todos os ornamentos parados.
    static = re.sub(r'assets/((?:banner|project-)[\w-]*)(?<!-still)\.svg',
                    lambda m:'assets/'+m[1]+'-still.svg', README.read_text(encoding='utf-8'))
    static_path=ROOT/'README-static.md'
    if args.check:
        if not static_path.exists() or static_path.read_text(encoding='utf-8')!=static:
            print('README-static.md desatualizado',file=sys.stderr)
            return 1
    else:
        static_path.write_text(static,encoding='utf-8',newline='\n')
    return 0


if __name__ == "__main__":
    sys.exit(main())
