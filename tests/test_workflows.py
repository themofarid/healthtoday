import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class WorkflowTests(unittest.TestCase):
    def test_pages_workflow_deploys_site_folder(self):
        text = read(".github/workflows/pages.yml")
        for needle in ("upload-pages-artifact", "deploy-pages", "path: site", "pages: write"):
            self.assertIn(needle, text)

    def test_watchdog_workflow_is_daily_and_runs_command(self):
        text = read(".github/workflows/watchdog.yml")
        for needle in ("cron:", "python -m tools watchdog", "issues: write", "gh issue create",
                       "gh workflow run pages.yml", "actions: write"):
            self.assertIn(needle, text)

    def test_article_prompt_states_draft_format_and_forbidden_claims(self):
        text = read("docs/article-prompt.md")
        for needle in ("# ", "### ", "## Benefit 1:", "## Benefit 2:", "## Benefit 3:",
                       "## The one con:", "## Conclusion", "cure", "guaranteed", "doctors hate",
                       "miracle", "no side effects", "before and after", "reverse diabetes",
                       "get off medication"):
            self.assertIn(needle, text)

    def test_readme_mentions_public_repo_and_pages_setting(self):
        text = read("README.md")
        self.assertIn("public", text.lower())
        self.assertIn("GitHub Actions", text)
        self.assertIn("python -m tools publish", text)

    def test_generated_files_are_not_committed(self):
        self.assertIn("newly_dead.txt", read(".gitignore"))


if __name__ == "__main__":
    unittest.main()
