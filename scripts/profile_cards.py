"""Ladrilhos de projetos: largura intrínseca para quebra de linha sem CSS próprio."""
from html import escape
from pathlib import Path
import re
import textwrap

PROJECTS = [
    dict(key='agents', name='Agentes de IA', detail='RAG, ferramentas e contexto para atendimento.', meta='TypeScript · pgvector', url='projetos/agentes.md', private=True),
    dict(key='essays', name='Redações', detail='OCR e IA para correção de redações.', meta='TypeScript · OCR · LLM', url='projetos/redacoes.md', private=True),
    dict(key='chomatter', name='Chomatter', detail='Linguagem narrativa com saltos e chamadas.', meta='Rust · TypeScript', url='projetos/chomatter.md', private=True),
    dict(key='gitclean', name='gitclean', detail='Limpe arquivos ignorados pelo Git.', meta='Rust · CLI interativa'),
    dict(key='tryless', name='TryLess', detail='Trate erros com Result.', meta='TypeScript · npm'),
    dict(key='skills', name='skills', detail='Instruções para agentes de programação.', meta='Claude Code · Codex'),
]
URLS = {p['key']: p.get('url', 'https://github.com/jordyfontoura/'+('TryLess' if p['key']=='tryless' else p['key'])) for p in PROJECTS}


def alt(project):
    detail = project['detail'][0].lower()+project['detail'][1:]
    destination = 'Código privado. Ler relato.' if project.get('private') else 'Abrir repositório.'
    return project['name']+': '+detail+' '+project['meta'].replace(' · ', ', ')+'. '+destination


def miniature_art(key):
    if key == 'agents':
        return '<rect class="box" x="0" y="20" width="50" height="40" rx="7"/><path class="line" d="M10 32H38 M10 43H30 M50 40H90 M90 40V12H110 M90 40V68H110"/><rect class="box" x="110" y="0" width="48" height="24" rx="5"/><rect class="box" x="110" y="56" width="48" height="24" rx="5"/>'
    if key == 'essays':
        return '<path class="box" d="M12 0H85L105 20V80H12Z"/><path class="line" d="M85 0V20H105 M25 32H80 M25 45H70 M25 58H60 M118 49L132 63L155 32"/>'
    if key == 'chomatter':
        return '<rect class="box" x="0" y="26" width="42" height="28" rx="5"/><rect class="box" x="112" y="0" width="46" height="25" rx="5"/><rect class="box" x="112" y="55" width="46" height="25" rx="5"/><path class="line" d="M42 40H75V12H112 M75 40V67H112 M135 55V40H92 M98 34L92 40L98 46"/>'
    if key == 'skills':
        return '<path class="line" d="M5,20 H155 M5,58 H155"/>'+''.join(f'<rect class="box" x="{x}" y="8" width="38" height="62" rx="6"/><path class="line" d="M{x+8},25 h22 m-22,12 h16 m-16,12 h20"/>' for x in [0,60,120])
    if key == 'tryless':
        return '<path class="line" d="M65,40 H90 V15 H115 M90,40 V65 H115"/><rect class="box" x="0" y="25" width="65" height="30" rx="7"/><path class="line" d="M14 34L22 40L14 46 M29 46H46 M123 15L130 22L143 8 M125 59L139 73 M139 59L125 73"/>'
    if key == 'gitclean':
        return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><path class="line" d="M12 16H80 M12 30H110 M12 44H66"/><rect class="box" x="10" y="61" width="138" height="7" rx="3"/><path class="line" d="M13,64.5 H100"/>'
    if key == 'np':
        return '<path class="line" d="M40,40 H75 M75,40 V10 H95 M75,40 H95 M75,40 V70 H95"/><rect class="box" x="2" y="25" width="35" height="30" rx="5"/><rect class="box" x="99" y="2" width="50" height="16" rx="4"/><rect class="box" x="99" y="32" width="50" height="16" rx="4"/><rect class="box" x="99" y="62" width="50" height="16" rx="4"/>'
    return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><path class="line" d="M8,57 H150 M8,27 L25,39 L43,16 L60,32 L79,22 L99,38 L119,15 L150,25"/>'


def miniature(key):
    routes = {
        'agents':'M50,40 H90 V12 H110',
        'essays':'M25,32 H80 M118,49 L132,63 L155,32',
        'chomatter':'M42,40 H75 V12 H112',
        'skills':'M0,70 V8 H38 V70 H60 V8 H98 V70 H120 V8 H158 V70',
        'tryless':'M65,40 H90 V15 H115',
        'gitclean':'M13,64.5 H145',
        'np':'M40,40 H75 V70 H95',
        'argus':'M8,27 L25,39 L43,16 L60,32 L79,22 L99,38 L119,15 L150,25',
    }
    phase=list(URLS).index(key)*-1.3
    return miniature_art(key)+f'<path class="motion-art" style="animation-delay:{phase}s" pathLength="96" d="{routes[key]}"/>'


def detail_lines(detail, limit):
    """Equilibra duas linhas sem deixar uma palavra isolada no final."""
    if len(detail)<=limit:
        return [detail]
    words=detail.split()
    options=[(' '.join(words[:i]), ' '.join(words[i:])) for i in range(1,len(words))]
    candidates=[lines for lines in options if max(map(len,lines))<=limit]
    return list(min(candidates,key=lambda lines:abs(len(lines[0])-len(lines[1])))) if candidates else textwrap.wrap(detail,limit)


def project_card(project, mobile, colors, font):
    # 400 px intrínsecos: dois ladrilhos em colunas largas, um em colunas menores.
    body_size, meta_size = (20, 19) if mobile else (17.5, 14.5)
    height = 228 if mobile else 206
    lines = detail_lines(project['detail'], 30 if mobile else 36)
    description = ''.join(f'<text class="body" x="24" y="{128+i*(28 if mobile else 24)}">{escape(line)}</text>' for i,line in enumerate(lines))
    css = f'''
    .name {{font:700 24px {font};fill:{colors['foreground']}}}
    .body {{font:400 {body_size}px {font};fill:{colors['lead']}}}
    .meta {{font:400 {meta_size}px {font};fill:{colors['muted']}}}
    .action {{font:400 {meta_size}px {font};fill:{colors['muted']}}}
    .line {{fill:none;stroke:{colors['muted']};stroke-width:1.5}}
    .box {{fill:{colors['card']};stroke:{colors['ring']}}}
    .motion-art {{fill:none;stroke:{colors['foreground']};stroke-width:3;stroke-linecap:round;stroke-opacity:0;stroke-dasharray:24 72;animation:art-flow 8s linear infinite;}}
    @keyframes art-flow {{from {{stroke-dashoffset:0;stroke-opacity:1;}} to {{stroke-dashoffset:-96;stroke-opacity:1;}}}}
    @media (prefers-reduced-motion: reduce) {{.motion-art {{animation:none;}}}}
    '''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}" viewBox="0 0 400 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(project['name'])}</title>
<desc id="desc">{escape(alt(project))}</desc>
<style>{css}</style>
<rect x="4.5" y="4.5" width="391" height="{height-9}" rx="18" fill="{colors['background']}" stroke="{colors['border']}"/>
<text class="name" x="24" y="44">{escape(project['name'])}</text>
<text class="meta" x="202" y="42">↗</text>
<g transform="translate(250 22) scale(.8)">{miniature(project['key'])}</g>
<text class="action" x="24" y="80">{'Código privado · Relato' if project.get('private') else 'Ver repositório'}</text>
{description}
<text class="meta" x="24" y="{height-24}">{escape(project['meta'])}</text>
</svg>
'''


def picture(name, description):
    if name.startswith('project-'):
        sources = [
            ('(prefers-reduced-motion: reduce) and (max-width: 480px)', '-mobile-still'),
            ('(prefers-reduced-motion: reduce)', '-still'),
            ('(max-width: 480px)', '-mobile'),
        ]
        width = 400
    else:
        variants = [
            ('(max-width: 480px)', '-mobile'),
            ('(max-width: 585px), (min-width: 768px) and (max-width: 905px)', '-compact'),
            ('(max-width: 1011px)', '-medium'),
            ('', ''),
        ]
        sources = []
        for reduced in (True, False):
            for condition, variant in variants:
                if not reduced and not condition:
                    continue
                media = ', '.join('(prefers-reduced-motion: reduce)'+(' and '+part if part else '') for part in condition.split(', ')) if reduced else condition
                sources.append((media, variant+('-still' if reduced else '')))
        width = 880
    markup = [f'  <source media="{media}" srcset="assets/{name}{suffix}.svg">' for media,suffix in sources]
    return '<picture>\n'+'\n'.join(markup)+f'\n  <img src="assets/{name}.svg" alt="{escape(description,quote=True)}" width="{width}">\n</picture>'


def project_block(project):
    # Sem linha vazia entre os links: as imagens ficam no mesmo fluxo inline.
    return f'<a href="{URLS[project["key"]]}">'+picture('project-'+project['key'],alt(project))+'</a>'


def outputs(colors, font):
    result = {}
    for project in PROJECTS:
        for mobile in (False, True):
            name = 'project-'+project['key']+('-mobile' if mobile else '')+'.svg'
            result[name] = project_card(project, mobile, colors, font)
    result.update({name.replace('.svg','-still.svg'):re.sub(r'animation:[^;]+;', 'animation:none;', svg) for name,svg in list(result.items())})
    return result


def reference_problems(readme):
    found = ['README.md: link, fontes ou alt do projeto '+project['key']+' incorretos' for project in PROJECTS if project_block(project) not in readme]
    root = Path(__file__).resolve().parents[1]
    for project in PROJECTS:
        if project.get('private') and not (root / URLS[project['key']]).is_file():
            found.append('README.md: relato do projeto '+project['key']+' ausente')
    return found
