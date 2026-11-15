"""Contratos de segurança do movimento nos SVGs públicos."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'build_assets', Path(__file__).resolve().parents[1] / 'scripts/build_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class MotionTests(unittest.TestCase):
    def test_generated_assets_meet_motion_contract(self):
        for svg in (assets.banner(), assets.banner_mobile(), assets.focus(), assets.focus_mobile()):
            with self.subTest(svg=svg[:80]):
                self.assertEqual(assets.problems('generated.svg', svg), [])

    def test_infinite_motion_is_rejected(self):
        svg = assets.banner().replace('linear 1 forwards', 'linear infinite forwards')
        self.assertTrue(assets.problems('infinite.svg', svg))

    def test_five_seconds_is_rejected(self):
        svg = assets.banner().replace('4.8s', '5s')
        self.assertTrue(assets.problems('long.svg', svg))

    def test_delayed_animation_must_finish_before_five_seconds(self):
        svg = assets.banner().replace('3.8s', '4.5s')
        self.assertTrue(assets.problems('delayed.svg', svg))

    def test_missing_reduced_motion_is_rejected(self):
        svg = assets.banner().replace('prefers-reduced-motion', 'unknown-motion')
        self.assertTrue(assets.problems('no-reduce.svg', svg))
