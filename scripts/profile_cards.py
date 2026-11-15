"""Cartões vetoriais do portfólio e mapa de tecnologias, sem recursos externos."""
from html import escape
import textwrap

PROJECTS = [
    dict(key='skills', name='skills', detail='Instruções de engenharia para agentes de código.', meta='Claude Code · Codex · português'),
    dict(key='tryless', name='TryLess', detail='Erros tipados em TypeScript com Result.', meta='TypeScript · npm'),
    dict(key='gitclean', name='gitclean', detail='Veja o espaço usado antes de limpar arquivos ignorados.', meta='Rust · CLI interativa'),
    dict(key='np', name='np', detail='Um comando para npm, Yarn e pnpm.', meta='Rust · CLI'),
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
STACK_ALT = 'Tecnologias por área: IA com Python, PyTorch, Vercel AI SDK, OpenAI SDK e PostgreSQL/pgvector; backend com TypeScript, Node.js, NestJS e Fastify; web com React/Next.js e Vue/Nuxt.js; infraestrutura com Docker, Kubernetes, AWS e Google Cloud; Rust em CLIs e aplicativos desktop pessoais e abertos.'


def alt(project):
    return project['name']+': '+project['detail']+' '+project['meta']+'. Abrir repositório.'


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


def miniature(key):
    if key == 'skills':
        return '<path class="line" d="M5,20 H155 M5,58 H155"/>'+''.join(f'<rect class="box" x="{x}" y="8" width="38" height="62" rx="6"/><path class="line" d="M{x+8},25 h22 m-22,12 h16 m-16,12 h20"/>' for x in [0,60,120])
    if key == 'tryless':
        return '<path class="line" d="M55,40 H90 V15 H125 M90,40 V65 H125"/><rect class="box" x="0" y="25" width="65" height="30" rx="7"/><text class="mini" x="8" y="45">Result</text><text class="mini" x="125" y="20">ok</text><text class="mini" x="125" y="70">err</text>'
    if key == 'gitclean':
        return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><text class="mini" x="10" y="22">.gitignore</text><path class="line" d="M10,40 h28 m8,0 h62 m-98,17 h28 m8,0 h84"/><rect class="box" x="12" y="67" width="90" height="5" rx="2"/>'
    if key == 'np':
        return '<path class="line" d="M40,40 H75 M75,40 V10 H95 M75,40 H95 M75,40 V70 H95"/><text class="mini" x="8" y="45">np</text><text class="mini" x="100" y="15">npm</text><text class="mini" x="100" y="45">Yarn</text><text class="mini" x="100" y="75">pnpm</text>'
    return '<rect class="box" x="0" y="0" width="158" height="80" rx="7"/><path class="line" d="M8,57 H150 M8,27 L25,39 L43,16 L60,32 L79,22 L99,38 L119,15 L150,25"/><text class="mini" x="10" y="73">CPU / GPU</text>'


def project_card(project, index, mobile, colors, font):
    width,height = (600,260) if mobile else (900,140)
    name_class = 'mobile-name' if mobile else 'name'
    meta_class = 'mobile-meta' if mobile else 'meta'
    body = f'<rect class="box" x="24" y="24" width="64" height="72" rx="12"/><text class="index" x="56" y="66" text-anchor="middle">{index:02}</text>'
    body += f'<text class="{name_class}" x="112" y="52">{escape(project["name"])}</text>'
    if mobile:
        body += f'<text class="{meta_class}" x="32" y="228">{escape(project["meta"])}</text>'
        for i,line in enumerate(textwrap.wrap(project['detail'],32)):
            body += f'<text class="mobile-body" x="32" y="{144+i*36}">{escape(line)}</text>'
        body += '<g transform="translate(426 24) scale(.85)">'+miniature(project['key'])+'</g>'
    else:
        body += f'<text class="body" x="112" y="84">{escape(project["detail"])}</text><text class="meta" x="112" y="116">{escape(project["meta"])}</text>'
        body += '<g transform="translate(706 30)">'+miniature(project['key'])+'</g>'
    return shell(width,height,project['name'],alt(project),body,colors,font)


def stack_card(mobile, colors, font):
    body = ''
    if mobile:
        cursor = 48
        for title,lines in STACK:
            body += f'<text class="stack-mobile-title" x="32" y="{cursor}">{escape(title)}</text>'
            for i,line in enumerate(lines):
                body += f'<text class="stack-mobile-body" x="32" y="{cursor+42+i*34}">{escape(line)}</text>'
            cursor += 42+(len(lines)-1)*34+64
        width,height=600,cursor-24
    else:
        width,height=900,380
        for i,(title,lines) in enumerate(STACK[:4]):
            x=32 if i%2==0 else 480
            y=44 if i<2 else 194
            body += f'<text class="stack-title" x="{x}" y="{y}">{escape(title)}</text>'
            for j,line in enumerate(lines):
                body += f'<text class="stack-body" x="{x}" y="{y+36+j*28}">{escape(line)}</text>'
        body += f'<path d="M32,294 H868" stroke="{colors["border"]}"/><text class="stack-title" x="32" y="342">Rust</text><text class="stack-body" x="120" y="342">CLIs e desktop · projetos pessoais e abertos</text>'
    return shell(width,height,'Tecnologias de trabalho',STACK_ALT,body,colors,font)


def picture(name,description):
    return f'<picture>\n  <source media="(max-width: 1011px)" srcset="assets/{name}-mobile.svg">\n  <img src="assets/{name}.svg" alt="{description}" width="880">\n</picture>'


def project_block(project):
    return f'<a href="{URLS[project["key"]]}">\n'+picture('project-'+project['key'],alt(project))+'\n</a>'


def outputs(colors,font):
    result={}
    for i,project in enumerate(PROJECTS,1):
        for mobile in [False,True]:
            suffix='-mobile' if mobile else ''
            result['project-'+project['key']+suffix+'.svg']=project_card(project,i,mobile,colors,font)
    result['stack.svg']=stack_card(False,colors,font)
    result['stack-mobile.svg']=stack_card(True,colors,font)
    return result


def reference_problems(readme):
    errors=[]
    for project in PROJECTS:
        if project_block(project) not in readme:
            errors.append('README.md: link, fontes ou alt do projeto '+project['key']+' incorretos')
    if picture('stack',STACK_ALT) not in readme:
        errors.append('README.md: fontes ou alt do mapa de tecnologias incorretos')
    return errors
