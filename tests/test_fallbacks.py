import unittest
from unittest.mock import patch

from db import DatabaseUnavailableError
import queries


class FallbackTests(unittest.TestCase):
    @patch("queries.run_query", side_effect=DatabaseUnavailableError("db down"))
    def test_list_roles_returns_demo_data_when_db_is_unavailable(self, _mock_run_query):
        roles = queries.list_roles()
        self.assertTrue(roles)
        self.assertIn("title", roles[0])

    @patch("queries.run_query", side_effect=DatabaseUnavailableError("db down"))
    def test_skill_gap_for_role_returns_demo_gap_when_db_is_unavailable(self, _mock_run_query):
        gaps = queries.skill_gap_for_role("Avery Chen", "Data Scientist")
        self.assertTrue(gaps)
        self.assertIn("skill", gaps[0])


if __name__ == "__main__":
    unittest.main()
