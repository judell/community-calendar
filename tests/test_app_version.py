"""The version is a contract between a publication and returning browsers."""

import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "app_version", Path(__file__).parents[1] / "scripts/app_version.py")
versioning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versioning)


@pytest.fixture
def site(tmp_path):
    for name in versioning.REQUIRED_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    for directory in versioning.ASSET_DIRS:
        path = tmp_path / directory / "fixture.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}')
    return tmp_path


def test_stable_across_output_and_data_changes(site):
    before = versioning.write_version(site)
    (site / "events.json").write_text('[{"title":"new data"}]')
    (site / "report.json").write_text('{}')
    (site / "xmlui/config.local.js").write_text('// local-only override')
    assert versioning.write_version(site) == before


@pytest.mark.parametrize("name", [
    "xmlui/helpers.js", "xmlui/Globals.xs", "xmlui/config.json",
    "xmlui/themes/fixture.json", "xmlui/xmlui/xmlui-standalone.umd.js",
    "categories.json",
])
def test_runtime_changes_invalidate(site, name):
    before = versioning.app_version(site)
    with (site / name).open('a') as stream:
        stream.write('\nchanged')
    assert versioning.app_version(site) != before


def test_renames_additions_and_removals_invalidate(site):
    before = versioning.app_version(site)
    path = site / "xmlui/components/fixture.json"
    path.rename(path.with_name("renamed.json"))
    renamed = versioning.app_version(site)
    assert renamed != before
    extra = site / "xmlui/components/extra.xmlui.xs"
    extra.write_text('var x = 1;')
    assert versioning.app_version(site) != renamed
    extra.unlink()
    assert versioning.app_version(site) == renamed


def test_file_boundaries_are_significant(site):
    a, b = site / "xmlui/helpers.js", site / "xmlui/shell.js"
    a.write_text('a')
    b.write_text('bc')
    before = versioning.app_version(site)
    a.write_text('ab')
    b.write_text('c')
    assert versioning.app_version(site) != before


def test_missing_required_file_does_not_publish_partial_version(site):
    before = versioning.write_version(site)
    (site / "xmlui/helpers.js").unlink()
    with pytest.raises(ValueError, match="Missing"):
        versioning.write_version(site)
    assert (site / "xmlui/version.txt").read_text().strip() == before
