#!/usr/bin/env python3
"""Tests for statuspage.py.

Weighted toward the failure paths. A status page that renders is easy; one
that tells you when it could not read its input is the whole point.

    python3 test_statuspage.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("statuspage", HERE / "statuspage.py")
S = importlib.util.module_from_spec(spec)
sys.modules["statuspage"] = S
spec.loader.exec_module(S)


class TestParsing(unittest.TestCase):
    def test_a_well_formed_line(self):
        svc = S.parse_line("api ok handling traffic", 1)
        self.assertEqual((svc.name, svc.state, svc.note), ("api", "ok", "handling traffic"))

    def test_the_note_is_optional(self):
        self.assertEqual(S.parse_line("api ok", 1).note, "")

    def test_blank_and_comment_lines_are_skipped(self):
        self.assertIsNone(S.parse_line("", 1))
        self.assertIsNone(S.parse_line("   ", 1))
        self.assertIsNone(S.parse_line("# a comment", 1))

    def test_state_is_case_insensitive(self):
        self.assertEqual(S.parse_line("api OK", 1).state, "ok")

    def test_a_note_may_contain_spaces(self):
        self.assertEqual(S.parse_line("db degraded slow since 09:00", 1).note,
                         "slow since 09:00")


class TestFailuresAreReported(unittest.TestCase):
    """The behaviour this exists for: bad input is never silently dropped."""

    def test_an_unknown_state_is_an_error_not_a_guess(self):
        with self.assertRaises(S.ParseError) as ctx:
            S.parse_line("api probably-fine", 1)
        self.assertIn("probably-fine", str(ctx.exception))
        self.assertIn("line 1", str(ctx.exception))

    def test_a_line_with_no_state_is_an_error(self):
        with self.assertRaises(S.ParseError):
            S.parse_line("lonely-service", 1)

    def test_one_bad_line_does_not_hide_the_good_ones(self):
        services, errors = S.parse("api ok\nbroken\ndb down maintenance\n")
        self.assertEqual([s.name for s in services], ["api", "db"])
        self.assertEqual(len(errors), 1)

    def test_errors_name_their_line_number(self):
        _, errors = S.parse("api ok\n\nnonsense-line\n")
        self.assertIn("line 3", errors[0])


class TestRendering(unittest.TestCase):
    def test_the_page_is_self_contained(self):
        page = S.render([S.Service("api", "ok")], [])
        self.assertNotIn("http://", page)
        self.assertNotIn("<script", page)

    def test_names_and_notes_are_escaped(self):
        page = S.render([S.Service("<script>x</script>", "ok", "a & b")], [])
        self.assertNotIn("<script>x", page)
        self.assertIn("&amp;", page)

    def test_unreadable_lines_appear_on_the_page(self):
        page = S.render([], ["line 2: unknown state 'maybe'"])
        self.assertIn("Could not read", page)
        self.assertIn("unknown state", page)

    def test_no_error_section_when_there_are_none(self):
        self.assertNotIn("Could not read", S.render([S.Service("api", "ok")], []))

    def test_state_reaches_the_row_class(self):
        self.assertIn('class="down"', S.render([S.Service("api", "down")], []))


class TestGeneratedTimestamp(unittest.TestCase):
    """render() is handed the time, never the clock — see statuspage.py."""

    TS = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

    def test_no_timestamp_is_shown_when_none_is_supplied(self):
        self.assertNotIn("Page generated", S.render([S.Service("api", "ok")], []))

    def test_the_supplied_timestamp_appears_on_the_page(self):
        page = S.render([], [], self.TS)
        self.assertIn("2026-01-01 12:30:00 UTC", page)

    def test_the_label_distinguishes_generation_time_from_service_checks(self):
        page = S.render([], [], self.TS)
        self.assertIn("Page generated", page)
        self.assertIn("not when any service was last checked", page)


if __name__ == "__main__":
    unittest.main(verbosity=2)
