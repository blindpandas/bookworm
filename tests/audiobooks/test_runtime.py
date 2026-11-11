"""Crash-sensitive engine initialization in a child process, with diagnostics."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("BOOKWORM_TEST_AUDIO") != "1", reason="Native audio tests are opt-in"
)


def test_engine_repeated_initialization_with_native_fault_reporting():
    # A native abort must fail this test with its stderr, rather than prevent
    # pytest from reporting all other test results. Keep faulthandler enabled.
    source = r"""
import faulthandler
import locale
import os
from pathlib import Path
import shutil
import sys
import tempfile
faulthandler.enable()
from bookworm.audiobooks.backend import create_mpv
from bookworm import app
from bookworm.audiobooks import backend
shadow = tempfile.TemporaryDirectory()
if sys.platform == "win32":
    expected = Path(backend.__file__).resolve().parents[2] / "scripts" / "dlls" / "mpv" / app.arch / "libmpv-2.dll"
    shutil.copyfile(expected, Path(shadow.name) / "mpv-2.dll")
    os.environ["PATH"] = shadow.name + os.pathsep + os.environ.get("PATH", "")
for index in range(12):
    if sys.platform == "win32":
        locale.setlocale(locale.LC_NUMERIC, "Hungarian_Hungary.1250")
    player = create_mpv(ao="null", pause=True, idle=True)
    try:
        assert locale.setlocale(locale.LC_NUMERIC) == "C"
        assert player.mpv_version
        player.speed = 0.75
        assert abs(player.speed - 0.75) < 0.001
        print("Engine initialized:", index + 1, player.mpv_version, flush=True)
    finally:
        player.terminate()
print("All audio clients closed", flush=True)
# Windows keeps the imported DLL mapped until exit; the shadow copy must never
# be loaded, so it can be removed now, not just after the process exits.
shadow.cleanup()
"""
    result = subprocess.run(
        [sys.executable, "-u", "-c", source],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, (
        f"Native engine exit code: {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    assert "All audio clients closed" in result.stdout
