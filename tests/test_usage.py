"""Contagem e fronteira pública com entradas sintéticas; não lê cache real."""
from datetime import date, datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('usage', Path(__file__).resolve().parents[1]/'scripts/build_usage.py')
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)


def row(key='request', hour=12, day=31, month=10, counts=(10,20,5,7), model=0):
    timestamp = int(datetime(2026,month,day,hour,tzinfo=timezone.utc).timestamp()*1000)
    return [timestamp,model,0,*counts,999,key,123.45,0,None]


def document(records, provider='claude'):
    return dict(version=9, models=['claude-opus-5-5','private-local-7b'],
                sessions=['private-session-id'], prompt='private-prompt',
                files={'C:/private/customer/session.jsonl':dict(p=provider,r=records,t=[])})


class UsageTests(unittest.TestCase):
    def test_repeated_request_first_wins_and_nulls_remain(self):
        source = document([row(),row(None,counts=(1,2,0,3)),row(None,counts=(1,2,0,3))])
        source['files']['C:/private/customer/session.jsonl']['t']=[row(counts=(999,999,999,999))]
        source['files']['second-copy'] = dict(p='claude',r=[row()],t=[])
        result = usage.collect(source,date(2026,11,1))
        agents, models, weeks = usage.metrics(result)
        self.assertEqual(dict(agents),{'Claude Code':54})  # 42 + 6 + 6; sem raciocínio
        self.assertEqual(sum(v for _,v in models),54)
        self.assertEqual(sum(sum(w.values()) for w in weeks),54)

    def test_timezone_window_and_future(self):
        result = usage.collect(document([
            row('outside',hour=2,day=1,month=10),  # 30/set em UTC-03
            row('start',hour=3,day=1,month=10),
            row('end',hour=2,day=1,month=11),      # 31/out em UTC-03
            row('future',hour=3,day=1,month=11),   # 01/nov fica fora
        ]),date(2026,11,1))
        self.assertEqual([r['day'] for r in result['records']],['2026-10-01','2026-10-31'])
        self.assertEqual(sum(usage.metrics(result)[0].values()),84)
        self.assertEqual(len(usage.metrics(result)[2]),31)

    def test_month_window_handles_year_and_leap_year(self):
        self.assertEqual(usage.month_window(date(2026,1,20)),(date(2025,12,1),date(2026,1,1)))
        self.assertEqual(usage.month_window(date(2024,3,1)),(date(2024,2,1),date(2024,3,1)))
        self.assertEqual(usage.month_window(date(2026,3,31)),(date(2026,2,1),date(2026,3,1)))

    def test_public_schema_rejects_incomplete_month_or_end_day(self):
        result=usage.collect(document([row()]),date(2026,11,1))
        result['since']='2026-10-02'
        with self.assertRaises(ValueError):usage.validate(result)
        result['since']='2026-10-01'
        result['records'][0]['day']='2026-11-01'
        with self.assertRaises(ValueError):usage.validate(result)

    def test_private_fields_never_reach_public_outputs(self):
        result = usage.collect(document([row(model=1)]),date(2026,11,1))
        public = json.dumps(result)+usage.panel(result)+usage.panel(result,True)+usage.panel(result,medium=True)+usage.panel(result,compact_variant=True)
        for forbidden in ['private-local-7b','private-prompt','private-session-id','customer','123.45']:
            self.assertNotIn(forbidden,public)
        self.assertEqual(result['records'][0]['model'],'Other models')

    def test_local_context_overrides_public_looking_id(self):
        result=usage.collect(document([row()],provider='local'),date(2026,11,1))
        self.assertEqual(result['records'][0]['model'],'Local models')
        self.assertNotIn('Claude Opus',json.dumps(result)+usage.panel(result))

    def test_new_cache_version_and_negative_counts_fail(self):
        source=document([row()]); source['version']=10
        with self.assertRaises(ValueError): usage.collect(source,date(2026,11,1))
        with self.assertRaises(ValueError): usage.collect(document([row(counts=(-1,0,0,0))]),date(2026,11,1))

    def test_bad_model_reference_and_incompatible_row_fail(self):
        with self.assertRaises(ValueError): usage.collect(document([row(model=999)]),date(2026,11,1))
        with self.assertRaises(ValueError): usage.collect(document([[1,2]]),date(2026,11,1))

    def test_public_schema_rejects_injected_field_or_label(self):
        result=usage.collect(document([row()]),date(2026,11,1))
        result['records'][0]['path']='private'
        with self.assertRaises(ValueError): usage.validate(result)
        del result['records'][0]['path']
        result['records'][0]['model']='private-local-7b'
        with self.assertRaises(ValueError): usage.validate(result)

    def test_no_records_preserves_previous_panel_by_failing(self):
        with self.assertRaises(ValueError): usage.collect(document([]),date(2026,11,1))

    def test_claude_synthetic_rows_are_removed_before_deduplication(self):
        source=document([row(model=2), row()])
        source['models'].append('<synthetic>')
        result=usage.collect(source,date(2026,11,1))
        self.assertEqual(dict(usage.metrics(result)[0]),{'Claude Code':42})

    def test_unknown_provider_never_reveals_even_public_looking_model(self):
        result=usage.collect(document([row()],provider='opencode'),date(2026,11,1))
        self.assertEqual(result['records'][0]['agent'],'Other agents')
        self.assertEqual(result['records'][0]['model'],'Other models')
        self.assertNotIn('Claude Opus',json.dumps(result)+usage.panel(result))

    def test_non_object_cache_fails_cleanly(self):
        with self.assertRaises(ValueError): usage.collect([],date(2026,11,1))


if __name__=='__main__': unittest.main()


class PanelLayoutTests(unittest.TestCase):
    def test_main_total_stays_below_page_title_scale(self):
        data=usage.collect(document([row()]),date(2026,11,1))
        for options,column in [({'mobile':True},440),({'compact_variant':True},545),
                               ({'medium':True},719),({},850)]:
            svg=usage.ET.fromstring(usage.panel(data,**options))
            total=usage.compact(sum(usage.metrics(data)[0].values()))
            label=next(e for e in svg.iter('{http://www.w3.org/2000/svg}text') if e.text==total)
            self.assertLessEqual(float(label.attrib['font-size'])*column/
                                 float(svg.attrib['viewBox'].split()[2]),32)

    def test_every_chart_variant_has_readable_labels_at_its_smallest_column(self):
        data = usage.collect(document([row()]), date(2026,11,1))
        for options, column in [({'mobile':True},280),({'compact_variant':True},408),
                                ({'medium':True},546),({},652)]:
            svg = usage.ET.fromstring(usage.panel(data, **options))
            scale = column / float(svg.attrib['viewBox'].split()[2])
            for label in svg.iter('{http://www.w3.org/2000/svg}text'):
                self.assertGreaterEqual(float(label.attrib['font-size'])*scale,11,
                                        (options,label.text))

    def test_chart_titles_stay_below_section_headings_at_largest_columns(self):
        data = usage.collect(document([row()]), date(2026,11,1))
        for options, column in [({'mobile':True},440),({'compact_variant':True},545),
                                ({'medium':True},719),({},850)]:
            svg = usage.ET.fromstring(usage.panel(data, **options))
            title = next(e for e in svg.iter('{http://www.w3.org/2000/svg}text')
                         if e.text == 'Uso de agentes')
            self.assertLessEqual(float(title.attrib['font-size'])*column/
                                 float(svg.attrib['viewBox'].split()[2]),24)

    def test_four_agents_leave_room_before_model_heading(self):
        data = usage.collect(document([row()]), date(2026,11,1))
        template = data['records'][0]
        entries = [('Claude Code','Claude Opus 5.5'), ('Codex','GPT-6.1 Sol'),
                   ('Local models','Local models'), ('Other agents','Other models')]
        data['records'] = [dict(template, agent=agent, model=model)
                           for agent, model in entries]
        svg = usage.ET.fromstring(usage.panel(data))
        texts = {}
        for element in svg.iter('{http://www.w3.org/2000/svg}text'):
            texts.setdefault(element.text, element)
        last_agent_y = max(float(texts[usage.DISPLAY_NAMES.get(agent,agent)].attrib['y'])
                           for agent, _ in entries)
        model_heading_y = float(texts['POR MODELO'].attrib['y'])
        self.assertGreaterEqual(model_heading_y-last_agent_y, 40)


class UsageTextTests(unittest.TestCase):
    def test_alt_contains_month_total_and_distribution(self):
        data = usage.collect(document([row()]), date(2026,11,1))
        text = usage.alternative_text(data)
        self.assertIn('out/2026', text)
        self.assertIn('42 tokens', text)
        self.assertIn('Claude Code 100%', text)
        self.assertNotIn('Modelos locais', text)

    def test_portuguese_compact_units(self):
        self.assertEqual(usage.compact(19_000_000_000), '19,0 bi')
        self.assertEqual(usage.compact(5_000), '5,0 mil')
        self.assertEqual(usage.compact(.5), '0,5')

    def test_local_alt_explains_aggregation_without_names(self):
        data = usage.collect(document([row()], provider='local'), date(2026,11,1))
        text = usage.alternative_text(data)
        self.assertIn('Modelos locais 100%', text)
        self.assertIn('Modelos locais agregados sem divulgar seus nomes.', text)
        self.assertNotIn('claude-opus', text)
        self.assertNotIn('private-local', text)

    def test_chart_scale_rounds_up_to_readable_boundaries(self):
        for value, expected in [(1,1),(5,5),(6,10),(999,1000),(1000,1000),(1_565_000_000,2_000_000_000)]:
            with self.subTest(value=value):
                self.assertEqual(usage.nice_max(value),expected)
