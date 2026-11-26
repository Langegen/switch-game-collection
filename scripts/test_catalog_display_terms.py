import unittest
from catalog_display_terms import apply_display_terms, translate_genre_terms


class DisplayTermsTests(unittest.TestCase):
    def test_genre_preserves_order_and_unknowns(self):
        mapping = {"action": "动作", "adventure": "冒险", "rpg": "角色扮演 (RPG)"}
        self.assertEqual(translate_genre_terms("Action, Adventure / RPG; Unknown Tag", mapping),
                         "动作, 冒险 / 角色扮演 (RPG); Unknown Tag")
        self.assertEqual(translate_genre_terms("动作、Adventure", mapping), "动作、冒险")
        self.assertIsNone(translate_genre_terms(None, mapping))

    def test_only_display_fields_change(self):
        record = {"genre": "Action", "voice_lang": "Angliyskaya", "title_id": "id", "version": "1", "title": "Original"}
        changed = apply_display_terms(record, {"genre": {"action": "动作"}, "voice_lang": {"angliyskaya": "英语"}})
        self.assertEqual(changed, ["genre", "voice_lang"])
        self.assertEqual(record, {"genre": "动作", "voice_lang": "英语", "title_id": "id", "version": "1", "title": "Original"})

    def test_exact_source_translation_and_existing_chinese(self):
        terms = {"description": {"Original": "中文译文", "Source": "已审核的翻译"}}
        record = {"description": "Transliterated"}
        self.assertEqual(apply_display_terms(record, terms, "Source"), ["description"])
        self.assertEqual(record["description"], "已审核的翻译")
        self.assertEqual(apply_display_terms(record, terms, "Source"), [])
        self.assertEqual(apply_display_terms({"description": "Unmatched"}, terms), [])


if __name__ == "__main__":
    unittest.main()
