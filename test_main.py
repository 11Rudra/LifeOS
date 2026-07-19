import os
import unittest

os.environ["LIFEOS_DB_PATH"] = "/tmp/lifeos-test.db"

from main import app


class LifeOSTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_renders_lifeos(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LifeOS Command Center", response.data)

    def test_markdown_file_route_serves_content(self):
        response = self.client.get("/LifeOS/00-Dashboard.md")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Golden Rules", response.data)

    def test_entries_form_creates_and_lists_entry(self):
        response = self.client.post(
            "/entries",
            data={
                "title": "Morning Reflection",
                "category": "Reflection",
                "content": "I stayed consistent today.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Morning Reflection", response.data)
        self.assertIn(b"I stayed consistent today.", response.data)

    def test_weekly_planner_saves_time_inputs(self):
        response = self.client.post(
            "/planner",
            data={
                "plan-Monday-Health": "1.5",
                "plan-Monday-Family": "0.5",
                "plan-Monday-Career": "3",
                "plan-Saturday-Learning": "2",
                "plan-Sunday-Rest": "8",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Weekly Planner", response.data)
        self.assertIn(b"1.5", response.data)


if __name__ == "__main__":
    unittest.main()
