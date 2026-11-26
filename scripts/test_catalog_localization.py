import unittest
from unittest.mock import patch

import build_catalogs as b


class CatalogLocalizationTests(unittest.TestCase):
    def setUp(self):
        self.cfg = b.LANG_CONFIGS["zh-hans"]

    def test_english_description_in_chinese_catalog(self):
        item = {"description": "Explore the island."}
        upstream = {"description": "Explore the island."}
        self.assertEqual(b.localized_description(item, upstream, self.cfg, {
            "Explore the island.": "探索岛屿。"}), "探索岛屿。")
        self.assertEqual(b.localized_description(item, upstream, self.cfg, {}),
                         "Explore the island.")

    def test_latin_only_translation_cache_is_not_chinese_prose(self):
        source = "Explore the island."
        cache = {source: "Explore the wonderful island."}
        self.assertIsNone(b.cached_translation(source, cache, target_lang="zh-CN", prose=True))
        self.assertEqual(b.localized_description({"description": source}, {}, self.cfg, cache), source)
        self.assertEqual(b.localized_description({"description": source}, {}, self.cfg, {source: "探索岛屿。"}), "探索岛屿。")
        self.assertTrue(b.needs_translation("Long English prose that has not been translated 中文", "zh-CN", prose=True))

    def test_native_description_preferred(self):
        self.assertEqual(b.localized_description(
            {"description": "English prose"}, {"description": "中文简介"},
            self.cfg, {}), "中文简介")

    def test_translation_cache_retry(self):
        text = "Новый режим"
        self.assertIsNone(b.cached_translation(text, {text: b.transliterate(text)}))
        self.assertIsNone(b.cached_translation(text, {text: ""}))
        self.assertIsNone(b.cached_translation(text, {text: text}))
        self.assertEqual(b.text_from_cache(text, {}), text)
        self.assertEqual(b.text_from_cache(text, {text: "新模式"}), "新模式")

    def test_rule_pass_preserves_remaining_notes(self):
        raw = "Необычная пометка"
        self.assertEqual(b.translate_interface_lang(raw, self.cfg, {}), raw)
        self.assertEqual(b.translate_interface_lang(raw, self.cfg, {raw: "特殊备注"}), "特殊备注")

    def test_network_failure_not_cached(self):
        text = "Новый режим"
        with patch.object(b.urllib.request, "urlopen", side_effect=OSError("offline")), \
                patch.object(b.time, "sleep"):
            self.assertEqual(b.fetch_translation_single(text, "zh-CN"), (text, None))
        cache = {text: b.transliterate(text)}
        with patch.object(b, "fetch_translation_single", return_value=(text, None)), \
                patch.object(b, "save_cache"):
            b.batch_preload_translations([text], cache, "unused", "zh-CN", max_workers=1)
        self.assertNotIn(text, cache)

    def test_exact_title_keeps_suffix(self):
        self.assertEqual(b.exact_localized_title("Example Game [NSP] [v2]",
                                               "示例游戏", "Example Game"),
                         "示例游戏 [NSP] [v2]")
        self.assertIsNone(b.exact_localized_title("Example Game Deluxe [NSP]",
                                                 "示例游戏", "Example Game"))
        self.assertIsNone(b.exact_localized_title("Example Game (Demo)",
                                                 "示例游戏", "Example Game"))


if __name__ == "__main__":
    unittest.main()
