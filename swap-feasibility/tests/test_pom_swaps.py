import unittest
from datetime import datetime, timezone

from swap_pilot.detect import assign_group, same_commit_swaps
from swap_pilot.pom import parse_pom
from swap_pilot.summarize import months_between


POM = """<?xml version="1.0"?>
<project>
  <groupId>org.example</groupId>
  <artifactId>demo</artifactId>
  <properties><slf4j.version>2.0.9</slf4j.version></properties>
  <dependencies>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>${slf4j.version}</version>
    </dependency>
    <dependency>
      <groupId>${missing}</groupId>
      <artifactId>nope</artifactId>
    </dependency>
  </dependencies>
  <build><plugins><plugin><dependencies>
    <dependency><groupId>junit</groupId><artifactId>junit</artifactId></dependency>
  </dependencies></plugin></plugins></build>
</project>
"""


class PomTests(unittest.TestCase):
    def test_property_version_is_kept_and_unresolved_is_unparsed(self):
        deps, bad = parse_pom(POM)
        self.assertIn("org.slf4j:slf4j-api", deps)
        self.assertNotIn("junit:junit", deps)
        self.assertTrue(any("unresolved" in note for note in bad))

    def test_project_group_and_parent_property_resolve(self):
        parent = """<project>
          <groupId>com.example</groupId>
          <artifactId>parent</artifactId>
          <version>1</version>
          <properties><lib.version>1</lib.version></properties>
        </project>"""
        child = """<project>
          <parent>
            <groupId>com.example</groupId>
            <artifactId>parent</artifactId>
            <version>1</version>
          </parent>
          <artifactId>child</artifactId>
          <dependencies>
            <dependency>
              <groupId>${project.groupId}</groupId>
              <artifactId>okhttp</artifactId>
            </dependency>
            <dependency>
              <groupId>${project.parent.groupId}</groupId>
              <artifactId>mockwebserver</artifactId>
            </dependency>
            <dependency>
              <groupId>org.example</groupId>
              <artifactId>${missing.lib}</artifactId>
            </dependency>
          </dependencies>
        </project>"""
        deps, bad = parse_pom(child, [parent])
        self.assertIn("com.example:okhttp", deps)
        self.assertIn("com.example:mockwebserver", deps)
        self.assertTrue(any("unresolved" in note for note in bad))

    def test_broken_xml_is_unparsed(self):
        deps, bad = parse_pom("<project>")
        self.assertEqual(deps, set())
        self.assertEqual(len(bad), 1)

    def test_same_commit_swap_uses_the_rule_list(self):
        rules = {("log4j:log4j", "org.slf4j:slf4j-api"): {"rule_id": "7", "rule_type": "undecided"}}
        events = [
            {
                "sha": "abc",
                "date": "2026-02-01T00:00:00+00:00",
                "author": "Ada",
                "email": "ada@example.com",
                "message": "replace log4j",
                "removed": {"log4j:log4j"},
                "added": {"org.slf4j:slf4j-api"},
                "bot": False,
            }
        ]
        rows = same_commit_swaps("example/demo", events, rules)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rule_id"], "7")
        self.assertEqual(rows[0]["detection"], "same commit")

    def test_missing_adoption_date_stays_na(self):
        row = {"date": "2026-02-01T00:00:00+00:00"}
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        cutoff = datetime(2026, 11, 8, tzinfo=timezone.utc)
        self.assertEqual(assign_group(row, "yes", "", start, cutoff), "NA")

    def test_negative_window_is_zero_and_missing_stays_missing(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        earlier = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(months_between(start, earlier, 30.4375), 0.0)
        self.assertIsNone(months_between(None, start, 30.4375))


if __name__ == "__main__":
    unittest.main()
