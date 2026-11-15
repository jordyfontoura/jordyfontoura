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

    def test_animation_rename_preserves_delay_validation(self):
        svg = assets.banner().replace('activate', 'spark').replace('3.8s', '4.5s')
        self.assertTrue(assets.problems('renamed.svg', svg))

    def test_every_animated_class_must_be_disabled(self):
        svg = assets.banner().replace('.neuron,.orbit,.packet,.reveal,.caret { animation:none;', '.orbit,.packet,.reveal,.caret { animation:none;')
        self.assertTrue(assets.problems('partial-reduce.svg', svg))

    def test_medium_banner_stays_horizontal(self):
        svg = assets.banner_medium()
        document = assets.xml.dom.minidom.parseString(svg)
        root = document.documentElement
        self.assertGreaterEqual(float(root.getAttribute('width')) / float(root.getAttribute('height')), 2)

    def test_shorthand_delay_counts_toward_total(self):
        svg = assets.focus().replace('animation: flow 4.8s linear 1;', 'animation: flow 3s linear 2500ms 1;')
        self.assertTrue(assets.problems('shorthand-delay.svg', svg))

    def test_css_delay_counts_toward_total(self):
        svg = assets.focus().replace('animation: flow 4.8s linear 1;', 'animation: flow 4.8s linear 1; animation-delay:500ms;')
        self.assertTrue(assets.problems('css-delay.svg', svg))

    def test_banner_scale_matches_across_medium_desktop(self):
        self.assertEqual(assets.banner(), assets.banner_medium())

    def test_typing_advances_one_complete_character_per_step(self):
        svg = assets.banner()
        document = assets.xml.dom.minidom.parseString(svg)
        command = next(e for e in document.getElementsByTagName('text') if e.hasAttribute('textLength'))
        content = ''.join(node.data for node in command.childNodes if node.nodeType == node.TEXT_NODE)
        steps = assets.re.search(r'animation:typing[^;]*steps\((\d+),end\)', svg)
        self.assertEqual(int(steps[1]), len(content))
        mask = next(e for e in document.getElementsByTagName('rect') if e.getAttribute('class') == 'reveal')
        self.assertEqual(float(mask.getAttribute('width')), float(command.getAttribute('textLength')))
        self.assertEqual(command.getAttribute('lengthAdjust'), 'spacing')
