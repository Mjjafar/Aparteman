from django.test import SimpleTestCase
from django.conf import settings


class SettingsTest(SimpleTestCase):
    def test_persian_sqlite_settings(self):
        self.assertEqual(settings.LANGUAGE_CODE, "fa-ir")
        self.assertEqual(settings.TIME_ZONE, "Asia/Tehran")
        self.assertIn("sqlite3", settings.DATABASES["default"]["ENGINE"])
        name = str(settings.DATABASES["default"]["NAME"])
        # Django swaps in an in-memory DB while tests run; accept both.
        self.assertTrue(name.endswith("db.sqlite3") or "memory" in name)
