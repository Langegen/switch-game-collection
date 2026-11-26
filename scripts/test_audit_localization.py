import unittest
from audit_localization import audit_catalog, audit_homebrew, classify, identity_diff


class AuditTests(unittest.TestCase):
    def test_script_categories(self):
        for text, expected in [("中文说明", "han_present"), ("中文 описание", "cyrillic_review"),
                               ("English prose", "latin_review"), ("NSP / XCI", "neutral"),
                               ("2026-11-26", "neutral"), ("", "missing"), ("未知", "missing"),
                               ("123", "neutral")]:
            self.assertEqual(classify(text, "zh-Hans"), expected)
        self.assertEqual(classify("русский", "ru"), "other")

    def test_chinese_summary_not_counted_as_full_translation(self):
        self.assertEqual(classify("中文摘要（保留原文）：\n摘要\n\n原文：\nEnglish", "zh-Hans"),
                         "summary_with_original")

    def test_fields_and_indices(self):
        result = audit_catalog({"games": [{"title": "中文", "description": "English"},
                                         {"title": "Name", "description": "中文简介"}]}, "zh-Hans", True)
        self.assertEqual(result["entries"], 2)
        self.assertEqual(result["fields"]["description"],
                         {"han_present": 1, "latin_review": 1, "review_indices": [0]})

    def test_identity_diff_ignores_display_text(self):
        reference = [{"title_id": "id", "topic_id": "one", "title": "Name", "version": "1"}]
        candidate = [dict(reference[0], title="中文名称")]
        self.assertEqual(identity_diff(reference, candidate), {})
        candidate[0]["version"] = "2"
        self.assertEqual(identity_diff(reference, candidate), {"version": 1})
        self.assertTrue(identity_diff(reference, []))

    def test_homebrew_sections(self):
        index = {"packages": [{"description_i18n": {"zh-Hans": "简介"}}, {}],
                 "fortheusers": {"app": {"description_i18n": {"ru": "Описание"}}}}
        result = audit_homebrew(index)
        self.assertEqual(result["packages"], {"total": 2, "localized_description": 1,
                                              "missing_locale_description": 1})
        self.assertEqual(result["fortheusers"]["localized_description"], 0)


if __name__ == "__main__":
    unittest.main()
