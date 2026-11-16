"""Contratos de escala entre os textos primários dos SVGs e o Markdown."""
import math
from pathlib import Path
from runpy import run_path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
measure=run_path(str(ROOT/'scripts/svg_typography.py'))['text_metrics']
EXTREMES={'mobile':(280,440),'compact':(408,545),'medium':(546,719),'desktop':(652,850)}

PROJECT_EXTREMES={'mobile':(280,400),'desktop':(400,400)}


class TypographyTests(unittest.TestCase):
    def test_intermediate_project_body_stays_near_markdown_scale(self):
        for key in ['skills','tryless','gitclean','np','argus']:
            path=ROOT/f'assets/project-{key}.svg'
            for row in measure(path.read_text(encoding='utf-8'),400):
                if 'body' in row['classes']:
                    self.assertLessEqual(row['displayFontSize'],19.2,(path.name,row))

    def test_project_labels_are_readable_in_the_smallest_column(self):
        for path in (ROOT/'assets').glob('project-*.svg'):
            mobile='-mobile' in path.stem
            for row in measure(path.read_text(encoding='utf-8'),280 if mobile else 400):
                self.assertGreaterEqual(row['displayFontSize'],13,(path.name,row))


    def test_every_generated_svg_text_is_measurable(self):
        for path in (ROOT/'assets').glob('*.svg'):
            rows=measure(path.read_text(encoding='utf-8'),850)
            self.assertTrue(rows,path.name)
            self.assertTrue(all(math.isfinite(r['displayFontSize']) and r['displayFontSize']>0 for r in rows),path.name)

    def test_primary_body_text_at_both_extremes_of_every_variant(self):
        primary={'body'}
        for path in (ROOT/'assets').glob('*.svg'):
            if '-still' in path.stem or path.stem.startswith('agent-usage'):
                continue
            ranges=PROJECT_EXTREMES if path.stem.startswith('project-') else EXTREMES
            variant=path.stem.rsplit('-',1)[-1]
            variant=variant if variant in ranges else 'desktop'
            for width in ranges[variant]:
                rows=[r for r in measure(path.read_text(encoding='utf-8'),width) if primary.intersection(r['classes'])]
                self.assertTrue(rows,(path.name,width))
                for row in rows:
                    self.assertGreaterEqual(row['displayFontSize'],14 if variant=='mobile' else 15,(path.name,width,row))
                    self.assertLessEqual(row['displayFontSize'],22.01 if variant=='mobile' else 20.1,(path.name,width,row))

    def test_component_titles_do_not_dominate_markdown_section_headings(self):
        for family in ['project-skills','project-tryless','project-gitclean','project-np','project-argus']:
            ranges=PROJECT_EXTREMES
            for variant,widths in ranges.items():
                suffix='' if variant=='desktop' else '-'+variant
                svg=(ROOT/f'assets/{family}{suffix}.svg').read_text(encoding='utf-8')
                for width in widths:
                    for row in measure(svg,width):
                        if {'name'}.intersection(row['classes']):
                            self.assertLessEqual(row['displayFontSize'],24.1,(family,variant,width,row))

    def test_banner_name_keeps_its_hierarchy(self):
        for variant,widths in EXTREMES.items():
            suffix='' if variant=='desktop' else '-'+variant
            svg=(ROOT/f'assets/banner{suffix}.svg').read_text(encoding='utf-8')
            for width in widths:
                name=next(r for r in measure(svg,width) if 'name' in r['classes'])
                self.assertGreaterEqual(name['displayFontSize'],24,(variant,width))
                self.assertLessEqual(name['displayFontSize'],40.1,(variant,width))
