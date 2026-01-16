import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest


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


class MergeImportedFilterRulesTests(unittest.TestCase):
    def test_import_inactive_by_default(self):
        existing = []
        imported = [{"name": "A", "active": True}, {"name": "B", "active": False}]
        out, actions = SM.merge_imported_filter_rules(
            existing_rules=existing, imported_rules=imported, preserve_active=False, force=False
        )
        self.assertEqual(actions, ["create: A", "create: B"])
        self.assertEqual(len(out), 2)
        self.assertFalse(out[0]["active"])
        self.assertFalse(out[1]["active"])

    def test_overwrite_existing_inactive_same_name(self):
        existing = [{"name": "A", "active": False, "filterTests": [{"condition": "anyof"}]}]
        imported = [{"name": "A", "active": True, "filterTests": [{"condition": "allof"}]}]
        out, actions = SM.merge_imported_filter_rules(
            existing_rules=existing, imported_rules=imported, preserve_active=False, force=False
        )
        self.assertEqual(actions, ["update: A"])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["name"], "A")
        self.assertFalse(out[0]["active"])
        self.assertEqual(out[0]["filterTests"][0]["condition"], "allof")

    def test_conflict_active_creates_variant(self):
        existing = [{"name": "A", "active": True}]
        imported = [{"name": "A", "active": True, "filterActions": [{"actionStop": [{}]}]}]
        out, actions = SM.merge_imported_filter_rules(
            existing_rules=existing, imported_rules=imported, preserve_active=False, force=False
        )
        self.assertEqual(actions, ["create: A(1)"])
        self.assertEqual({r["name"] for r in out}, {"A", "A(1)"})
        a1 = next(r for r in out if r["name"] == "A(1)")
        self.assertFalse(a1["active"])

    def test_conflict_updates_existing_variant(self):
        existing = [{"name": "A", "active": True}, {"name": "A(1)", "active": False, "x": 1}]
        imported = [{"name": "A", "active": True, "x": 2}]
        out, actions = SM.merge_imported_filter_rules(
            existing_rules=existing, imported_rules=imported, preserve_active=False, force=False
        )
        self.assertEqual(actions, ["update: A(1)"])
        a1 = next(r for r in out if r["name"] == "A(1)")
        self.assertEqual(a1["x"], 2)

    def test_conflict_both_active_errors(self):
        existing = [{"name": "A", "active": True}, {"name": "A(1)", "active": True}]
        imported = [{"name": "A", "active": True}]
        with self.assertRaises(SystemExit):
            SM.merge_imported_filter_rules(
                existing_rules=existing, imported_rules=imported, preserve_active=False, force=False
            )

    def test_force_overwrites_active_base(self):
        existing = [{"name": "A", "active": True, "x": 1}]
        imported = [{"name": "A", "active": True, "x": 2}]
        out, actions = SM.merge_imported_filter_rules(
            existing_rules=existing, imported_rules=imported, preserve_active=True, force=True
        )
        self.assertEqual(actions, ["update: A"])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["x"], 2)
        self.assertTrue(out[0]["active"])


if __name__ == "__main__":
    unittest.main()
