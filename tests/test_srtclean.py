# -*- coding: utf-8 -*-
"""Tes srt-cleaner: parser, tiap langkah pembersihan, dan CLI end-to-end."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from srtclean.clean import clean_all
from srtclean.cli import main
from srtclean.parser import format_time, parse_srt, render_srt

BASIC = """1
00:00:01,000 --> 00:00:04,000
Halo, dunia!

2
00:00:05,000 --> 00:00:08,000
Baris kedua.
"""


class TestParser(unittest.TestCase):
    def test_parse_basic(self):
        cues = parse_srt(BASIC)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start, 1000)
        self.assertEqual(cues[0].end, 4000)
        self.assertEqual(cues[0].lines, ["Halo, dunia!"])

    def test_parse_bom_crlf(self):
        cues = parse_srt("\ufeff1\r\n00:00:01,000 --> 00:00:02,000\r\nHai!\r\n")
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].lines, ["Hai!"])

    def test_parse_missing_index(self):
        cues = parse_srt("00:00:01,000 --> 00:00:02,000\nTanpa nomor.\n")
        self.assertEqual(len(cues), 1)
        self.assertIsNone(cues[0].index)

    def test_parse_bad_timestamp_raises(self):
        with self.assertRaises(ValueError):
            parse_srt("1\nkemarin --> besok\nTeks.\n")

    def test_format_time(self):
        self.assertEqual(format_time(3661001), "01:01:01,001")
        self.assertEqual(format_time(0), "00:00:00,000")


class TestCleaning(unittest.TestCase):
    def _clean(self, text, **opts):
        return clean_all(parse_srt(text), opts)

    def test_strip_html(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\n<i>Miring</i> dan <b>tebal</b> &amp; teman.\n")
        self.assertEqual(cues[0].lines, ["Miring dan tebal & teman."])
        self.assertEqual(st["tags"], 4)

    def test_strip_brackets(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\n[MUSIK] Halo [tawa] dunia.\n")
        self.assertEqual(cues[0].lines, ["Halo dunia."])
        self.assertEqual(st["brackets"], 2)

    def test_paren_whole_line_dropped_inline_kept(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:03,000\n(suara pintu)\nDia bilang (pelan) halo.\n")
        self.assertEqual(cues[0].lines, ["Dia bilang (pelan) halo."])
        self.assertEqual(st["paren_lines"], 1)

    def test_speaker_label(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\nBUDI: Selamat pagi.\n")
        self.assertEqual(cues[0].lines, ["Selamat pagi."])
        self.assertEqual(st["labels"], 1)

    def test_not_a_label(self):
        cues, _ = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\nHalo: apa kabar?\n")
        self.assertEqual(cues[0].lines, ["Halo: apa kabar?"])

    def test_empty_cue_dropped(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\n[MUSIK]\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\nMasih ada.\n")
        self.assertEqual(len(cues), 1)
        self.assertEqual(st["empty"], 1)

    def test_dedup_merges(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:02,000\nSama.\n\n"
            "2\n00:00:02,500 --> 00:00:04,000\nSama.\n")
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].end, 4000)
        self.assertEqual(st["merged"], 1)

    def test_overlap_fixed(self):
        cues, st = self._clean(
            "1\n00:00:01,000 --> 00:00:05,000\nPertama.\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nKedua.\n")
        self.assertEqual(cues[0].end, 4000)
        self.assertEqual(st["timing"], 1)

    def test_negative_duration_fixed(self):
        cues, st = self._clean(
            "1\n00:00:05,000 --> 00:00:04,000\nTerbalik.\n")
        self.assertEqual(cues[0].end, 6000)
        self.assertEqual(st["timing"], 1)

    def test_renumber(self):
        cues, _ = self._clean(
            "7\n00:00:01,000 --> 00:00:02,000\n[MUSIK]\n\n"
            "9\n00:00:03,000 --> 00:00:04,000\nHalo.\n")
        self.assertEqual(render_srt(cues).split("\n")[0], "1")


class TestCLI(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "kotor.srt")
            with open(src, "w", encoding="utf-8") as f:
                f.write("1\n00:00:01,000 --> 00:00:02,000\n<i>[MUSIK] Halo.</i>\n")
            self.assertEqual(main([src, "-o", os.path.join(d, "bersih.srt")]), 0)
            with open(os.path.join(d, "bersih.srt"), encoding="utf-8") as f:
                self.assertIn("Halo.", f.read())
                self.assertNotIn("<i>", f.read())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "kotor.srt")
            with open(src, "w", encoding="utf-8") as f:
                f.write(BASIC)
            self.assertEqual(main([src, "--dry-run"]), 0)
            self.assertFalse(os.path.exists(os.path.join(d, "kotor.clean.srt")))

    def test_missing_file_exit_2(self):
        self.assertEqual(main(["/tidak/ada.srt"]), 2)


if __name__ == "__main__":
    unittest.main()
