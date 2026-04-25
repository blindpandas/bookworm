import pytest

from bookworm.platforms.win32.update_paths import (
    get_bootstrap_archive_path,
    get_update_target_dir,
    resolve_bootstrap_path,
)


def test_bootstrap_archive_path_is_root_level():
    assert get_bootstrap_archive_path() == "bootstrap.exe"


def test_resolve_bootstrap_path_prefers_root_level_file(tmp_path):
    root_bootstrap = tmp_path / "bootstrap.exe"
    root_bootstrap.write_text("root")
    legacy_bootstrap = tmp_path / "_internal" / "bootstrap.exe"
    legacy_bootstrap.parent.mkdir()
    legacy_bootstrap.write_text("legacy")

    assert resolve_bootstrap_path(tmp_path) == root_bootstrap


def test_resolve_bootstrap_path_falls_back_to_legacy_internal_location(tmp_path):
    legacy_bootstrap = tmp_path / "_internal" / "bootstrap.exe"
    legacy_bootstrap.parent.mkdir()
    legacy_bootstrap.write_text("legacy")

    assert resolve_bootstrap_path(tmp_path) == legacy_bootstrap


def test_resolve_bootstrap_path_raises_clear_error_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_bootstrap_path(tmp_path)

    message = str(exc_info.value)
    assert str(tmp_path / "bootstrap.exe") in message
    assert str(tmp_path / "_internal" / "bootstrap.exe") in message


def test_get_update_target_dir_uses_current_executable_parent(tmp_path):
    executable = tmp_path / "Bookworm.exe"

    assert get_update_target_dir(executable) == tmp_path.resolve()
