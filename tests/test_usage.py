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
        public = json.dumps(result)+usage.panel(result)+usage.panel(result,True)+usage.panel(result,medium=True)
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
