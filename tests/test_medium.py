import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

from medium_engine import (
    clean_text,
    extract_tags,
    build_medium_payload,
    load_state,
    save_state
)

class TestMediumSyndicator(unittest.TestCase):

    def test_clean_text(self):
        raw = "<p>Analyzing <strong>autonomous systems</strong> &amp; governance</p>"
        self.assertEqual(clean_text(raw), "Analyzing autonomous systems & governance")

    def test_extract_tags(self):
        categories = ["Artificial Intelligence", "Robotics!", "AI Ethics & Society", "Future", "Policy", "Extra"]
        tags = extract_tags(categories)
        self.assertLessEqual(len(tags), 5)
        for t in tags:
            self.assertNotIn("!", t)
            self.assertLessEqual(len(t), 25)

    def test_build_medium_payload(self):
        post = {
            "title": "Autonomous Robotics & Legal Frameworks",
            "link": "https://aviperera.com/autonomous-robotics-frameworks/",
            "content_html": "<p>A deep forensic breakdown of legal liabilities.</p>",
            "categories": ["AI Ethics", "Legal"]
        }
        payload = build_medium_payload(post, publish_status="public")

        self.assertEqual(payload["title"], "Autonomous Robotics & Legal Frameworks")
        self.assertEqual(payload["contentFormat"], "html")
        self.assertEqual(payload["canonicalUrl"], "https://aviperera.com/autonomous-robotics-frameworks/")
        self.assertIn("https://aviperera.com/autonomous-robotics-frameworks/", payload["content"])
        self.assertIn("aviperera.com", payload["content"])
        self.assertEqual(payload["publishStatus"], "public")
        self.assertTrue(payload["notifyFollowers"])

    def test_load_and_save_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_state_file = os.path.join(tmpdir, "state", "medium_history.json")
            with patch("medium_engine.STATE_FILE", test_state_file):
                state = load_state()
                self.assertEqual(state["syndicated"], {})

                state["syndicated"]["post-1"] = {
                    "title": "Sample Post",
                    "canonical_url": "https://aviperera.com/post-1",
                    "medium_id": "med-123"
                }
                save_state(state)

                reloaded = load_state()
                self.assertIn("post-1", reloaded["syndicated"])
                self.assertEqual(reloaded["syndicated"]["post-1"]["medium_id"], "med-123")

if __name__ == "__main__":
    unittest.main()
