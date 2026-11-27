import unittest
from catalog_display_terms import apply_display_terms


class DisplayTermsTests(unittest.TestCase):
    def test_genre_left_untouched_and_display_fields_change(self):
        record = {
            "genre": "Action, Homebrew",
            "voice_lang": "Angliyskaya",
            "interface_lang": "multi [multi8]",
            "multiplayer": "1-4kh",
            "performance": "da (9.0.1 + atmosfera)",
            "title_id": "id",
            "version": "1",
            "title": "Original",
        }
        terms = {
            "genre": {"action": "动作"},
            "voice_lang": {"angliyskaya": "英语"},
            "interface_lang": {"multi [multi8]": "多语言 [MULTI8]"},
            "multiplayer": {"1-4kh": "1-4 人"},
            "performance": {"da (9.0.1 + atmosfera)": "支持（9.0.1 + Atmosfera）"},
        }
        changed = apply_display_terms(record, terms)
        self.assertEqual(changed, ["interface_lang", "voice_lang", "multiplayer", "performance"])
        self.assertEqual(record["genre"], "Action, Homebrew")
        self.assertEqual(record["voice_lang"], "英语")
        self.assertEqual(record["interface_lang"], "多语言 [MULTI8]")
        self.assertEqual(record["multiplayer"], "1-4 人")
        self.assertEqual(record["performance"], "支持（9.0.1 + Atmosfera）")
        self.assertEqual(record["title_id"], "id")
        self.assertEqual(record["version"], "1")
        self.assertEqual(record["title"], "Original")

    def test_exact_source_translation_and_existing_chinese(self):
        terms = {"description": {"Original": "中文译文", "Source": "已审核的翻译"}}
        record = {"description": "Transliterated"}
        self.assertEqual(apply_display_terms(record, terms, "Source"), ["description"])
        self.assertEqual(record["description"], "已审核的翻译")
        self.assertEqual(apply_display_terms(record, terms, "Source"), [])
        self.assertEqual(apply_display_terms({"description": "Unmatched"}, terms), [])


if __name__ == "__main__":
    unittest.main()
