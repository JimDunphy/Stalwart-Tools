import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest
from datetime import timezone


def load_smmailbox_module():
    smmailbox_path = pathlib.Path(__file__).resolve().parents[1] / "smmailbox"
    loader = importlib.machinery.SourceFileLoader("smmailbox", str(smmailbox_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


SM = load_smmailbox_module()


class TestSmMailboxCalendars(unittest.TestCase):
    def test_calendar_folder_name_mapping(self) -> None:
        self.assertEqual(
            SM.zimbra_calendar_folder_to_calendar_name(
                SM.ZimbraCalendarFolder(folder_id="11", name="Work", abs_folder_path="/Calendar/Work")
            ),
            "Work",
        )
        self.assertEqual(
            SM.zimbra_calendar_folder_to_calendar_name(
                SM.ZimbraCalendarFolder(folder_id="12", name="Nested", abs_folder_path="/Calendar/Work/Nested")
            ),
            "Work/Nested",
        )
        self.assertEqual(
            SM.zimbra_calendar_folder_to_calendar_name(
                SM.ZimbraCalendarFolder(folder_id="10", name="Calendar", abs_folder_path="/Calendar")
            ),
            "Calendar",
        )

    def test_parse_iso_datetime(self) -> None:
        self.assertEqual(SM.parse_iso_datetime("2026-01-01").hour, 0)
        self.assertEqual(SM.parse_iso_datetime("2026-01-01T12:34:56").minute, 34)
        dt = SM.parse_iso_datetime("2026-01-01T00:00:00Z")
        self.assertIsNotNone(dt.tzinfo)

    def test_local_to_utc(self) -> None:
        # UTC passthrough
        dt = SM.jmap_local_datetime_to_utc("2026-01-01T00:00:00Z", "Etc/UTC")
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_default_calendar_selection_prefers_tz(self) -> None:
        calendars = [
            {"id": "b", "name": "Stalwart Calendar (user@example.com)"},
            {"id": "c", "name": "Work", "timeZone": "America/Vancouver"},
        ]
        self.assertEqual(SM.jmap_default_calendar_id(calendars), "c")

        calendars = [
            {"id": "x", "name": "X", "timeZone": "America/Vancouver"},
            {"id": "y", "name": "Y", "isDefault": True},
        ]
        self.assertEqual(SM.jmap_default_calendar_id(calendars), "y")

    def test_create_from_parsed_drops_alerts(self) -> None:
        parsed = {
            "start": "2026-01-01T00:00:00",
            "duration": "PT1H",
            "timeZone": "Etc/UTC",
            "uid": "u1",
            "title": "t",
            "alerts": {"k1": {"action": "email"}},
        }
        create = SM.jmap_calendar_event_create_from_parsed(parsed, calendar_id="cal1", stable_uid="u1")
        self.assertNotIn("alerts", create)
        self.assertEqual(create["calendarIds"], {"cal1": True})

    def test_calendar_dedupe_key_ignores_uid(self) -> None:
        parsed = {
            "start": "2026-01-01T00:00:00",
            "duration": "PT1H",
            "timeZone": "Etc/UTC",
            "title": "t",
        }
        a = SM.jmap_calendar_event_create_from_parsed(parsed, calendar_id="cal1", stable_uid="u1")
        b = SM.jmap_calendar_event_create_from_parsed(parsed, calendar_id="cal1", stable_uid="u2")
        self.assertEqual(SM.calendar_event_dedupe_key(a), SM.calendar_event_dedupe_key(b))


if __name__ == "__main__":
    unittest.main()
