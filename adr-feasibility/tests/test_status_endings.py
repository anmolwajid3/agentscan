import unittest

from adr_pilot.endings import classify_ending
from adr_pilot.eligibility import check1_passed, classify_project
from adr_pilot.kappa import cohens_kappa, weighted_kappa
from adr_pilot.lead import extract_paths, pick_implementation
from adr_pilot.signals import ai_coauthor_hits, classify_signal_path, is_agent_author, mention_kind
from adr_pilot.status import find_replacement, parse_status


class StatusTests(unittest.TestCase):
    def test_status_heading_after_a_long_decision(self):
        preamble = "\n".join(f"Paragraph {i} about the design." for i in range(150))
        text = f"# ADR 1: Logging\n\n## Context\n\n{preamble}\n\n## Status\n\nAccepted\n\n## Consequences\n"
        self.assertEqual(parse_status(text).state, "accepted")

    def test_not_implemented_stays_proposed(self):
        text = "# Title\n\n## Status\n\nProposed, not implemented yet. Work had been started.\n"
        self.assertEqual(parse_status(text).state, "proposed")

    def test_accepted_even_if_it_also_says_not_implemented(self):
        text = "# Title\n\n## Status\n\nAccepted (lazy consensus). Not yet implemented.\n"
        self.assertEqual(parse_status(text).state, "accepted")

    def test_nygard_accepted(self):
        text = "# Use Postgres\n\n## Status\n\nAccepted\n\n## Context\n\nWe need a database.\n"
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "accepted")

    def test_madr_superseded_link(self):
        text = (
            "# Use REST\n\n## Status\n\nsuperseded by [ADR-0004](0004-use-grpc.md)\n\n"
            "## Context\n\nThe old API.\n"
        )
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "superseded")
        self.assertIn("0004-use-grpc.md", parsed.replacement or "")

    def test_template_legend_is_not_a_status(self):
        text = (
            "# Title\n\n## Status\n\n"
            "<!--- What is the status, such as proposed, accepted, rejected, deprecated, superseded -->\n"
        )
        self.assertEqual(parse_status(text).state, "unknown")

    def test_unchecked_menu_is_not_superseded(self):
        text = (
            "# Title\n\nStatus: - [x] active - [ ] rejected - [ ] deprecated - [ ] superseded\n"
        )
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "accepted")

    def test_checked_superseded(self):
        text = "# Title\n\n## Status\n\n- [ ] proposed\n- [ ] accepted\n- [x] superseded by ADR-0009\n"
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "superseded")
        self.assertIn("0009", parsed.replacement or "")

    def test_front_matter(self):
        text = "---\nstatus: accepted\ndate: 2024-01-01\n---\n# Title\n"
        self.assertEqual(parse_status(text).state, "accepted")

    def test_accepted_then_superseded_phrase(self):
        text = "# Title\n\n## Status\n\nAccepted. Superseded by [ADR043](ADR043-k8s.md)\n"
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "superseded")
        self.assertIn("ADR043", parsed.replacement or "")

    def test_supersedes_means_this_record_is_the_replacement(self):
        text = "# New way\n\n## Status\n\nAccepted. Supersedes [4. Old way](0004-old.md)\n"
        self.assertEqual(parse_status(text).state, "accepted")


class EndingTests(unittest.TestCase):
    def test_replacement_pointer(self):
        ending = classify_ending(
            "accepted",
            "superseded",
            new_raw="superseded by ADR-0004",
            replacement="ADR-0004 (0004.md)",
        )
        self.assertEqual(ending.label, "replaced")

    def test_rejected_proposal(self):
        ending = classify_ending("proposed", "rejected", new_raw="rejected")
        self.assertEqual(ending.label, "rejected-before-use")

    def test_deprecated(self):
        ending = classify_ending("accepted", "deprecated", new_raw="deprecated")
        self.assertEqual(ending.label, "no-longer-needed")

    def test_rename(self):
        ending = classify_ending("accepted", "accepted", renamed=True, message="Move ADRs to docs/adr")
        self.assertEqual(ending.label, "cleanup-or-rename")

    def test_superseded_means_obsolete_when_it_says_so(self):
        ending = classify_ending(
            "accepted",
            "superseded",
            new_raw="superseded, no longer needed",
            message="Remove the feature",
        )
        self.assertEqual(ending.label, "no-longer-needed")

    def test_deprecated_by_an_adr_number_is_replaced(self):
        text = "## Status\n\nDeprecated by [60. lock-pip-requirements](0060-lock-pip-requirements.md)\n"
        parsed = parse_status(text)
        self.assertEqual(parsed.state, "deprecated")
        self.assertIn("0060", parsed.replacement or "")
        ending = classify_ending("accepted", "deprecated", new_raw=parsed.raw, replacement=parsed.replacement)
        self.assertEqual(ending.label, "replaced")

    def test_deprecated_as_of_adr_is_replaced(self):
        raw = "Deprecated as of [ADR-5](ADR-5_no-more-bootstrap.md)."
        ending = classify_ending("accepted", "deprecated", new_raw=raw)
        self.assertEqual(ending.label, "replaced")

    def test_deprecated_by_a_bare_number_is_replaced(self):
        ending = classify_ending("accepted", "deprecated", new_raw="Deprecated by 60")
        self.assertEqual(ending.label, "replaced")

    def test_rejected_see_adr_is_replaced(self):
        raw = "Rejected (see [ADR 8](0008-stream-first.md))"
        parsed = parse_status("# Title\n\n## Status\n\n" + raw + "\n")
        self.assertEqual(parsed.state, "rejected")
        ending = classify_ending("accepted", "rejected", new_raw=raw)
        self.assertEqual(ending.label, "replaced")

    def test_a_year_or_a_person_is_not_a_replacement(self):
        self.assertEqual(
            classify_ending("accepted", "deprecated", new_raw="Deprecated by 2021").label,
            "no-longer-needed",
        )
        self.assertEqual(
            classify_ending("proposed", "rejected", new_raw="Rejected by DAO").label,
            "rejected-before-use",
        )
        self.assertEqual(
            classify_ending("accepted", "deprecated", new_raw="Deprecated (no superseding ADR)").label,
            "no-longer-needed",
        )


class EligibilityTests(unittest.TestCase):
    def test_before_signal_only(self):
        result = classify_project(
            adr_dates=["2020-01-01T00:00:00Z"] * 6 + ["2025-01-01T00:00:00Z"],
            superseded_flags=[False] * 6 + [True],
            signal_date="2024-06-01T00:00:00Z",
            likely_template=False,
            clone_ok=True,
        )
        self.assertEqual(result.group, "ai-eligible")
        self.assertEqual(result.adr_count_before_signal, 6)
        self.assertEqual(result.superseded, 0)
        self.assertTrue(result.counts_toward_ai)

    def test_quiet_project_still_counts(self):
        result = classify_project(
            adr_dates=["2018-01-01T00:00:00Z"] * 5,
            superseded_flags=[True, False, False, False, False],
            signal_date=None,
            likely_template=False,
            clone_ok=True,
        )
        self.assertEqual(result.group, "non-ai-eligible")
        self.assertEqual(result.superseded, 1)

    def test_ai_native_does_not_fill_the_ai_quota(self):
        result = classify_project(
            adr_dates=["2025-02-01T00:00:00Z"] * 8,
            superseded_flags=[False] * 8,
            signal_date="2025-01-01T00:00:00Z",
            likely_template=False,
            clone_ok=True,
        )
        self.assertEqual(result.group, "ai-native")
        self.assertFalse(result.counts_toward_ai)

    def test_pass_bar(self):
        self.assertFalse(check1_passed(49, 50, 100))
        self.assertTrue(check1_passed(50, 50, 100))


class KappaTests(unittest.TestCase):
    def test_perfect_agreement(self):
        result = cohens_kappa([("a", "a"), ("b", "b"), ("a", "a")])
        self.assertEqual(result["kappa"], 1)

    def test_chance_is_zero_and_total_disagreement_is_negative(self):
        chance = cohens_kappa([("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")])
        self.assertAlmostEqual(chance["kappa"], 0.0)
        disagreement = cohens_kappa([("a", "b"), ("b", "a"), ("a", "b"), ("b", "a")])
        self.assertAlmostEqual(disagreement["kappa"], -1.0)

    def test_weighted_perfect(self):
        result = weighted_kappa([(0, 0), (1, 1), (2, 2)], categories=[0, 1, 2])
        self.assertEqual(result["kappa"], 1)


class SignalTests(unittest.TestCase):
    def test_primary_file(self):
        self.assertEqual(classify_signal_path("CLAUDE.md"), "primary")
        self.assertEqual(classify_signal_path(".github/copilot-instructions.md"), "primary")
        self.assertIsNone(classify_signal_path("vendor/pkg/CLAUDE.md"))

    def test_coauthor_ignores_a_human_named_claude(self):
        message = "Co-authored-by: Claude Martin <claude.martin@example.com>\n"
        self.assertEqual(ai_coauthor_hits(message), [])

    def test_coauthor_accepts_copilot(self):
        message = "Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>\n"
        self.assertEqual(len(ai_coauthor_hits(message)), 1)

    def test_agent_author(self):
        self.assertTrue(is_agent_author("Copilot", "copilot@github.com"))
        self.assertFalse(is_agent_author("Claude Martin", "claude.martin@example.com"))

    def test_cursor_word_alone_is_not_strict(self):
        self.assertEqual(mention_kind("fix cursor position in the table"), "literal-only")
        self.assertEqual(mention_kind("pair with GitHub Copilot on the parser"), "strict")


class LeadTests(unittest.TestCase):
    def test_picks_the_named_file_after_the_adr(self):
        commits = [
            {"sha": "a", "date": "2020-01-01T00:00:00Z", "subject": "earlier", "files": ["src/db.py"]},
            {"sha": "b", "date": "2021-02-01T00:00:00Z", "subject": "apply decision", "files": ["src/db.py"]},
        ]
        hit = pick_implementation(
            "2021-01-01T00:00:00Z",
            "docs/adr/0001-use-postgres.md",
            ["src/db.py"],
            "1",
            commits,
        )
        self.assertEqual(hit.sha, "b")

    def test_extracts_paths(self):
        paths = extract_paths("Store rows in `src/db.py` and ignore docs/adr/0001.md.")
        self.assertIn("src/db.py", paths)
        self.assertFalse(any(path.endswith("0001.md") for path in paths))


if __name__ == "__main__":
    unittest.main()
