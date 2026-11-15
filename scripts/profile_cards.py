"""Cartões vetoriais do portfólio e mapa de tecnologias, sem recursos externos."""
from html import escape
import textwrap

PROJECTS = [
    dict(key='skills', name='skills', detail='Alinhe decisões, implemente e peça provas aos agentes.', meta='Claude Code · Codex · português'),
    dict(key='tryless', name='TryLess', detail='Trate erros com Result em TypeScript.', meta='TypeScript · npm'),
    dict(key='gitclean', name='gitclean', detail='Inspecione e limpe arquivos ignorados pelo Git.', meta='Rust · CLI interativa'),
    dict(key='np', name='np', detail='Use npm, Yarn e pnpm com um só comando.', meta='Rust · CLI'),
    dict(key='argus', name='Argus', detail='Monitore hardware e configure alertas no Windows.', meta='Rust · Tauri'),
]
URLS = {p['key']: 'https://github.com/jordyfontoura/'+('TryLess' if p['key']=='tryless' else p['key']) for p in PROJECTS}
STACK = [
    ('IA aplicada', ['Python · PyTorch', 'Vercel AI SDK · OpenAI SDK', 'PostgreSQL · pgvector']),
    ('Backend', ['TypeScript · Node.js', 'NestJS · Fastify']),
    ('Web', ['React · Next.js', 'Vue · Nuxt.js']),
    ('Infraestrutura', ['Docker · Kubernetes', 'AWS · Google Cloud']),
    ('Rust', ['CLIs e aplicativos desktop', 'Projetos pessoais e abertos']),
]
STACK_ALT = 'Tecnologias por área: IA com Python, PyTorch, Vercel AI SDK, OpenAI SDK e PostgreSQL/pgvector; backend com TypeScript, Node.js, NestJS e Fastify; web com React/Next.js e Vue/Nuxt.js; infraestrutura com Docker, Kubernetes, AWS e Google Cloud; Rust em projetos pessoais e abertos de CLIs e aplicativos desktop.'


def alt(project):
    detail = project['detail'][0].lower()+project['detail'][1:]
    return project['name']+': '+detail+' '+project['meta'].replace(' · ', ', ')+'. Abrir repositório.'


def shell(width, height, title, description, body, colors, font):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{colors['foreground']}" opacity=".04"/></pattern></defs>
<style>.name {{font:700 32px {font};fill:{colors['foreground']};letter-spacing:-.5px}} .body {{font:400 22px {font};fill:{colors['lead']}}} .meta {{font:400 19px {font};fill:{colors['muted']}}} .mini {{font:500 14px ui-monospace,Consolas,monospace;fill:{colors['accent']}}} .line {{fill:none;stroke:{colors['muted']};stroke-width:1.5}} .box {{fill:{colors['card']};stroke:{colors['ring']}}} .index {{font:500 20px ui-monospace,Consolas,monospace;fill:{colors['muted']}}} .mobile-name {{font:700 38px {font};fill:{colors['foreground']}}} .mobile-body {{font:400 30px {font};fill:{colors['lead']}}} .mobile-meta {{font:400 26px {font};fill:{colors['muted']}}} .stack-title {{font:600 27px {font};fill:{colors['foreground']}}} .stack-body {{font:400 24px {font};fill:{colors['lead']}}} .stack-mobile-title {{font:600 32px {font};fill:{colors['foreground']}}} .stack-mobile-body {{font:400 28px {font};fill:{colors['lead']}}} </style>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="24" fill="{colors['background']}" stroke="{colors['border']}"/>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="24" fill="url(#dots)"/>
{body}
</svg>
'''


def miniature_art(key):
    if key == 'skills':
        return '<path class="line" d="M5,20 H155 M5,58 H155"/>'+''.join(f'<rect class="box" x="{x}" y="8" width="38" height="62" rx="6"/><path class="line" d="M{x+8},25 h22 m-22,12 h16 m-16,12 h20"/>' for x in [0,60,120])
    if key == 'tryless':
        return '<path class="line" d="M65,40 H90 V15 H115 M90,40 V65 H115"/><rect class="box" x="0" y="25" width="65" height="30" rx="7"/><text class="mini" x="8" y="45">Result</text><text class="mini" x="125" y="20">ok</text><text class="mini" x="125" y="70">err</text>'
    if key == 'gitclean':
        return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><text class="mini" x="10" y="22">.gitignore</text><text class="mini" x="10" y="48">espaço usado</text><rect class="box" x="10" y="61" width="138" height="7" rx="3"/><path class="line" d="M13,64.5 H100"/>'
    if key == 'np':
        return '<path class="line" d="M40,40 H75 M75,40 V10 H95 M75,40 H95 M75,40 V70 H95"/><text class="mini" x="8" y="45">np</text><text class="mini" x="100" y="15">npm</text><text class="mini" x="100" y="45">Yarn</text><text class="mini" x="100" y="75">pnpm</text>'
    return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><path class="line" d="M8,57 H150 M8,27 L25,39 L43,16 L60,32 L79,22 L99,38 L119,15 L150,25"/><text class="mini" x="10" y="73">CPU / GPU</text>'


def miniature(key):
    routes = {
        'skills':'M0,70 V8 H38 V70 H60 V8 H98 V70 H120 V8 H158 V70',
        'tryless':'M65,40 H90 V15 H115',
        'gitclean':'M13,64.5 H145',
        'np':'M40,40 H75 V70 H95',
        'argus':'M8,27 L25,39 L43,16 L60,32 L79,22 L99,38 L119,15 L150,25',
    }
    phase=list(URLS).index(key)*-.55
    return miniature_art(key)+f'<path class="motion-art" style="animation-delay:{phase}s" pathLength="96" d="{routes[key]}"/>'


def wrapped_detail(detail, width):
    lines = textwrap.wrap(detail, width)
    if len(lines)>1 and len(lines[-1].split())==1:
        previous, word = lines[-2].rsplit(' ',1)
        lines[-2:] = [previous,word+' '+lines[-1]]
    return lines


def project_card(project, index, variant, colors, font):
    mobile = variant == 'mobile'
    compact = variant == 'compact'
    width,height = {'mobile':(600,260),'compact':(600,210),'medium':(800,174),'':(900,150)}[variant]
    name_class = 'mobile-name' if mobile else 'name'
    meta_class = 'mobile-meta' if mobile else 'meta'
    body = f'<rect class="box" x="24" y="24" width="64" height="72" rx="12"/><text class="index" x="56" y="66" text-anchor="middle">{index:02}</text>'
    body += f'<text class="{name_class}" x="112" y="52">{escape(project["name"])}</text>'
    arrow_x = 380 if mobile or compact else width-200
    body += f'<text class="{"mobile-name" if mobile else "name"}" x="{arrow_x}" y="52">↗</text>'
    if mobile or compact:
        body += f'<text class="{meta_class}" x="32" y="{height-24}">{escape(project["meta"])}</text>'
        for i,line in enumerate(wrapped_detail(project['detail'],32 if mobile else 46)):
            body += f'<text class="{"mobile-body" if mobile else "body"}" x="32" y="{(144 if mobile else 122)+i*(36 if mobile else 27)}">{escape(line)}</text>'
        body += '<g transform="translate(426 24) scale(.85)">'+miniature(project['key'])+'</g>'
    else:
        for i,line in enumerate(wrapped_detail(project['detail'],44 if variant=='medium' else 54)):
            body += f'<text class="body" x="112" y="{84+i*27}">{escape(line)}</text>'
        body += f'<text class="meta" x="112" y="{height-24}">{escape(project["meta"])}</text>'
        body += f'<g transform="translate({width-168} 24) scale(.85)">'+miniature(project['key'])+'</g>'
    body += f'<text class="mini" x="{width-32}" y="{height-24}" text-anchor="end">repositório ↗</text>'
    # A ação pertence ao link do README; a descrição isolada só descreve a imagem.
    svg = shell(width,height,project['name'],alt(project).removesuffix(' Abrir repositório.'),body,colors,font)
    return svg.replace('700 32px','700 25px').replace('400 22px',f'400 {21 if variant=="" else 22.1}px').replace('400 19px','400 18px').replace('400 26px','400 24px')


def stack_symbol(index):
    paths = [
        'M2,12 L12,2 L22,12 L12,22 Z M2,12 H22 M12,2 V22',
        'M2,4 H22 V20 H2 Z M7,9 L10,12 L7,15 M13,15 H18',
        'M2,3 H22 V21 H2 Z M2,8 H22 M9,8 V21',
        'M4,5 H20 V11 H4 Z M4,15 H20 V21 H4 Z M7,8 H9 M7,18 H9',
        'M5,5 H19 V19 H5 Z M9,1 V5 M15,1 V5 M9,19 V23 M15,19 V23 M1,9 H5 M19,9 H23 M1,15 H5 M19,15 H23',
    ]
    return f'<path class="line" d="{paths[index]}"/><path class="motion-art" style="animation-delay:{index*-.65}s" pathLength="96" d="{paths[index]}"/>'


def stack_card(variant, colors, font):
    mobile = variant in ('mobile','compact')
    body = ''
    if mobile:
        cursor = 48
        for index,(title,lines) in enumerate(STACK):
            body += f'<g transform="translate(32 {cursor-26}) scale(1.3)">{stack_symbol(index)}</g><text class="stack-mobile-title" x="72" y="{cursor}">{escape(title)}</text>'
            for i,line in enumerate(lines):
                body += f'<text class="stack-mobile-body" x="32" y="{cursor+42+i*34}">{escape(line)}</text>'
            cursor += 42+(len(lines)-1)*34+64
        width,height=600,cursor-24
    else:
        width,height=900,380
        for i,(title,lines) in enumerate(STACK[:4]):
            x=32 if i%2==0 else 480
            y=44 if i<2 else 194
            body += f'<g transform="translate({x} {y-22})">{stack_symbol(i)}</g><text class="stack-title" x="{x+38}" y="{y}">{escape(title)}</text>'
            for j,line in enumerate(lines):
                body += f'<text class="stack-body" x="{x}" y="{y+36+j*28}">{escape(line)}</text>'
        body += f'<path d="M32,294 H868" stroke="{colors["border"]}"/><g transform="translate(32 320)">{stack_symbol(4)}</g><text class="stack-title" x="70" y="342">Rust</text><text class="stack-body" x="150" y="342">CLIs e desktop · projetos pessoais e abertos</text>'
    svg = shell(width,height,'Tecnologias de trabalho',STACK_ALT,body,colors,font)
    if variant=='compact':
        svg = svg.replace('600 32px','600 26px').replace('400 28px','400 22.1px')
    elif variant=='medium':
        # Mesma composição horizontal; viewBox maior para tipografia intermediária.
        svg = svg.replace('width="900"','width="800"',1).replace('height="380"','height="338"',1)
        svg = svg.replace('400 24px','400 24.75px').replace('600 27px','600 29.25px')
    else:
        svg = svg.replace('400 24px','400 22px').replace('600 27px','600 25px') if not mobile else svg
    return svg


def picture(name,description):
    # A coluna encolhe quando o GitHub exibe a barra lateral a partir de 768 px.
    reduced=''
    for condition,variant in [('(max-width: 480px)','-mobile'),('(max-width: 585px), (min-width: 768px) and (max-width: 905px)','-compact'),('(max-width: 1011px)','-medium'),('', '')]:
        media=', '.join('(prefers-reduced-motion: reduce)'+(' and '+part if part else '') for part in condition.split(', '))
        reduced+=f'  <source media="{media}" srcset="assets/{name}{variant}-still.svg">\n'
    return (f'<picture>\n'+reduced+f'  <source media="(max-width: 480px)" srcset="assets/{name}-mobile.svg">\n'
            f'  <source media="(max-width: 585px), (min-width: 768px) and (max-width: 905px)" srcset="assets/{name}-compact.svg">\n'
            f'  <source media="(max-width: 1011px)" srcset="assets/{name}-medium.svg">\n'
            f'  <img src="assets/{name}.svg" alt="{escape(description,quote=True)}" width="880">\n</picture>')


def project_block(project):
    return f'<a href="{URLS[project["key"]]}">\n'+picture('project-'+project['key'],alt(project))+'\n</a>'


def outputs(colors,font):
    import re
    result={}
    for i,project in enumerate(PROJECTS,1):
        for variant in ['','mobile','compact','medium']:
            suffix='-'+variant if variant else ''
            result['project-'+project['key']+suffix+'.svg']=project_card(project,i,variant,colors,font)
    for variant in ['','mobile','compact','medium']:
        suffix='-'+variant if variant else ''
        result['stack'+suffix+'.svg']=stack_card(variant,colors,font)
    for name,svg in list(result.items()):
        css=f'.motion-art {{fill:none; stroke:{colors["foreground"]}; stroke-width:3; stroke-linecap:round; stroke-opacity:0; stroke-dasharray:24 72; animation:art-flow 3.8s linear infinite;}} @keyframes art-flow {{from {{stroke-dashoffset:0;stroke-opacity:1;}} to {{stroke-dashoffset:-96;stroke-opacity:1;}}}} @media (prefers-reduced-motion: reduce) {{.motion-art {{animation:none;}}}}'
        result[name]=svg.replace('</style>',css+'</style>')
    result.update({name.replace('.svg','-still.svg'):re.sub(r'animation:[^;]+;','animation:none;',svg) for name,svg in list(result.items())})
    return result


def reference_problems(readme):
    errors=[]
    for project in PROJECTS:
        if project_block(project) not in readme:
            errors.append('README.md: link, fontes ou alt do projeto '+project['key']+' incorretos')
    if picture('stack',STACK_ALT) not in readme:
        errors.append('README.md: fontes ou alt do mapa de tecnologias incorretos')
    return errors
