"""Contratos de segurança do movimento nos SVGs públicos."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'build_assets', Path(__file__).resolve().parents[1] / 'scripts/build_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class MotionTests(unittest.TestCase):
    def opening(self):
        return assets.banner().replace('</style>', '.intro {animation:typing 3.2s steps(34,end) 1 both;} @media (prefers-reduced-motion: reduce) {.intro {animation:none;}}</style>').replace('</svg>', '<rect class="intro" width="1" height="1"/></svg>')

    def test_animation_rules_without_their_elements_are_rejected(self):
        svg=assets.banner().replace('class="companion-idle"','class="disconnected"')
        self.assertTrue(assets.problems('banner.svg',svg))

    def test_decorative_loops_keep_reduced_motion_and_static_alternative(self):
        self.assertEqual(assets.problems('banner.svg',assets.banner()),[])
        readme=(assets.ROOT/'README-static.md').read_text(encoding='utf-8')
        references=assets.re.findall(r'(?:src|srcset)="assets/([^\"]+)"',readme)
        for reference in references:
            svg=(assets.ASSETS/reference).read_text(encoding='utf-8')
            self.assertIsNone(assets.re.search(r'animation:\s*(?!none\b)[^;]+;',svg),reference)

    def test_all_three_sizes_require_every_motion_component(self):
        for family, variants in [('banner',[assets.banner,assets.banner_medium,assets.banner_compact,assets.banner_mobile])]:
            for index,generate in enumerate(variants):
                svg=generate()
                self.assertEqual(assets.problems(f'{family}-{index}.svg',svg),[])
                frozen=assets.re.sub(r'animation:[^;]+;', 'animation:none;',svg)
                self.assertTrue(assets.problems(f'{family}-{index}.svg',frozen))
                self.assertEqual(assets.problems(f'{family}-{index}-still.svg',frozen),[])

    def test_generated_assets_meet_motion_contract(self):
        for svg in (assets.banner(), assets.banner_mobile(), assets.banner_medium(), assets.banner_compact()):
            with self.subTest(svg=svg[:80]):
                self.assertEqual(assets.problems('generated.svg', svg), [])

    def test_infinite_opening_is_rejected(self):
        svg = self.opening().replace('typing 3.2s steps(34,end) 1 both','typing 3.2s steps(34,end) infinite both')
        self.assertTrue(assets.problems('infinite.svg', svg))

    def test_five_seconds_is_rejected(self):
        svg = self.opening().replace('typing 3.2s','typing 5s')
        self.assertTrue(assets.problems('long.svg', svg))

    def test_delayed_animation_must_finish_before_five_seconds(self):
        svg = self.opening().replace('typing 3.2s', 'typing 4s 2s')
        self.assertTrue(assets.problems('delayed.svg', svg))

    def test_missing_reduced_motion_is_rejected(self):
        svg = assets.banner().replace('prefers-reduced-motion', 'unknown-motion')
        self.assertTrue(assets.problems('no-reduce.svg', svg))

    def test_animation_rename_preserves_delay_validation(self):
        svg = self.opening().replace('typing', 'write').replace('3.2s', '4s 2s')
        self.assertTrue(assets.problems('renamed.svg', svg))

    def test_every_animated_class_must_be_disabled(self):
        svg = assets.banner().replace('.companion-idle,.companion-antenna,.companion-cursor,.companion-shadow,.companion-aerial,.companion-command,.companion-confirmation,.companion-context,.companion-tools,.companion-product { animation:none;', '.companion-antenna,.companion-cursor,.companion-shadow,.companion-aerial,.companion-command,.companion-confirmation,.companion-context,.companion-tools,.companion-product { animation:none;')
        self.assertTrue(assets.problems('partial-reduce.svg', svg))

    def test_antenna_and_terminal_stay_with_the_floating_companion(self):
        for generate in [assets.banner, assets.banner_medium, assets.banner_compact, assets.banner_mobile]:
            document = assets.xml.dom.minidom.parseString(generate())
            body = next(e for e in document.getElementsByTagName('g')
                        if e.getAttribute('class') == 'companion-idle')
            children = {e.getAttribute('class') for e in body.getElementsByTagName('*')}
            self.assertTrue({'companion-mast', 'companion-antenna', 'companion-prompt',
                             'companion-cursor', 'companion-outline'} <= children)

    def test_medium_banner_stays_horizontal(self):
        svg = assets.banner_medium()
        document = assets.xml.dom.minidom.parseString(svg)
        root = document.documentElement
        self.assertGreaterEqual(float(root.getAttribute('width')) / float(root.getAttribute('height')), 2)

    def test_shorthand_delay_counts_toward_total(self):
        svg = self.opening().replace('animation:typing 3.2s steps(34,end) 1 both;', 'animation:typing 3s linear 2500ms 1;')
        self.assertTrue(assets.problems('shorthand-delay.svg', svg))

    def test_css_delay_counts_toward_total(self):
        svg = self.opening().replace('animation:typing 3.2s steps(34,end) 1 both;', 'animation:typing 4.8s linear 1; animation-delay:500ms;')
        self.assertTrue(assets.problems('css-delay.svg', svg))

    def test_medium_banner_text_is_readable_in_narrow_profile_column(self):
        svg=assets.banner_medium()
        document=assets.xml.dom.minidom.parseString(svg)
        width=float(document.documentElement.getAttribute('viewBox').split()[2])
        self.assertIn(assets.BANNER_ALT,svg)
        for label in ['body']:
            font=assets.re.search(r'\.'+label+r'\s*\{\s*font:\d+\s+([\d.]+)px',svg)
            self.assertIsNotNone(font,label)
            self.assertGreaterEqual(float(font[1])*546/width,15,label)

    def test_desktop_banner_type_is_proportional_to_markdown(self):
        svg=assets.banner()
        width=float(assets.xml.dom.minidom.parseString(svg).documentElement.getAttribute('viewBox').split()[2])
        # Coluna larga do perfil; o corpo do Markdown tem 16 px na prévia.
        for label,maximum in [('body',20),('name',40)]:
            font=assets.re.search(r'\.'+label+r'\s*\{\s*font:\d+\s+([\d.]+)px',svg)
            self.assertIsNotNone(font,label)
            self.assertLessEqual(float(font[1])*850/width,maximum,label)

    def test_static_banner_descriptions_do_not_claim_motion(self):
        for variant in ['','-mobile','-medium','-compact']:
            svg=(assets.ASSETS/f'banner{variant}-still.svg').read_text(encoding='utf-8')
            document=assets.xml.dom.minidom.parseString(svg)
            description=document.getElementsByTagName('desc')[0].firstChild.data
            self.assertIn('sem animação',description)
            self.assertNotIn('movimento contínuo',description)

    def test_static_readme_offers_return_to_animated_version(self):
        text=(assets.ROOT/'README-static.md').read_text(encoding='utf-8')
        self.assertIn('[Com animação](',text)
        self.assertNotIn('[Sem animação](',text)

    def test_personal_banner_has_no_cv_copy_or_opening_mask(self):
        for generate in [assets.banner, assets.banner_medium, assets.banner_compact, assets.banner_mobile]:
            svg = generate()
            for forbidden in ['Engenheiro de IA', 'desde 2018', 'laboratório', 'contexto →', 'command-mask']:
                self.assertNotIn(forbidden, svg)
            self.assertIn('RPG Maker', svg)

    def test_static_companion_shows_prompt_and_hides_confirmation(self):
        for suffix in ['', '-mobile', '-medium', '-compact']:
            svg = (assets.ASSETS/f'banner{suffix}-still.svg').read_text(encoding='utf-8')
            self.assertIn('.companion-confirmation { opacity:0; animation:none;', svg)
            self.assertIn('.companion-command { animation:none;', svg)
            self.assertIsNone(assets.re.search(r'animation:\s*(?!none\b)[^;]+;', svg))
