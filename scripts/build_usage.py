"""Coleta só o cache de métricas T3 v9 e gera o painel público, sem ler transcrições.

python -I scripts/build_usage.py --collect  # atualiza agregado e SVGs localmente
python -I scripts/build_usage.py --check    # confere somente arquivos públicos
Sem --collect, regenera os SVGs a partir do agregado sanitizado.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/agent-usage.json'
OFFSET = timezone(timedelta(hours=-3))
AGENTS = {'claude': 'Claude Code', 'codex': 'Codex', 'local': 'Local models'}
# Lista fechada: identificadores desconhecidos nunca são copiados para a exportação.
PUBLIC_MODELS = {
    'claude-opus-5-5': 'Claude Opus 5.5',
    'claude-sonnet-5-5': 'Claude Sonnet 5.5',
    'claude-haiku-5-5': 'Claude Haiku 5.5',
    'gpt-6.1-sol': 'GPT-6.1 Sol',
    'gpt-6.1-terra': 'GPT-6.1 Terra',
    'gpt-6-astra': 'GPT-6 Astra',
    'gpt-6-luna': 'GPT-6 Luna',
    'gpt-6-sol': 'GPT-6 Sol',
}
SAFE_MODELS = set(PUBLIC_MODELS.values()) | {'Other models', 'Local models'}
SAFE_AGENTS = set(AGENTS.values()) | {'Other agents'}
CATEGORIES = ('uncached_input', 'cached_input', 'cache_creation', 'output')
ALT = 'Recorded coding-agent usage by day, agent and model for the last closed calendar month. Input and output tokens, including cache; partial history. Local model names are hidden.'


def month_window(reference):
    """Primeiro dia do mês anterior, inclusivo; primeiro do mês de referência, exclusivo."""
    end = reference.replace(day=1)
    return (end-timedelta(days=1)).replace(day=1), end


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError('Contador de uso inválido; nenhum arquivo foi atualizado.')
    return value


def collect(document, as_of):
    """Projeção fechada do cache: paths, sessões, IDs, custo e nomes privados não saem."""
    if not isinstance(document, dict) or document.get('version') != 9:
        raise ValueError('Formato de cache não suportado; esperado T3 v9.')
    start, end = month_window(as_of)
    seen, grouped = set(), defaultdict(lambda: [0, 0, 0, 0])
    latest = None
    for entry in document['files'].values():
        provider = entry['p']
        agent = AGENTS.get(provider, 'Other agents')
        for row in entry['r'] + entry['t']:
            if not isinstance(row, list) or len(row) < 12:
                raise ValueError('Registro de métricas incompatível; cache preservado.')
            timestamp, model_index = integer(row[0]), integer(row[1])
            if model_index >= len(document['models']):
                raise ValueError('Referência de modelo inválida no cache.')
            raw_model = document['models'][model_index]
            # Mesma exclusão de decodeScanCache, antes de registrar a chave.
            if provider == 'claude' and raw_model == '<synthetic>':
                continue
            counts = [integer(v) for v in row[3:7]]
            integer(row[7])  # raciocínio já está incluído em output, não somar
            key = row[8]
            if key is not None:
                if not isinstance(key, str):
                    raise ValueError('Chave de deduplicação inválida.')
                if key in seen:
                    continue
                seen.add(key)
            instant = datetime.fromtimestamp(timestamp / 1000, OFFSET)
            day = instant.date()
            if not start <= day < end or sum(counts) == 0:
                continue
            # O contexto local prevalece até sobre um nome que pareça público.
            if provider == 'local':
                model = 'Local models'
            elif (provider == 'claude' and raw_model.startswith('claude-')) or (provider == 'codex' and raw_model.startswith('gpt-')):
                model = PUBLIC_MODELS.get(raw_model, 'Other models')
            else:
                model = 'Other models'
            bucket = grouped[(day.isoformat(), agent, model)]
            for i, count in enumerate(counts):
                bucket[i] += count
            latest = max(latest, instant) if latest else instant
    if not grouped:
        raise ValueError('Nenhum contador no período; último painel válido preservado.')
    records = [dict(day=day, agent=agent, model=model, **dict(zip(CATEGORIES, values)))
               for (day, agent, model), values in sorted(grouped.items())]
    return dict(schema_version=2, source='T3 usage cache v9', timezone='UTC-03:00',
                since=start.isoformat(), until_exclusive=end.isoformat(),
                latest_record_at=latest.isoformat(timespec='seconds'), coverage='partial', records=records)


def validate(data):
    expected = {'schema_version', 'source', 'timezone', 'since', 'until_exclusive', 'latest_record_at', 'coverage', 'records'}
    if set(data) != expected or data['schema_version'] != 2 or data['coverage'] != 'partial':
        raise ValueError('Agregado público incompatível.')
    if data['source'] != 'T3 usage cache v9' or data['timezone'] != 'UTC-03:00':
        raise ValueError('Origem de métricas incompatível.')
    start, end = date.fromisoformat(data['since']), date.fromisoformat(data['until_exclusive'])
    if (start, end) != month_window(end):
        raise ValueError('O painel exige um mês civil fechado.')
    latest = datetime.fromisoformat(data['latest_record_at'])
    if latest.utcoffset() != timedelta(hours=-3) or not start <= latest.date() < end:
        raise ValueError('Data da última métrica inválida.')
    keys = set()
    for row in data['records']:
        if set(row) != {'day', 'agent', 'model', *CATEGORIES}:
            raise ValueError('Campos não permitidos no agregado público.')
        if row['agent'] not in SAFE_AGENTS or row['model'] not in SAFE_MODELS:
            raise ValueError('Rótulo não permitido no agregado público.')
        if row['agent'] == 'Local models' and row['model'] != 'Local models':
            raise ValueError('Identidade de modelo local não pode ser publicada.')
        permitted = {'Other models'}
        if row['agent'] == 'Claude Code':
            permitted |= {v for k,v in PUBLIC_MODELS.items() if k.startswith('claude-')}
        elif row['agent'] == 'Codex':
            permitted |= {v for k,v in PUBLIC_MODELS.items() if k.startswith('gpt-')}
        elif row['agent'] == 'Local models':
            permitted = {'Local models'}
        if row['model'] not in permitted:
            raise ValueError('Modelo incompatível com a fonte permitida.')
        if not start <= date.fromisoformat(row['day']) < end:
            raise ValueError('Métrica fora da janela.')
        for category in CATEGORIES:
            integer(row[category])
        key = (row['day'], row['agent'], row['model'])
        if key in keys:
            raise ValueError('Agregado público duplicado.')
        keys.add(key)
    if not data['records'] or not sum(sum(row[k] for k in CATEGORIES) for row in data['records']):
        raise ValueError('Agregado público sem uso registrado.')


def metrics(data):
    validate(data)
    agents, models = Counter(), Counter()
    start = date.fromisoformat(data['since'])
    days = [Counter() for _ in range((date.fromisoformat(data['until_exclusive'])-start).days)]
    for row in data['records']:
        total = sum(row[k] for k in CATEGORIES)
        agents[row['agent']] += total
        models[row['model']] += total
        days[(date.fromisoformat(row['day']) - start).days][row['agent']] += total
    top = models.most_common(3)
    rest = sum(models.values()) - sum(v for _, v in top)
    if rest:
        top.append(('Remaining models', rest))
    return agents, top, days


def compact(number):
    for divisor, unit in [(10**9, 'B'), (10**6, 'M'), (10**3, 'K')]:
        if number >= divisor:
            return f'{number/divisor:.1f}{unit}'
    return str(number)


def panel(data, mobile=False, medium=False):
    agents, models, days = metrics(data)
    total = sum(agents.values())
    mobile = mobile or medium
    width = 600 if medium else 360 if mobile else 720
    height = 518 + len(agents)*54 + len(models)*52 if mobile else 700
    fg, muted, bg, border = '#fafafa', '#a1a1aa', '#09090b', '#27272a'
    colors = ['#fafafa', '#a1a1aa', '#52525b', '#3f3f46']
    ordered = agents.most_common()
    palette = {name: colors[i] for i, (name, _) in enumerate(ordered)}
    parts = []
    def text(x, y, value, size=18, color=muted, weight=400, end=False):
        if medium and end:
            x -= 1  # Reserva para a extensão dos glifos além da âncora à direita.
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{"end" if end else "start"}">{escape(str(value))}</text>')
    def rect(x, y, w, h, fill, radius=3):
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{radius}" fill="{fill}"/>')
    def rule(y):
        parts.append(f'<path d="M24 {y}H{width-24}" stroke="{border}"/>')
    text(24, 38, 'My agent activity', 25, fg, 600)
    text(24, 88, compact(total), 40, fg, 650)
    month = date.fromisoformat(data['since']).strftime('%B %Y')
    text(24, 116, 'recorded tokens · '+month, 18)
    text(24 if mobile else width-24, 145 if mobile else 85,
         data['since'] + ' → < ' + data['until_exclusive'], 16, end=not mobile)
    if not mobile:
        text(width-24, 114, 'Partial history · UTC-03:00', 16, end=True)
    chart_top, bottom = (173, 273) if mobile else (160, 290)
    maximum = max(sum(w.values()) for w in days)
    span = (width - 48) / len(days)
    gap = min(7, span/4)
    for i, day in enumerate(days):
        cursor = bottom
        for name, _ in reversed(ordered):
            h = day[name] / maximum * (bottom-chart_top)
            if h:
                cursor -= h
                rect(24+i*span, cursor, span-gap, h, palette[name], 1)
        if not sum(day.values()):
            rect(24+i*span, bottom-2, span-gap, 2, border, 0)
        elif sum(day.values())/maximum*(bottom-chart_top) < 1:
            parts.append(f'<circle cx="{24+i*span+(span-gap)/2:.2f}" cy="{bottom}" r="1.5" fill="{fg}"/>')
    text(24, bottom+26, 'Daily recorded volume', 16)
    text(width-24, bottom+26, 'oldest → latest', 14, end=True)
    rule(bottom+45)
    def ranking(items, x, y, section_width, heading, agent=False):
        text(x, y, heading, 20, fg, 600)
        for i, (name, count) in enumerate(items):
            top = y+33+i*52
            text(x, top, name, 17, fg)
            text(x+section_width, top, f'{count/total:.0%}', 17, fg, end=True)
            rect(x, top+12, section_width, 8, '#18181b')
            rect(x, top+12, section_width*count/total, 8, palette[name] if agent else muted)
    y = bottom+78
    ranking(ordered, 24, y, width-48 if mobile else 280, 'By agent', True)
    ranking(models, 24 if mobile else 376, y+len(ordered)*54+56 if mobile else y,
            width-48 if mobile else 320, 'Top models · by tokens')
    rule(height-100 if mobile else height-84)
    text(24, height-76 if mobile else height-57, 'Input + output incl. cache · not cost', 14 if mobile else 17)
    if mobile:
        text(24, height-51, 'Partial history · UTC-03:00', 14)
    text(24, height-26 if mobile else height-32, 'Latest record: '+data['latest_record_at'][:10], 14 if mobile else 17)
    if not mobile:
        text(width-24, height-32, 'Snapshot · partial coverage', 15, end=True)
    body = ''.join(parts)
    result = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">My recorded coding-agent activity</title>
<desc id="desc">{escape(ALT)} {total:,} tokens from {data['since']} (inclusive) to {data['until_exclusive']} (exclusive).{' Intermediate layout.' if medium else ''}</desc>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="18" fill="{bg}" stroke="{border}"/>
<g font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif">{body}</g>
</svg>
'''
    ET.fromstring(result)
    if len(result.encode()) > 100_000 or re.search(r'<script|<foreignObject|@import|@font-face|url\((?!#)|href=', result):
        raise ValueError('SVG contém recurso não permitido.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--cache', type=Path, default=Path.home()/'.t3/userdata/usage-scan-cache-v9.json')
    parser.add_argument('--as-of', type=date.fromisoformat, help='Data de referência; coleta o mês civil anterior a essa data.')
    args = parser.parse_args()
    if args.collect and args.check:
        parser.error('--collect e --check são operações distintas')
    try:
        if args.collect:
            data = collect(json.loads(args.cache.read_text(encoding='utf-8')), args.as_of or datetime.now(OFFSET).date())
        else:
            data = json.loads(DATA.read_text(encoding='utf-8'))
        validate(data)
        if args.check:
            readme = (ROOT/'README.md').read_text(encoding='utf-8')
            expected = ('<picture>\n'
                        '  <source media="(max-width: 480px)" srcset="assets/agent-usage-mobile.svg">\n'
                        '  <source media="(max-width: 1011px)" srcset="assets/agent-usage-medium.svg">\n'
                        f'  <img src="assets/agent-usage.svg" alt="{ALT}" width="720">')
            if expected not in readme:
                raise ValueError('Referência ou texto alternativo do painel ausente.')
        outputs = {DATA: json.dumps(data, indent=2, ensure_ascii=False)+'\n',
                   ROOT/'assets/agent-usage.svg': panel(data),
                   ROOT/'assets/agent-usage-mobile.svg': panel(data, True),
                   ROOT/'assets/agent-usage-medium.svg': panel(data, medium=True)}
        for path, content in outputs.items():
            if args.check:
                if path.read_text(encoding='utf-8') != content:
                    raise ValueError('Painel desatualizado; execute scripts/build_usage.py.')
            else:
                path.parent.mkdir(exist_ok=True)
                temporary = path.with_suffix(path.suffix+'.tmp')
                temporary.write_text(content, encoding='utf-8', newline='\n')
                temporary.replace(path)
        if args.collect:
            print('Agregado sanitizado e painel atualizados. Nenhuma conversa ou credencial exportada.')
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError, IndexError, AttributeError):
        print('Não foi possível validar a fonte/painel. Confira o formato, a janela e os arquivos locais; nenhum detalhe privado foi exibido.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
