#!/usr/bin/env python3
"""Tests for the PR feed/scraper validation script.

The DB-first model registers a scraper through a pending_feeds.txt entry
whose command begins "python scrapers/" (or "python scripts/") and whose
output is cities/<city>/<name>.ics — the feeds-table insert-time trigger
contract in supabase/ddl/16_feeds.sql. The nightly runner executes active
rows from the DB, so the workflow carries no per-scraper lines.

These tests pin that contract: a new-scraper PR with only a pending entry
validates clean (no workflow edit), contract violations are reported, and
ICS-URL entries stay self-contained.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import validate_pr_feeds as vpf

VALID_ENTRY = (
    "# Visit Bloomington\n"
    '# cmd: python scrapers/visit_bloomington.py --name "Visit Bloomington" '
    "--output cities/bloomington/visit_bloomington.ics\n"
    "cities/bloomington/visit_bloomington.ics\n"
)


def _setup(tmp_path, monkeypatch, pending: str, *, scraper_files=(), feeds=None):
    """Point the validator at a tmp repo and return the changed-file entries."""
    monkeypatch.setattr(vpf, "ROOT", tmp_path)
    city = tmp_path / "cities" / "bloomington"
    city.mkdir(parents=True, exist_ok=True)
    (city / "pending_feeds.txt").write_text(pending)
    if feeds is not None:
        (city / "feeds.txt").write_text(feeds)
    for name in scraper_files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# stub\n")


class TestDbFirstScraperEntry:
    def test_new_scraper_pending_entry_validates_clean_without_workflow(
        self, tmp_path, monkeypatch
    ):
        _setup(
            tmp_path,
            monkeypatch,
            VALID_ENTRY,
            scraper_files=["scrapers/visit_bloomington.py"],
        )
        changed = [
            ("M", "cities/bloomington/pending_feeds.txt"),
            ("A", "scrapers/visit_bloomington.py"),
        ]
        monkeypatch.setattr(vpf, "get_changed_file_statuses", lambda base_ref: changed)

        assert vpf.validate("origin/main") == []

    def test_command_violating_trigger_contract_is_flagged(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# Visit Bloomington\n"
            "# cmd: python other/visit_bloomington.py --output "
            "cities/bloomington/visit_bloomington.ics\n"
            "cities/bloomington/visit_bloomington.ics\n",
            scraper_files=["other/visit_bloomington.py"],
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "DB trigger contract" in errors[0]
        assert "python scrapers/" in errors[0]

    def test_output_violating_trigger_contract_is_flagged(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# Visit Bloomington\n"
            "# cmd: python scrapers/visit_bloomington.py --output "
            "cities/Bloomington/visit_bloomington.ics\n"
            "cities/Bloomington/visit_bloomington.ics\n",
            scraper_files=["scrapers/visit_bloomington.py"],
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "DB trigger contract" in errors[0]
        assert "cities/<city>/<file>.ics" in errors[0]

    def test_missing_command_is_flagged(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# Visit Bloomington\ncities/bloomington/visit_bloomington.ics\n",
            scraper_files=["scrapers/visit_bloomington.py"],
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "python scrapers/" in errors[0]

    def test_missing_scraper_file_is_flagged(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch, VALID_ENTRY)
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "scrapers/visit_bloomington.py" in errors[0]
        assert "not a file" in errors[0]

    def test_command_without_py_suffix_is_still_checked_for_file(self, tmp_path, monkeypatch):
        # The DB trigger only checks the "python scrapers/" prefix, so a
        # command can name a repo script without a .py suffix. The referenced
        # file must still be validated, or the nightly runner fails first.
        _setup(
            tmp_path,
            monkeypatch,
            "# Visit Bloomington\n"
            "# cmd: python scrapers/missing --output "
            "cities/bloomington/visit_bloomington.ics\n"
            "cities/bloomington/visit_bloomington.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "scrapers/missing" in errors[0]
        assert "not a file" in errors[0]

    def test_command_naming_a_directory_is_flagged(self, tmp_path, monkeypatch):
        # "Not a file" includes a repo directory: a command whose token names
        # a directory must be rejected, or the nightly runner fails first.
        _setup(
            tmp_path,
            monkeypatch,
            "# Visit Bloomington\n"
            "# cmd: python scrapers/lib --output "
            "cities/bloomington/visit_bloomington.ics\n"
            "cities/bloomington/visit_bloomington.ics\n",
        )
        (tmp_path / "scrapers" / "lib").mkdir(parents=True)
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "scrapers/lib" in errors[0]
        assert "not a file" in errors[0]


class TestIcsUrlEntry:
    def test_ics_url_entry_is_self_contained(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# Some Org\nhttps://example.com/events.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        assert vpf.validate("origin/main") == []

    def test_my_picks_capability_url_is_rejected(self, tmp_path, monkeypatch):
        """A curator's feed token is the only credential for their picks and
        feeds.txt is public, so the URL can never be a pending entry
        (GHSA-3pg8-w4j4-6wv8)."""
        _setup(
            tmp_path,
            monkeypatch,
            "# The Night\nhttps://ref.supabase.co/functions/v1/my-picks?token=0d6f3c1a\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")

        assert len(errors) == 1
        assert "my-picks" in errors[0]

    def test_my_picks_capability_url_in_metadata_is_rejected(self, tmp_path, monkeypatch):
        # The name comment is inserted into feeds as the feed's name and
        # exported back to feeds.txt, so a token there is committed too.
        _setup(
            tmp_path,
            monkeypatch,
            "# The Night | https://ref.supabase.co/functions/v1/my-picks?token=0d6f3c1a\n"
            "https://example.com/events.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/pending_feeds.txt")],
        )

        errors = vpf.validate("origin/main")

        assert len(errors) == 1
        assert "pending_feeds.txt:1" in errors[0]


class TestFeedsTxtEntry:
    """feeds.txt is generated, but a hand-edited line is how the two Bloomington
    tokens leaked, so a changed feeds.txt is validated too."""

    def test_capability_url_in_feeds_txt_is_rejected(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# empty\n",
            feeds="# The Night\nhttps://ref.supabase.co/functions/v1/my-picks?token=0d6f3c1a\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/feeds.txt")],
        )

        errors = vpf.validate("origin/main")

        assert len(errors) == 1
        assert "feeds.txt:2" in errors[0]

    def test_capability_url_in_feeds_txt_metadata_is_rejected(self, tmp_path, monkeypatch):
        # A "# Name | fallback URL" comment is copied into X-SOURCE-URL by
        # download_feeds.py, so the token is committed and published even above
        # an ordinary feed URL.
        _setup(
            tmp_path,
            monkeypatch,
            "# empty\n",
            feeds="# Plain | https://ref.supabase.co/functions/v1/my-picks?token=0d6f3c1a\n"
            "https://example.com/events.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/feeds.txt")],
        )

        errors = vpf.validate("origin/main")

        assert len(errors) == 1
        assert "feeds.txt:1" in errors[0]

    def test_clean_feeds_txt_passes(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# empty\n",
            feeds="# Plain\nhttps://example.com/events.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("M", "cities/bloomington/feeds.txt")],
        )

        assert vpf.validate("origin/main") == []


class TestNewScraperRegistration:
    def test_new_scraper_without_pending_entry_is_flagged(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch, "# empty\n", scraper_files=["scrapers/orphan.py"])
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("A", "scrapers/orphan.py")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "scrapers/orphan.py" in errors[0]
        assert "pending_feeds.txt" in errors[0]

    def test_new_scraper_registered_in_feeds_txt_passes(self, tmp_path, monkeypatch):
        _setup(
            tmp_path,
            monkeypatch,
            "# empty\n",
            scraper_files=["scrapers/orphan.py"],
            feeds="# Orphan\n# cmd: python scrapers/orphan.py\ncities/bloomington/orphan.ics\n",
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("A", "scrapers/orphan.py")],
        )

        assert vpf.validate("origin/main") == []

    def test_new_scraper_matching_template_comment_is_still_flagged(self, tmp_path, monkeypatch):
        # The pending_feeds.txt template mentions "python scrapers/example.py"
        # inside a comment. A real scrapers/example.py is not thereby
        # registered; the check must match the exact script path of a
        # '# cmd:' entry, not a substring of all feed content.
        _setup(
            tmp_path,
            monkeypatch,
            "# Display Name\n"
            '#   # cmd: python scrapers/example.py --name "Source Name" '
            "--output cities/bloomington/example.ics\n"
            "#   cities/bloomington/example.ics\n",
            scraper_files=["scrapers/example.py"],
        )
        monkeypatch.setattr(
            vpf,
            "get_changed_file_statuses",
            lambda base_ref: [("A", "scrapers/example.py")],
        )

        errors = vpf.validate("origin/main")
        assert len(errors) == 1
        assert "scrapers/example.py" in errors[0]
        assert "pending_feeds.txt" in errors[0]


class TestRelevance:
    def test_workflow_only_change_is_not_relevant(self):
        assert vpf.is_relevant([".github/workflows/generate-calendar.yml"]) is False

    def test_scraper_change_is_relevant(self):
        assert vpf.is_relevant(["scrapers/foo.py"]) is True
