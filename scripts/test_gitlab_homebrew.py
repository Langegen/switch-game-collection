import json
import unittest
from unittest.mock import patch

import homebrew_indexer as h

REPO = "example/compressor"
ID = 123
BASE = f"https://gitlab.com/{REPO}/-/"


def release(tag, links):
    return {"tag_name": tag, "released_at": "2026-11-26T00:00:00Z",
            "description": "Release", "assets": {"links": links}}


class GitLabReleaseTests(unittest.TestCase):
    def test_stable_only(self):
        links = [{"id": 3, "name": "Switch", "url": BASE + "uploads/abc/tool.nro"}]
        releases = [release("v2.0.0-test", links), release("v1.9.0", links),
                    release("v1.10.0", links)]
        with patch.object(h, "http_get", side_effect=[
            json.dumps({"path_with_namespace": REPO}).encode(), json.dumps(releases).encode()
        ]):
            result = h.latest_gitlab_release(REPO, ID)
        self.assertEqual(result["tag_name"], "v1.10.0")
        asset, problem = h.pick_asset(result, "*.nro")
        self.assertEqual(problem, "")
        self.assertEqual(asset["name"], "tool.nro")

    def test_approved_project_only(self):
        for url in ("http://gitlab.com/" + REPO + "/-/tool.nro",
                    "https://gitlab.com.evil.invalid/" + REPO + "/-/tool.nro",
                    "https://gitlab.com/other/project/-/tool.nro",
                    BASE + "%2e%2e/tool.nro",
                    "https://gitlab.com:8080/" + REPO + "/-/tool.nro"):
            self.assertFalse(h.gitlab_project_url(REPO, ID, url))
        self.assertTrue(h.gitlab_project_url(REPO, ID, BASE + "uploads/a/tool.nro"))
        self.assertTrue(h.gitlab_project_url(
            REPO, ID, f"https://gitlab.com/api/v4/projects/{ID}/packages/generic/tool/1.0/tool.nro"))

    def test_reject_ambiguous_or_non_nro(self):
        data = h.normalize_gitlab_release(release("1.0.0", [
            {"id": 1, "url": BASE + "a/tool.nro"},
            {"id": 2, "url": BASE + "b/other.nro"},
            {"id": 3, "url": BASE + "c/windows.zip"},
            {"id": 4, "url": "https://example.invalid/tool.nro"}
        ]), REPO, ID)
        self.assertEqual(len(data["assets"]), 2)
        asset, _ = h.pick_asset(data, "*.nro")
        self.assertIsNone(asset)

    def test_project_id_mismatch(self):
        with patch.object(h, "http_get", return_value=b'{"path_with_namespace":"other/project"}'):
            with self.assertRaises(ValueError):
                h.latest_gitlab_release(REPO, ID)

    def test_test_only_release(self):
        with patch.object(h, "http_get", side_effect=[
            json.dumps({"path_with_namespace": REPO}).encode(),
            json.dumps([release("v2.0.0-rc1", [])]).encode()
        ]):
            self.assertIsNone(h.latest_gitlab_release(REPO, ID))


if __name__ == "__main__":
    unittest.main()
