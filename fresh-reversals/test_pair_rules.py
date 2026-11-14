"""Rules that decide which ADR links are reversals."""

import unittest

from pair_rules import classify_links, pairs_in_repo, resolve_target


OLD = "docs/adr/0001-use-postgres.md"
NEW = "docs/adr/0004-use-mysql.md"


def text_with(status: str, body: str = "") -> str:
    return f"# Use a database\n\n## Status\n\n{status}\n\n## Context\n\n{body}\n"


class LinkRuleTest(unittest.TestCase):
    def test_status_link_counts_and_a_cross_reference_does_not(self):
        text = text_with(
            "Superseded by [ADR 4](0004-use-mysql.md).",
            "See [ADR 3](0003-cache.md) for the cache.",
        )
        known = {"0004-use-mysql.md", "0003-cache.md"}
        accepted, rejected = classify_links(text, known)
        self.assertEqual(rejected, 1)
        self.assertEqual(len(accepted), 1)
        self.assertIn("0004-use-mysql.md", accepted[0]["url"])

    def test_sentence_with_replaced_wording_counts(self):
        text = (
            "# Move the API\n\n## Context\n\n"
            "The public API was replaced by [ADR 4](0004-use-mysql.md) after the review.\n"
            "See [ADR 3](0003-cache.md) for background.\n"
        )
        accepted, rejected = classify_links(text, {"0004-use-mysql.md", "0003-cache.md"})
        self.assertEqual(rejected, 1)
        self.assertEqual(accepted[0]["url"], "0004-use-mysql.md")

    def test_pair_resolves_the_new_adr(self):
        records = [
            {"path": OLD, "text": text_with("Superseded by [ADR 4](0004-use-mysql.md).")},
            {"path": NEW, "text": "# Use MySQL\n\n## Status\n\nAccepted\n\n## Context\n\nMySQL stores the orders.\n"},
            {"path": "docs/adr/0003-cache.md", "text": "# Cache\n\n## Status\n\nAccepted\n"},
        ]
        found, rejected, unresolved = pairs_in_repo(records)
        self.assertEqual(rejected, 0)
        self.assertEqual(unresolved, 0)
        self.assertEqual(found[0]["new_adr"], NEW)

    def test_resolve_relative_link(self):
        paths = [OLD, NEW]
        self.assertEqual(resolve_target("[ADR 4](0004-use-mysql.md)", OLD, paths), NEW)


if __name__ == "__main__":
    unittest.main()
