"""Rules that decide which ADR links are reversals."""

import unittest

from pair_rules import (
    choose_best_commit,
    classify_links,
    filename_has_number,
    has_status_section,
    is_foreign_copy,
    is_general_folder_path,
    is_template_file,
    pairs_in_repo,
    resolve_target,
)


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

    def test_supersedes_on_the_new_file_points_backward(self):
        records = [
            {"path": OLD, "text": text_with("Accepted.")},
            {"path": NEW, "text": text_with("Supersedes [ADR 0001](0001-use-postgres.md).")},
        ]
        found, _rejected, unresolved = pairs_in_repo(records)
        self.assertEqual(unresolved, 0)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["old_adr"], OLD)
        self.assertEqual(found[0]["new_adr"], NEW)

    def test_both_directions_collapse_to_the_superseded_by_order(self):
        records = [
            {"path": OLD, "text": text_with("Superseded by [ADR 4](0004-use-mysql.md).")},
            {"path": NEW, "text": text_with("Supersedes [ADR 0001](0001-use-postgres.md).")},
        ]
        found, _rejected, _unresolved = pairs_in_repo(records)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["old_adr"], OLD)
        self.assertEqual(found[0]["new_adr"], NEW)

    def test_subject_of_supersedes_is_the_new_adr(self):
        current = "docs/decisions/013-rewrite-context-on-device.md"
        named = "docs/decisions/024-shared-polishing-pipeline.md"
        other = "docs/decisions/012-context-scene-selection.md"
        text = (
            "# On device\n\n## Status\n\n"
            "Accepted. [ADR 024](024-shared-polishing-pipeline.md) supersedes the on-device-only restriction.\n"
            "See [ADR 012](012-context-scene-selection.md) for scenes.\n"
        )
        records = [
            {"path": current, "text": text},
            {"path": named, "text": "# Shared polishing\n\n## Status\n\nAccepted\n"},
            {"path": other, "text": "# Scenes\n\n## Status\n\nAccepted\n"},
        ]
        found, rejected, _unresolved = pairs_in_repo(records)
        self.assertEqual(rejected, 1)
        self.assertEqual([(row["old_adr"], row["new_adr"]) for row in found], [(current, named)])

    def test_plain_link_and_amended_by_are_not_pairs(self):
        text = text_with(
            "Accepted. See [ADR 4](0004-use-mysql.md). Amends [ADR 3](0003-cache.md).",
        )
        records = [
            {"path": OLD, "text": text},
            {"path": NEW, "text": "# Use MySQL\n\n## Status\n\nAccepted\n"},
            {"path": "docs/adr/0003-cache.md", "text": "# Cache\n\n## Status\n\nAccepted\n"},
        ]
        found, rejected, unresolved = pairs_in_repo(records)
        self.assertEqual(found, [])
        self.assertGreaterEqual(rejected, 1)
        self.assertEqual(unresolved, 0)

    def test_partial_supersede_is_kept_and_marked(self):
        records = [
            {"path": NEW, "text": text_with("Partially supersedes [ADR 0001](0001-use-postgres.md).")},
            {"path": OLD, "text": "# Use Postgres\n\n## Status\n\nAccepted\n"},
        ]
        found, _rejected, _unresolved = pairs_in_repo(records)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["old_adr"], OLD)
        self.assertEqual(found[0]["partial"], "yes")

    def test_supersedes_nothing_is_dropped(self):
        records = [
            {"path": NEW, "text": text_with("Supersedes nothing.")},
            {"path": OLD, "text": "# Use Postgres\n\n## Status\n\nAccepted\n"},
        ]
        found, _rejected, unresolved = pairs_in_repo(records)
        self.assertEqual(found, [])
        self.assertEqual(unresolved, 0)

    def test_copied_and_template_files_are_detectable(self):
        self.assertTrue(is_foreign_copy("spider2-dbt/examples/app/dbt_packages/dbt_utils/0001.md", "# x", "xlang-ai/Spider2"))
        self.assertTrue(is_template_file("docs/adr/template.md", "# Template"))
        self.assertTrue(is_template_file("docs/adr/0001.md", "This is a template for writing architecture decisions."))
        self.assertFalse(is_template_file(OLD, text_with("Accepted.")))

    def test_general_folder_needs_a_number_or_a_status(self):
        self.assertTrue(is_general_folder_path("docs/architecture/overview.md"))
        self.assertFalse(is_general_folder_path("docs/architecture/decisions/0001-use-postgres.md"))
        self.assertFalse(is_general_folder_path("docs/adr/0001-use-postgres.md"))
        self.assertTrue(filename_has_number("docs/architecture/0001-keep.md"))
        self.assertFalse(filename_has_number("docs/architecture/overview.md"))
        self.assertTrue(has_status_section("# Title\n\n## Status\n\nAccepted\n"))
        self.assertFalse(has_status_section("# Title\n\nSome notes.\n"))

    def test_title_match_beats_a_dependency_bump(self):
        commits = [
            {"sha": "bump111", "subject": "Bump faraday from 1.0 to 2.0", "files": ["M\tGemfile.lock", "M\tGemfile"]},
            {
                "sha": "d3384f5611",
                "subject": "Use one Android fused Glass renderer",
                "files": ["M\tandroid/src/GlassRenderer.kt"],
            },
        ]
        best = choose_best_commit(commits, "Use one Android fused Glass renderer", "", "", "3")
        self.assertIsNotNone(best)
        self.assertEqual(best["commit"]["sha"], "d3384f5611")
        self.assertEqual(best["confidence"], "high_topic")

    def test_asyncio_title_matches_async_xml_rpc(self):
        commits = [
            {"sha": "57d79e74d2", "subject": "Add asyncio xml rpc server", "files": ["A\tsrc/xmlrpc.py"]},
            {"sha": "c6074970aa", "subject": "Update the changelog", "files": ["M\tCHANGELOG.md"]},
        ]
        best = choose_best_commit(commits, "Async XML-RPC server POC", "# Thread based XML-RPC server", "", "12")
        self.assertEqual(best["commit"]["sha"], "57d79e74d2")
        self.assertIn(best["confidence"], {"high_topic", "high_cooccur"})

    def test_dependency_bump_does_not_win_on_json_schema_keywords(self):
        commits = [
            {"sha": "2c783677d7", "subject": "Bump the schema gem", "files": ["M\tGemfile.lock"]},
            {
                "sha": "realdrop",
                "subject": "Drop JSON schema for document configuration",
                "files": ["M\tapp/models/edition.rb", "D\tapp/schemas/document.json"],
            },
        ]
        best = choose_best_commit(
            commits,
            "Drop JSON schema for document configuration",
            "# Use JSON schema for flexible page schemas",
            "",
            "8",
        )
        self.assertEqual(best["commit"]["sha"], "realdrop")
        self.assertNotEqual(best["commit"]["sha"], "2c783677d7")


if __name__ == "__main__":
    unittest.main()
