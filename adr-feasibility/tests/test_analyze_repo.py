import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from adr_pilot.analyze import analyze_clone


def _git(repo, *args, env):
    subprocess.run(["git", *args], cwd=repo, check=True, env=env, capture_output=True)


class AnalyzeRepoTests(unittest.TestCase):
    def test_counts_only_adrs_before_the_signal_and_labels_endings(self):
        root = tempfile.mkdtemp(prefix="adr-pilot-")
        self.addCleanup(shutil.rmtree, root, True)
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Ada",
            "GIT_AUTHOR_EMAIL": "ada@example.com",
            "GIT_COMMITTER_NAME": "Ada",
            "GIT_COMMITTER_EMAIL": "ada@example.com",
        }
        _git(root, "init", "-b", "main", env=env)
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)

        def commit(days, message, author_date=None):
            when = (start + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            local = env.copy()
            local["GIT_AUTHOR_DATE"] = author_date or when
            local["GIT_COMMITTER_DATE"] = author_date or when
            _git(root, "add", "-A", env=local)
            _git(root, "commit", "-m", message, env=local)

        os.makedirs(os.path.join(root, "docs/adr"), exist_ok=True)
        os.makedirs(os.path.join(root, "src"), exist_ok=True)
        records = {
            "0001-use-postgres.md": "# Use Postgres\n\n## Status\n\nAccepted\n\nUse `src/db.py`.\n",
            "0002-use-redis.md": "# Use Redis\n\n## Status\n\nProposed\n",
            "0003-use-rest.md": "# Use REST\n\n## Status\n\nAccepted\n",
            "0004-use-grpc.md": "# Use gRPC\n\n## Status\n\nAccepted\n",
            "0005-log-json.md": "# Log JSON\n\n## Status\n\nAccepted\n",
        }
        for name, body in records.items():
            with open(os.path.join(root, "docs/adr", name), "w", encoding="utf-8") as handle:
                handle.write(body)
        with open(os.path.join(root, "src/db.py"), "w", encoding="utf-8") as handle:
            handle.write("print('db')\n")
        commit(0, "record five decisions and the database module")

        with open(os.path.join(root, "docs/adr/0002-use-redis.md"), "w", encoding="utf-8") as handle:
            handle.write("# Use Redis\n\n## Status\n\nRejected\n\nWe will not add Redis.\n")
        commit(30, "reject the Redis proposal")

        with open(os.path.join(root, "docs/adr/0003-use-rest.md"), "w", encoding="utf-8") as handle:
            handle.write(
                "# Use REST\n\n## Status\n\nSuperseded by [ADR-0004](0004-use-grpc.md)\n"
            )
        commit(60, "replace REST with gRPC")

        with open(os.path.join(root, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("# Claude\nUse the project conventions.\n")
        commit(400, "add Claude instructions")

        with open(os.path.join(root, "src/db.py"), "a", encoding="utf-8") as handle:
            handle.write("# tuned\n")
        commit(401, "tune the pool\n\nCo-authored-by: Copilot <copilot@github.com>\n")

        with open(os.path.join(root, "docs/adr/0006-after-ai.md"), "w", encoding="utf-8") as handle:
            handle.write("# After\n\n## Status\n\nAccepted\n")
        commit(420, "record a decision after adopting Claude")

        result = analyze_clone(root, repo_name="example/decisions")
        self.assertEqual(result["group"], "ai-eligible")
        self.assertEqual(result["adr_count_before_signal"], 5)
        self.assertEqual(result["adr_count"], 6)
        self.assertEqual(result["signal_kind"], "file:primary")
        labels = {(change["path"].rsplit("/", 1)[-1], change["script_label"]) for change in result["status_changes"]}
        self.assertIn(("0002-use-redis.md", "rejected-before-use"), labels)
        self.assertIn(("0003-use-rest.md", "replaced"), labels)
        superseded = [adr for adr in result["adrs"] if adr["status"] == "superseded"]
        self.assertEqual(len(superseded), 1)
        postgres = next(adr for adr in result["adrs"] if adr["path"].endswith("0001-use-postgres.md"))
        self.assertEqual(postgres["implementation"]["reason"], "first-commit-touching-a-path-named-in-the-adr")


if __name__ == "__main__":
    unittest.main()
