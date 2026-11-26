import unittest
from catalog_reviewed_metadata import apply_reviewed_metadata, has_chinese_prose, SUMMARY_PREFIX


class ReviewedMetadataTests(unittest.TestCase):
    def setUp(self):
        self.data = {"titles": {"sample game": {"title_ids": ["010000000000A000"],
                    "display_name": "示例游戏", "summary": "探索岛屿。"}},
                    "entities": {"nintendo": "任天堂"}}

    def test_exact_match_preserves_original(self):
        r = {"title": "Sample Game [v2]", "title_id": "010000000000A000",
             "description": "Explore the island.", "publisher": "Nintendo", "version": "2"}
        self.assertEqual(apply_reviewed_metadata(r, self.data), ["title", "description", "publisher"])
        self.assertEqual(r["title"], "示例游戏 / Sample Game [v2]")
        self.assertEqual(r["description"], SUMMARY_PREFIX + "\n探索岛屿。\n\n原文：\nExplore the island.")
        self.assertEqual(r["publisher"], "任天堂（Nintendo）")
        self.assertEqual(r["version"], "2")
        self.assertEqual(apply_reviewed_metadata(r, self.data), [])

    def test_reject_wrong_id_and_edition(self):
        for title, tid in (("Sample Game", "010000000000B000"),
                           ("Sample Game Deluxe", "010000000000A000")):
            r = {"title": title, "title_id": tid, "description": "Original"}
            self.assertEqual(apply_reviewed_metadata(r, self.data), [])

    def test_existing_chinese_description_is_not_replaced(self):
        r = {"title": "Sample Game", "title_id": "010000000000A000", "description": "已有中文简介"}
        self.assertEqual(apply_reviewed_metadata(r, self.data), ["title"])
        self.assertEqual(r["description"], "已有中文简介")

    def test_script_detection_does_not_accept_latin_prose_with_one_han(self):
        self.assertTrue(has_chinese_prose("一款 RPG 游戏"))
        self.assertFalse(has_chinese_prose("Long English prose that is clearly not translated 中文"))
        self.assertFalse(has_chinese_prose("Описание 中文"))
        self.assertFalse(has_chinese_prose(None))


if __name__ == "__main__":
    unittest.main()
