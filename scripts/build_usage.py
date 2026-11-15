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
from runpy import run_path
import re
import sys
import xml.etree.ElementTree as ET

THEME = run_path(str(Path(__file__).with_name('theme.py')))
COLOR, AGENT_COLORS = THEME['COLOR'], THEME['AGENT_COLORS']
DISPLAY_NAMES = {'Local models': 'Modelos locais', 'Other agents': 'Outros agentes',
                 'Remaining models': 'Demais modelos', 'Other models': 'Outros modelos'}

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
ALT = 'Uso de agentes de programação'


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


def compact(number, precision=1):
    for divisor, unit in [(10**9, 'bi'), (10**6, 'mi'), (10**3, 'mil')]:
        if number >= divisor:
            return f'{number/divisor:.{precision}f}'.replace('.', ',')+' '+unit
    return f'{number:g}'.replace('.', ',')


def nice_max(value):
    if value <= 1:
        return 1
    base = 10 ** (len(str(value))-1)
    return next(step*base for step in (1,2,5,10) if step*base >= value)


def month_label(value):
    months = ('jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez')
    return f'{months[value.month-1]}/{value.year}'


def alternative_text(data):
    agents, _, _ = metrics(data)
    total = sum(agents.values())
    period = month_label(date.fromisoformat(data['since']))
    distribution = '; '.join(f"{DISPLAY_NAMES.get(name,name)} {count/total:.0%}"
                             for name,count in agents.most_common())
    formatted_total = f'{total:,}'.replace(',', '.')
    text = f"{ALT} em {period}: {formatted_total} tokens; {distribution}."
    text += ' Entrada, saída e cache; histórico parcial. Tokens não representam custo ou produtividade.'
    if 'Local models' in agents:
        text += ' Modelos locais agregados sem divulgar seus nomes.'
    return text


def panel(data, mobile=False, medium=False):
    """Volume diário e participação, com cores estáveis e escala explícita."""
    agents, models, days = metrics(data)
    total = sum(agents.values())
    stacked = mobile or medium
    width = 600 if medium else 360 if mobile else 900
    agent_y = 450 if stacked else 150
    model_title_y = agent_y + len(agents)*44 + 26 if stacked else max(266, agent_y + (len(agents)-1)*32 + 42)
    model_y = model_title_y + (30 if stacked else 27)
    footer_y = model_y + len(models)*40 + 8 if stacked else max(396, model_y + (len(models)-1)*25 + 28)
    height = footer_y + (116 if stacked else 72)
    fg, muted = COLOR['foreground'], COLOR['muted']
    parts = []

    def text(x, y, value, size=15, color=muted, weight=400, anchor='start'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rect(x, y, w, h, color, radius=2):
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius}" fill="{color}"/>')

    def rule(x1, y, x2, dashed=False):
        dash = ' stroke-dasharray="3 5"' if dashed else ''
        parts.append(f'<path d="M{x1},{y} H{x2}" stroke="{COLOR["ring"]}" stroke-width="1"{dash}/>')

    start = date.fromisoformat(data['since'])
    end = date.fromisoformat(data['until_exclusive']) - timedelta(days=1)
    if stacked:
        text(32, 40, 'Uso de agentes', 25, fg, 650)
        text(32, 89, compact(total), 38, COLOR['accent'], 650)
        text(32, 118, 'tokens registrados · '+month_label(start), 17)
        text(32, 145, f'{start:%d/%m} a {end:%d/%m}', 16)
    else:
        text(32, 43, 'Uso de agentes', 24, fg, 650)
        text(32, 70, f'{month_label(start)} · {start:%d/%m} a {end:%d/%m}', 16)
        text(width-32, 43, compact(total), 32, COLOR['accent'], 650, 'end')
        text(width-32, 70, 'tokens registrados', 16, anchor='end')
        rule(32, 91, width-32)

    x0, chart_width = (92, width-124) if stacked else (98, 442)
    top, bottom = (184, 324) if stacked else (120, 285)
    maximum = nice_max(max(sum(day.values()) for day in days))
    for fraction in [0, .5, 1]:
        y = bottom - (bottom-top)*fraction
        rule(x0, y, x0+chart_width, True)
        text(x0-12, y+5, compact(maximum*fraction).replace(',0 ', ' '), 13 if stacked else 14, anchor='end')
    span = chart_width / len(days)
    for i, day in enumerate(days):
        cursor = bottom
        for name, _ in reversed(agents.most_common()):
            h = day[name] / maximum * (bottom-top)
            if h:
                cursor -= h
                rect(x0+i*span+1, cursor, max(1,span-3), h, AGENT_COLORS[name], 1)
        if not sum(day.values()):
            rect(x0+i*span+1, bottom-2, max(1,span-3), 2, COLOR['ring'], 0)
    for i in sorted({0, 7, 14, 21, len(days)-1}):
        if i < len(days):
            text(x0+(i+.5)*span, bottom+26, f'{(start+timedelta(days=i)).day:02}', 13 if stacked else 14, anchor='middle')
    text(x0 if not stacked else 32, bottom+59, 'Volume diário · tokens', 17, COLOR['lead'], 500)
    active = sum(bool(sum(day.values())) for day in days)
    if not stacked:
        text(x0, bottom+84, f'{active} dias com registros no período', 15)

    ranking_x = 32 if stacked else 594
    ranking_end = width-32
    text(ranking_x, agent_y-30, 'POR AGENTE', 17 if stacked else 14, muted, 600)
    for i, (name, count) in enumerate(agents.most_common()):
        y = agent_y + i*(44 if stacked else 32)
        rect(ranking_x, y-11, 9, 9, AGENT_COLORS[name])
        text(ranking_x+20, y, DISPLAY_NAMES.get(name,name), 18 if stacked else 17, fg)
        text(ranking_end, y, f'{count/total:.0%}', 18 if stacked else 17, COLOR['lead'], anchor='end')
        bar_width = ranking_end-ranking_x-20
        rect(ranking_x+20, y+9, bar_width, 3, COLOR['border'], 1)
        rect(ranking_x+20, y+9, bar_width*count/total, 3, AGENT_COLORS[name], 1)
    text(ranking_x, model_title_y, 'POR MODELO', 17 if stacked else 14, muted, 600)
    for i, (name, count) in enumerate(models):
        y = model_y + i*(40 if stacked else 25)
        text(ranking_x, y, DISPLAY_NAMES.get(name,name), 18 if stacked else 16, COLOR['lead'])
        text(ranking_end, y, f'{count/total:.0%}', 18 if stacked else 16, muted, anchor='end')
    rule(32, footer_y, width-32)
    if stacked:
        text(32, footer_y+28, 'Entrada + saída e cache', 15)
        text(32, footer_y+51, 'Tokens não representam custo', 15)
        text(32, footer_y+74, 'Histórico parcial · UTC-03:00', 14)
        text(32, footer_y+97, 'Último registro: '+datetime.fromisoformat(data['latest_record_at']).strftime('%d/%m/%Y'), 14)
    else:
        text(32, footer_y+25, 'Entrada + saída e cache · tokens não representam custo', 14)
        text(32, footer_y+48, 'Histórico parcial · UTC-03:00', 14)
        text(width-32, footer_y+48, 'Último registro: '+datetime.fromisoformat(data['latest_record_at']).strftime('%d/%m/%Y'), 14, anchor='end')
    body = ''.join(parts)
    result = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Uso de agentes</title>
<desc id="desc">{escape(alternative_text(data))}</desc>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="24" fill="{COLOR['background']}" stroke="{COLOR['border']}"/>
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
        alt = escape(alternative_text(data), quote=True)
        readme_path = ROOT/'README.md'
        readme = readme_path.read_text(encoding='utf-8')
        if args.check:
            expected = ('<picture>\n'
                        '  <source media="(max-width: 480px)" srcset="assets/agent-usage-mobile.svg">\n'
                        '  <source media="(max-width: 1011px)" srcset="assets/agent-usage-medium.svg">\n'
                        f'  <img src="assets/agent-usage.svg" alt="{alt}" width="880">')
            if expected not in readme:
                raise ValueError('Referência ou texto alternativo do painel ausente.')
        updated_readme, references = re.subn(r'(<img src="assets/agent-usage.svg" alt=")[^"]*(" width="880">)',
                                               lambda match: match[1]+alt+match[2], readme)
        if references != 1:
            raise ValueError('Referência única do painel ausente.')
        outputs = {readme_path: updated_readme, DATA: json.dumps(data, indent=2, ensure_ascii=False)+'\n',
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
