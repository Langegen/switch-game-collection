import copy
import unittest

from homebrew_localization import apply_zh_hans


class LocalizationTests(unittest.TestCase):
    def test_only_existing_entries_and_preserve_fields(self):
        index = {"packages": [{"repo": "Example/Tool", "sha256": "abc", "description": "Original",
                              "description_i18n": {"ru": "Описание"}}],
                 "fortheusers": {"Tool": {"kinds": ["app"]}}, "hidden": ["hidden"]}
        original = copy.deepcopy(index)
        overrides = {"packages": {"example/tool": "中文说明", "other/tool": "不应添加"},
                     "fortheusers": {"tool": "工具说明", "hidden": "不应添加"}}
        self.assertEqual(apply_zh_hans(index, overrides), {"packages": 1, "fortheusers": 1})
        self.assertEqual(index["packages"][0]["description_i18n"].pop("zh-Hans"), "中文说明")
        self.assertEqual(index["fortheusers"]["Tool"].pop("description_i18n"), {"zh-Hans": "工具说明"})
        self.assertEqual(index, original)

    def test_preserve_existing_translation_and_retry_blank(self):
        index = {"packages": [{"repo": "a/b", "description_i18n": {"zh-Hans": "已审核"}},
                              {"repo": "a/c", "description_i18n": {"zh-Hans": " "}}]}
        overrides = {"packages": {"a/b": "新内容", "a/c": "补充"}}
        self.assertEqual(apply_zh_hans(index, overrides)["packages"], 1)
        self.assertEqual(index["packages"][0]["description_i18n"]["zh-Hans"], "已审核")
        self.assertEqual(index["packages"][1]["description_i18n"]["zh-Hans"], "补充")
        self.assertEqual(apply_zh_hans(index, overrides)["packages"], 0)

    def test_missing_override_is_noop(self):
        index = {"packages": [{"repo": "a/b"}], "fortheusers": {"x": {}}}
        original = copy.deepcopy(index)
        self.assertEqual(apply_zh_hans(index, {}), {"packages": 0, "fortheusers": 0})
        self.assertEqual(index, original)


if __name__ == "__main__":
    unittest.main()
