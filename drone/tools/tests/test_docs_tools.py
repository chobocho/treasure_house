# -*- coding: utf-8 -*-
"""1차 문서 도구의 시험 (PLAN.md §3.1, §0.14) — html_text·
pdf_sections·fetch_docs·excerpt.

픽스처는 2026-09-25 에 받은 진짜 문서의 발췌다(tools/tests/fixtures/).
기대값은 그 원문을 눈으로 읽어 적었다. 네트워크는 쓰지 않는다 —
받기(get)와 GitHub API 는 make docs 가 실제로 돌려 본다.

    python3 -m unittest discover -s tools/tests
"""
import hashlib
import io
import os
import sys
import tempfile
import shutil
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.dirname(HERE))

import excerpt       # noqa: E402
import fetch_docs    # noqa: E402
import html_text     # noqa: E402
import pdf_sections  # noqa: E402


def fixture(name):
    with io.open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def heads(text):
    return [l[2:] for l in text.split('\n') if l.startswith('§\t')]


def lines(text):
    return text.split('\n')


# ------------------------------------------------------------ HTML
class Px4Page(unittest.TestCase):
    """vitepress — <main> 안만, 제목의 id 는 '#id' 절 줄이 된다."""

    def setUp(self):
        self.t = html_text.convert(
            fixture('px4_controller_diagrams.html'))

    def test_headings_and_anchors_in_order(self):
        self.assertEqual(heads(self.t), [
            '#controller-diagrams', 'Controller Diagrams',
            '#multicopter-control-architecture',
            'Multicopter Control Architecture',
            '#multicopter-angular-rate-controller',
            'Multicopter Angular Rate Controller'])

    def test_list_item_line(self):
        self.assertIn('- This is a standard cascaded control '
                      'architecture.', lines(self.t))

    def test_inline_code_stays_in_its_line(self):
        self.assertTrue(any('low-pass filter (IMU_GYRO_CUTOFF)' in l
                            for l in lines(self.t)))

    def test_nav_footer_script_style_dropped(self):
        for junk in ('Introduction', 'Edit on GitHub', 'tracking-code',
                     'color:red', '​', '¶'):
            self.assertNotIn(junk, self.t)


class ArduPilotPage(unittest.TestCase):
    """Sphinx(rtd) — <section id> 가 절 줄, 제목의 ¶ 는 버린다."""

    def setUp(self):
        self.t = html_text.convert(
            fixture('ardupilot_tuning_process.html'))

    def test_section_anchor_then_heading(self):
        self.assertEqual(heads(self.t)[:2],
                         ['#tuning-process-instructions',
                          'Tuning Process Instructions'])

    def test_span_label_is_not_an_anchor(self):
        self.assertNotIn('#id1', heads(self.t))

    def test_ordered_list(self):
        self.assertIn('- Initial tuning flight to obtain a stable, but '
                      'not necessarily optimized, tune.', lines(self.t))

    def test_side_nav_and_footer_dropped(self):
        self.assertNotIn('Copter', heads(self.t))
        self.assertNotIn('Previous', self.t)
        self.assertNotIn('¶', self.t)


class MavlinkPage(unittest.TestCase):
    def setUp(self):
        self.t = html_text.convert(
            fixture('mavlink_serialization.html'))

    def test_headings(self):
        h = heads(self.t)
        for want in ('Packet Serialization', '#packet_format',
                     'Packet Format', '#crc_extra',
                     'CRC_EXTRA Calculation'):
            self.assertIn(want, h)

    def test_pre_is_verbatim(self):
        ls = lines(self.t)
        self.assertIn('def message_checksum(msg):', ls)
        self.assertIn('    crc = x25crc()', ls)

    def test_table_row_joined_with_bars(self):
        self.assertTrue(any(l.startswith('0 | uint8_t magic | Packet '
                                         'start marker | 0xFD | ')
                            for l in lines(self.t)), self.t)

    def test_copy_button_dropped(self):
        self.assertNotIn('Copy Code', self.t)


class SkybrushPage(unittest.TestCase):
    """Antora — <dt> 는 절 줄. CSV 가져오기 형식이 여기 있다."""

    def setUp(self):
        self.t = html_text.convert(fixture('skybrush_formations.html'))

    def test_dt_and_h2_headings(self):
        h = heads(self.t)
        for want in ('Formations panel', 'From static CSV file',
                     'From zipped CSV files', '#_create_takeoff_grid',
                     'Create Takeoff Grid'):
            self.assertIn(want, h)

    def test_csv_format_line(self):
        self.assertTrue(any(l.endswith(
            'linear color space): Name, x_m, y_m, z_m, Red, Green, '
            'Blue') for l in lines(self.t)), self.t)

    def test_breadcrumbs_and_aside_dropped(self):
        self.assertNotIn('Tabs and panels', self.t)
        self.assertNotIn('Skybrush Studio for Blender', heads(self.t))


class BlenderPage(unittest.TestCase):
    """Sphinx(furo) — API 항목 <dt id> 가 '#bpy.types…' 절 줄이 된다."""

    def setUp(self):
        self.t = html_text.convert(fixture('blender_object.html'))

    def test_object_anchors(self):
        h = heads(self.t)
        for want in ('#object-id', 'Object(ID)', '#bpy.types.Object',
                     'class bpy.types.Object(ID)',
                     '#bpy.types.Object.location', 'location'):
            self.assertIn(want, h)

    def test_field_list_dt_is_not_a_heading(self):
        self.assertNotIn('Type:', heads(self.t))
        self.assertIn('Type:', lines(self.t))

    def test_example_code_verbatim(self):
        ls = lines(self.t)
        self.assertIn('light_object.location = (5.0, 5.0, 5.0)', ls)
        self.assertIn('# Create new light data-block.', ls)

    def test_sidebar_dropped(self):
        self.assertNotIn('ObjectBase', self.t)


class FaaPage(unittest.TestCase):
    def setUp(self):
        self.t = html_text.convert(fixture('faa_part107_waivers.html'))

    def test_headings(self):
        self.assertEqual(heads(self.t), [
            'Part 107 Waivers', 'How to Apply for a Part 107 Waiver',
            'Step 1: Determine what you need.'])

    def test_waiver_table_row(self):
        self.assertTrue(any(
            l.startswith('Fly a small UAS from a moving aircraft') and
            '§ 107.25 Operation from a moving vehicle or aircraft' in l
            for l in lines(self.t)), self.t)

    def test_sidebar_header_footer_dropped(self):
        for junk in ('In This Section', 'Main navigation',
                     '800 Independence', 'How to Register Your Drone'):
            self.assertNotIn(junk, self.t)


class EasaPage(unittest.TestCase):
    def setUp(self):
        self.t = html_text.convert(fixture('easa_open_category.html'))

    def test_headings_without_block_ids(self):
        # EASA 본문 제목은 h5 다 — 그래서 h5·h6 도 제목으로 센다
        self.assertEqual(heads(self.t), [
            'Open Category — Low Risk — Civil Drones',
            'Table for ‘Open’ category applicable since '
            '1 January 2024'])

    def test_subcategory_list(self):
        self.assertIn('- A1: fly over people but not over assemblies '
                      'of people', lines(self.t))

    def test_breadcrumb_dropped(self):
        self.assertNotIn('You are here', self.t)


# ------------------------------------------------------------ XML
class EcfrXml(unittest.TestCase):
    def setUp(self):
        self.t = html_text.convert_ecfr(fixture('ecfr_part107.xml'))

    def test_part_subpart_section_heads(self):
        self.assertEqual(heads(self.t), [
            'PART 107—SMALL UNMANNED AIRCRAFT SYSTEMS',
            'Subpart B—Operating Rules', '#107.29',
            '§ 107.29 Operation at night.'])

    def test_paragraph_lines(self):
        ls = lines(self.t)
        self.assertIn('(3) In Alaska, the period of civil twilight as '
                      'defined in the Air Almanac.', ls)
        self.assertIn('Authority: 49 U.S.C. 106(f), 40101 note, '
                      '40103(b), 44701(a)(5), 46105(c), 46110, 44807.',
                      ls)

    def test_metadata_attributes_not_in_text(self):
        self.assertNotIn('SUBSTITUTE_DATE', self.t)
        self.assertNotIn('hierarchy', self.t)


class LawXml(unittest.TestCase):
    """law.go.kr DRF lawService XML — 장·조문이 절 줄이 된다."""

    def setUp(self):
        self.t = html_text.convert_law(
            fixture('law_aviation_safety_act.xml'))

    def test_heads(self):
        self.assertEqual(heads(self.t), [
            '항공안전법', '제10장 초경량비행장치',
            '제125조', '제125조(초경량비행장치 조종자 증명 등)',
            '제129조', '제129조(초경량비행장치 조종자 등의 준수사항)',
            '제131조의2', '제131조의2(무인비행장치의 적용 특례)'])

    def test_dates_line(self):
        self.assertEqual(lines(self.t)[1:2],
                         ['공포 2026-06-16 · 공포번호 제21822호 · '
                          '시행 2026-09-17'])

    def test_paragraph_item_subitem(self):
        ls = lines(self.t)
        self.assertTrue(any(l.startswith('⑤ 제1항에도 불구하고 ') and
                            l.endswith('<신설 2017.8.9>') for l in ls))
        self.assertIn('3의3. 제4항을 위반하여 다음 각 목의 어느 하나에 '
                      '해당하는 행위를 알선한 경우', ls)
        self.assertTrue(any(l.startswith('가. 다른 사람에게 ')
                            for l in ls))
        self.assertIn('[본조신설 2017.8.9]', ls)


# ------------------------------------------------------------ PDF
class PdfSections(unittest.TestCase):
    def test_two_column_paper_detected(self):
        self.assertEqual(pdf_sections.columns(
            fixture('pdf_lee_layout.txt')), 2)
        self.assertEqual(pdf_sections.columns(
            fixture('pdf_madgwick_layout.txt')), 1)

    def test_paper_headings(self):
        t = pdf_sections.sections(fixture('pdf_lee_text.txt'))
        self.assertEqual(heads(t), [
            'I. INTRODUCTION', 'II. QUADROTOR DYNAMICS MODEL',
            'VII. NUMERICAL RESULTS ILLUSTRATING COMPLEX FLIGHT '
            'MANEUVERS',
            'APPENDIX', 'A. Properties of the Hat Map', 'REFERENCES'])

    def test_numbered_list_sentence_is_not_a_heading(self):
        t = pdf_sections.sections(fixture('pdf_lee_text.txt'))
        self.assertIn('1. This is a system of four identical rotors '
                      'and propellers', lines(t))

    def test_report_headings_skip_table_of_contents(self):
        t = pdf_sections.sections(fixture('pdf_madgwick_layout.txt'))
        self.assertEqual(heads(t), [
            'Abstract', 'Contents', '1 Introduction',
            '3 Filter derivation', '3.1 Orientation from angular rate',
            '3.2 Orientation from vector observations',
            '3.4 Magnetic distortion compensation',
            '3.5 Gyroscope bias drift compensation'])

    def test_formula_debris_is_not_a_heading(self):
        # 논문 전체를 돌려 보니 나온 오탐(2026-09-25)
        for junk in ('1 T T', '2 Ω d', 'S          C      M      S'):
            self.assertIsNone(pdf_sections.heading(junk), junk)

    def test_abbreviation_inside_title(self):
        self.assertEqual(
            pdf_sections.heading('5.3    Filter gain vs. performance'),
            ('5.3 Filter gain vs. performance', False))

    def test_form_feed_removed(self):
        t = pdf_sections.sections('a\fb\n')
        self.assertNotIn('\f', t)


# ------------------------------------------------------------ 소스
class CodeText(unittest.TestCase):
    def test_px4_functions(self):
        src = fixture('px4_attitude_control.cpp')
        t = fetch_docs.code_text('AttitudeControl.cpp', src, 'c')
        self.assertEqual(heads(t), [
            'AttitudeControl.cpp', 'qmul', 'qinv', 'qzaxis',
            'AttitudeControl::setProportionalGain',
            'AttitudeControl::setRefModelFrequency',
            'AttitudeControl::setAttitudeSetpoint',
            'AttitudeControl::propagateReferenceModel'])

    def test_heading_sits_right_before_definition(self):
        src = fixture('px4_attitude_control.cpp')
        ls = lines(fetch_docs.code_text('a.cpp', src, 'c'))
        self.assertIn('§\tAttitudeControl::setRefModelFrequency', ls)
        k = ls.index('§\tAttitudeControl::setRefModelFrequency')
        self.assertTrue(ls[k + 1].startswith(
            'void AttitudeControl::setRefModelFrequency('))

    def test_betaflight_macros_are_not_functions(self):
        src = fixture('betaflight_pid.c')
        t = fetch_docs.code_text('pid.c', src, 'c')
        self.assertEqual(heads(t), ['pid.c', 'resetPidProfile',
                                    'handleCrashRecovery'])

    def test_source_lines_unchanged(self):
        src = fixture('betaflight_pid.c')
        t = fetch_docs.code_text('pid.c', src, 'c')
        body = [l for l in lines(t) if not l.startswith('§\t')]
        self.assertEqual('\n'.join(body), src)

    def test_xml_kept_verbatim_with_name_line(self):
        t = fetch_docs.code_text('common.xml', '<a>\n  <b/>\n</a>\n',
                                 'xml')
        self.assertEqual(t, '§\tcommon.xml\n<a>\n  <b/>\n</a>\n')

    def test_comment_block_is_skipped(self):
        src = '/*\nvoid f(int x)\n{\n*/\nint g(void)\n{\n}\n'
        self.assertEqual(heads(fetch_docs.code_text('x.c', src, 'c')),
                         ['x.c', 'g'])


# ------------------------------------------------------------ 받기
class Dispatch(unittest.TestCase):
    def test_detect(self):
        d = fetch_docs.detect
        self.assertEqual(d('https://x/a.pdf', b'%PDF-1.5\n'), 'pdf')
        self.assertEqual(d('https://arxiv.org/pdf/1003.2005',
                           b'%PDF-1.4'), 'pdf')
        self.assertEqual(d('https://r/x/AttitudeControl.cpp',
                           b'/**\n'), 'c')
        self.assertEqual(d('https://r/x/pid.c', b'#include'), 'c')
        self.assertEqual(d('https://r/x/checksum.h', b'#pragma'), 'c')
        self.assertEqual(d('https://r/x/mavcrc.py', b"'''"), 'text')
        self.assertEqual(d('https://r/README.md', b'# Crazyflie'), 'md')
        self.assertEqual(d('https://www.ecfr.gov/api/x?part=107',
                           b'<?xml version="1.0"?>\n<DIV5 N="107"'),
                         'ecfr')
        self.assertEqual(d('https://www.law.go.kr/DRF/lawService.do',
                           '<?xml version="1.0"?>\n<법령 법령키="1">'
                           .encode('utf-8')), 'law')
        self.assertEqual(d('https://r/common.xml',
                           b'<?xml version="1.0"?>\n<mavlink>'), 'xml')
        self.assertEqual(d('https://api.crossref.org/works/10.1/x',
                           b' {"status":"ok"}'), 'json')
        self.assertEqual(d('https://docs.px4.io/x',
                           b'<!DOCTYPE html>\n<html>'), 'html')
        self.assertEqual(d('https://x/y', b'<!doctype html><html>'),
                         'html')

    def test_raw_path(self):
        r = fetch_docs.raw_path
        self.assertEqual(r('px4/AttitudeControl.cpp.txt', 'c'),
                         'raw/px4/AttitudeControl.cpp')
        self.assertEqual(r('mavlink/common.xml.txt', 'xml'),
                         'raw/mavlink/common.xml')
        self.assertEqual(r('faa/waivers.txt', 'html'),
                         'raw/faa/waivers.html')
        self.assertEqual(r('law/aviation-safety-act.txt', 'law'),
                         'raw/law/aviation-safety-act.xml')
        self.assertEqual(r('paper/lee2010.txt', 'pdf'),
                         'raw/paper/lee2010.pdf')
        self.assertEqual(r('paper/capt.txt', 'json'),
                         'raw/paper/capt.json')

    def test_convert_dispatch(self):
        c = fetch_docs.convert
        self.assertEqual(heads(c('html', b'<main><h2>T</h2></main>',
                                 'a.html')), ['T'])
        self.assertEqual(heads(c('md', b'# Title\ntext\n', 'R.md')),
                         ['Title'])
        self.assertEqual(c('json', b'{"a": 1}', 'capt.json'),
                         '§\tcapt.json\n{"a": 1}\n')
        self.assertEqual(heads(c('c', b'int f(void)\n{\n}\n', 'f.c')),
                         ['f.c', 'f'])

    def test_fetched_line(self):
        line = fetch_docs.fetched_line('px4/a.txt', 'https://x/a',
                                       '2026-09-25', b'abc', 'A b')
        self.assertEqual(line.split('\t'), [
            'px4/a.txt', 'https://x/a', '2026-09-25',
            hashlib.sha256(b'abc').hexdigest(), 'A b'])

    def test_first_heading_skips_anchors(self):
        self.assertEqual(fetch_docs.first_heading(
            '§\t#controller-diagrams\n§\tController Diagrams\n'),
            'Controller Diagrams')
        self.assertEqual(fetch_docs.first_heading('\n  hello\n'),
                         'hello')


class Keys(unittest.TestCase):
    HEAD = 'key\tname\turl\tkind\tlicence\tfile\n'

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix='drone-keys-')
        self.p = os.path.join(self.d, 'cite_keys.tsv')

    def tearDown(self):
        shutil.rmtree(self.d)

    def write(self, body):
        with io.open(self.p, 'w', encoding='utf-8') as f:
            f.write(self.HEAD + body)

    def test_good_table(self):
        self.write('# 주석\na\tA\thttps://x/a\tdoc\t-\ta.txt\n'
                   'b\tB\thttps://x/b\tcode\tGPL-3.0\tb/b.c.txt\n')
        rows, bad = fetch_docs.read_keys(self.p)
        self.assertEqual(bad, [])
        self.assertEqual([r['key'] for r in rows], ['a', 'b'])

    def test_bad_rows_reported(self):
        self.write('a\tA\thttps://x/a\tblog\t-\ta.txt\n'
                   'b\tB\thttps://x/b\tdoc\t-\tb.html\n'
                   'c\tC\t\tdoc\t-\tc.txt\n'
                   'a\tA2\thttps://x/a2\tdoc\t-\ta2.txt\n'
                   'e\tE\thttps://x/e\tdoc\t-\ta.txt\n')
        rows, bad = fetch_docs.read_keys(self.p)
        self.assertEqual(len(bad), 5, bad)

    def test_select(self):
        rows = [dict(key='a', file='a.txt'),
                dict(key='b', file='b.txt')]
        s = fetch_docs.select
        self.assertEqual([r['key'] for r in s(rows, None, False,
                                              lambda r: True)],
                         ['a', 'b'])
        self.assertEqual([r['key'] for r in s(rows, 'b', False,
                                              lambda r: True)], ['b'])
        self.assertEqual([r['key'] for r in s(
            rows, None, True, lambda r: r['key'] == 'a')], ['b'])
        with self.assertRaises(KeyError):
            s(rows, 'zz', False, lambda r: True)


# ------------------------------------------------------------ 발췌
class Excerpt(unittest.TestCase):
    SHA = '0123456789abcdef0123456789abcdef01234567'

    def test_parse_pinned_raw_url(self):
        u = ('https://raw.githubusercontent.com/PX4/PX4-Autopilot/'
             + self.SHA + '/src/modules/a/AttitudeControl.cpp')
        self.assertEqual(excerpt.parse_raw_url(u), dict(
            repo='PX4/PX4-Autopilot', sha=self.SHA,
            path='src/modules/a/AttitudeControl.cpp'))

    def test_branch_url_is_refused(self):
        with self.assertRaises(ValueError):
            excerpt.parse_raw_url('https://raw.githubusercontent.com/'
                                  'a/b/main/x.c')
        with self.assertRaises(ValueError):
            excerpt.parse_raw_url('https://github.com/a/b/blob/x.c')

    def test_header_per_language(self):
        h = excerpt.header
        a = ('PX4/PX4-Autopilot', 'src/a.cpp', self.SHA, 139, 178,
             'BSD-3-Clause', '2026-09-25')
        self.assertEqual(h('cpp', *a),
                         '// PX4/PX4-Autopilot src/a.cpp @' + self.SHA
                         + ' L139-178 · BSD-3-Clause · fetched '
                         '2026-09-25')
        self.assertTrue(h('py', *a).startswith('# PX4/'))
        x = h('xml', *a)
        self.assertTrue(x.startswith('<!-- PX4/'))
        self.assertTrue(x.endswith(' -->'))
        with self.assertRaises(ValueError):
            h('rs', *a)

    def test_cut_bounds(self):
        text = ''.join('l%d\n' % i for i in range(1, 101))
        self.assertEqual(excerpt.cut(text, 3, 5), ['l3', 'l4', 'l5'])
        self.assertEqual(len(excerpt.cut(text, 1, 40)), 40)
        for a, b in ((1, 41), (0, 3), (5, 4), (90, 101)):
            with self.assertRaises(ValueError):
                excerpt.cut(text, a, b)

    def test_render_is_header_plus_lines(self):
        out = excerpt.render('c', 'a/b', 'x.c', self.SHA, 2, 3, 'MIT',
                             '2026-09-25', 'l1\nl2\nl3\n')
        ls = out.split('\n')
        self.assertTrue(ls[0].startswith('// a/b x.c @'))
        self.assertEqual(ls[1:], ['l2', 'l3', ''])

    def test_index_round_trip(self):
        d = tempfile.mkdtemp(prefix='drone-ex-')
        try:
            p = os.path.join(d, 'INDEX.tsv')
            row = dict(key='k', repo='a/b', path='x.c', sha=self.SHA,
                       start='2', end='3', licence='MIT',
                       why='왜 이 창인가')
            excerpt.write_index(p, [row])
            self.assertEqual(excerpt.read_index(p), [row])
            excerpt.write_index(p, excerpt.upsert(
                [row], dict(row, end='9')))
            self.assertEqual(excerpt.read_index(p)[0]['end'], '9')
        finally:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
