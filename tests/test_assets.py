"""Contratos de segurança do movimento nos SVGs públicos."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'build_assets', Path(__file__).resolve().parents[1] / 'scripts/build_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class MotionTests(unittest.TestCase):
    def test_animation_rules_without_their_elements_are_rejected(self):
        svg=assets.focus().replace('class="signal"','class="disconnected"')
        self.assertTrue(assets.problems('focus.svg',svg))

    def test_decorative_loops_keep_reduced_motion_and_static_alternative(self):
        self.assertEqual(assets.problems('banner.svg',assets.banner()),[])
        readme=(assets.ROOT/'README-static.md').read_text(encoding='utf-8')
        references=assets.re.findall(r'(?:src|srcset)="assets/([^\"]+)"',readme)
        for reference in references:
            svg=(assets.ASSETS/reference).read_text(encoding='utf-8')
            self.assertIsNone(assets.re.search(r'animation:\s*(?!none\b)[^;]+;',svg),reference)

    def test_all_three_sizes_require_every_motion_component(self):
        for family, variants in [('banner',[assets.banner,assets.banner_medium,assets.banner_mobile]),
                                 ('focus',[assets.focus,lambda:assets.focus_mobile(True),assets.focus_mobile])]:
            for index,generate in enumerate(variants):
                svg=generate()
                self.assertEqual(assets.problems(f'{family}-{index}.svg',svg),[])
                frozen=assets.re.sub(r'animation:[^;]+;', 'animation:none;',svg)
                self.assertTrue(assets.problems(f'{family}-{index}.svg',frozen))
                self.assertEqual(assets.problems(f'{family}-{index}-still.svg',frozen),[])

    def test_generated_assets_meet_motion_contract(self):
        for svg in (assets.banner(), assets.banner_mobile(), assets.focus(), assets.focus_mobile()):
            with self.subTest(svg=svg[:80]):
                self.assertEqual(assets.problems('generated.svg', svg), [])

    def test_infinite_opening_is_rejected(self):
        svg = assets.banner().replace('typing 3.2s steps(34,end) 1 both','typing 3.2s steps(34,end) infinite both')
        self.assertTrue(assets.problems('infinite.svg', svg))

    def test_five_seconds_is_rejected(self):
        svg = assets.banner().replace('typing 3.2s','typing 5s')
        self.assertTrue(assets.problems('long.svg', svg))

    def test_delayed_animation_must_finish_before_five_seconds(self):
        svg = assets.banner().replace('typing 3.2s', 'typing 4s 2s')
        self.assertTrue(assets.problems('delayed.svg', svg))

    def test_missing_reduced_motion_is_rejected(self):
        svg = assets.banner().replace('prefers-reduced-motion', 'unknown-motion')
        self.assertTrue(assets.problems('no-reduce.svg', svg))

    def test_animation_rename_preserves_delay_validation(self):
        svg = assets.banner().replace('typing', 'write').replace('3.2s', '4s 2s')
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
        svg = assets.banner().replace('animation:typing 3.2s steps(34,end) 1 both;', 'animation:typing 3s linear 2500ms 1;')
        self.assertTrue(assets.problems('shorthand-delay.svg', svg))

    def test_css_delay_counts_toward_total(self):
        svg = assets.banner().replace('animation:typing 3.2s steps(34,end) 1 both;', 'animation:typing 4.8s linear 1; animation-delay:500ms;')
        self.assertTrue(assets.problems('css-delay.svg', svg))

    def test_banner_scale_matches_across_medium_desktop(self):
        self.assertIn(assets.BANNER_ALT, assets.banner_medium())
        self.assertIn('400 34px',assets.banner_medium())
        self.assertGreaterEqual(34*408/900,15)

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
