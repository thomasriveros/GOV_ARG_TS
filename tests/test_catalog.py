import unittest
from unittest.mock import patch

from scripts.update_data import CatalogChangedError, fetch_category


def page(count, *ids):
    return {"count": count, "data": [{"field": {"id": value}} for value in ids]}


class CatalogRetryTests(unittest.TestCase):
    @patch("scripts.update_data.time.sleep")
    @patch("scripts.update_data.search_page")
    def test_changed_count_restarts_and_discards_partial_records(self, search, sleep):
        search.side_effect = [
            page(2, "old"), page(2, "old"), *([page(3, "new")] * 6),
            page(3, "a"), page(3, "a"), page(3, "b"), page(3, "c"),
        ]
        result = fetch_category("api", 1, "theme", [])
        self.assertEqual([row["field"]["id"] for row in result], ["a", "b", "c"])
        self.assertEqual([call.args[2] for call in search.call_args_list],
                         [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2])
        sleep.assert_called_once_with(2)

    @patch("scripts.update_data.time.sleep")
    @patch("scripts.update_data.search_page")
    def test_alternate_ordering_recovers_without_restart(self, search, sleep):
        search.side_effect = [page(2), page(3), page(2, "a", "b")]
        result = fetch_category("api", 1000, "theme", [])
        self.assertEqual([row["field"]["id"] for row in result], ["a", "b"])
        self.assertTrue(all(call.args[1] == 1000 for call in search.call_args_list))
        sleep.assert_not_called()

    @patch("scripts.update_data.time.sleep")
    @patch("scripts.update_data.search_page")
    def test_persistent_count_changes_fail_after_three_attempts(self, search, sleep):
        search.side_effect = ([page(1, "a")] + [page(2, "a")] * 6) * 3
        with self.assertRaises(CatalogChangedError):
            fetch_category("api", 1, "theme", [])
        self.assertEqual(search.call_count, 21)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    @patch("scripts.update_data.time.sleep")
    @patch("scripts.update_data.search_page")
    def test_incomplete_unique_ids_still_fail(self, search, sleep):
        search.side_effect = [page(2, "a")] + [page(2, "a", "a")] * 6
        with self.assertRaisesRegex(RuntimeError, "recovered 1 unique series, expected 2"):
            fetch_category("api", 2, "theme", [])
        sleep.assert_not_called()

    @patch("scripts.update_data.time.sleep")
    @patch("scripts.update_data.fetch_unique_partition")
    @patch("scripts.update_data.search_page")
    def test_partition_total_mismatch_restarts_whole_category(self, search, fetch, sleep):
        search.side_effect = [page(10001), page(1), page(1), page(1)]
        fetch.side_effect = [[{"field": {"id": "old"}}],
                             [{"field": {"id": "new"}}]]
        result = fetch_category("api", 1000, "theme", ["catalog"])
        self.assertEqual(result, [{"field": {"id": "new"}}])
        sleep.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
