import copy
import unittest
from regenerate_zh_hans_display import transform


class RegenerateDisplayTests(unittest.TestCase):
    def test_transform_preserves_order_original_data_and_identity(self):
        source = [{"title": "Sample [v2]", "title_id": "010000000000A000",
                   "genre": "Action, RPG", "description": "Explore the island.",
                   "publisher": "Nintendo", "version": "2", "topic_id": "one"}]
        before = copy.deepcopy(source)
        terms = {"genre": {"action": "动作", "rpg": "角色扮演"}}
        reviewed = {"titles": {"sample": {"title_ids": ["010000000000A000"],
                    "display_name": "示例游戏", "summary": "探索岛屿。"}},
                    "entities": {"nintendo": "任天堂"}}
        result, report = transform(source, terms, reviewed)
        self.assertEqual(source, before)
        self.assertEqual(list(result[0]), list(source[0]))
        self.assertEqual(result[0]["title"], "示例游戏 / Sample [v2]")
        self.assertEqual(result[0]["genre"], "动作, 角色扮演")
        self.assertEqual(result[0]["version"], "2")
        self.assertEqual(result[0]["topic_id"], "one")
        self.assertEqual(report["changed_records"], 1)
        self.assertEqual(report["non_display_field_differences"], 0)
        self.assertEqual(transform(result, terms, reviewed)[1]["changed_records"], 0)

    def test_empty_input(self):
        self.assertEqual(transform([], {}, {})[0], [])


if __name__ == "__main__":
    unittest.main()
