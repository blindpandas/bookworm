from pathlib import Path


BOOTSTRAP_ARCHIVE_PATH = Path("bootstrap.exe")
LEGACY_BOOTSTRAP_ARCHIVE_PATH = Path("_internal", "bootstrap.exe")


class BootstrapPathNotFoundError(FileNotFoundError):
    def __init__(self, searched_paths):
        joined_paths = ", ".join(str(path) for path in searched_paths)
        super().__init__(
            f"bootstrap.exe not found in extracted update bundle: {joined_paths}"
        )


def get_bootstrap_archive_path() -> str:
    return BOOTSTRAP_ARCHIVE_PATH.as_posix()


def resolve_bootstrap_path(extraction_dir) -> Path:
    extraction_dir = Path(extraction_dir)
    candidates = (
        extraction_dir / BOOTSTRAP_ARCHIVE_PATH,
        extraction_dir / LEGACY_BOOTSTRAP_ARCHIVE_PATH,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise BootstrapPathNotFoundError(candidates)


def get_update_target_dir(current_executable) -> Path:
    return Path(current_executable).resolve().parent
