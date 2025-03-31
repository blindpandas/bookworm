import pytest

from bookworm.otau import UpdateChannel, is_newer_version


def test_is_not_valid_identifier():
    with pytest.raises(TypeError):
        channel = UpdateChannel("test")


def test_is_valid_identifier():
    valid_identifiers = ("", "a", "b", "rc")
    for identifier in valid_identifiers:
        channel = UpdateChannel(identifier)


def test_is_major_version():
    c = UpdateChannel("")
    assert c.is_major == True


@pytest.mark.parametrize(
    "current_version,upstream_version,expected",
    [
        # Normal version comparisons
        ("2024.1", "2024.2", True),  # Minor version increment
        ("2024.1", "2025.1", True),  # Major version increment
        ("2025.1", "2024.4.2", False),  # Current version newer
        ("2024.1.0", "2024.1.1", True),  # Patch version increment
        # Pre-release versions
        ("2024.1rc1", "2024.1", True),  # Release candidate to final
        ("2024.1", "2024.1rc1", False),  # Final to release candidate
        ("2024.1a1", "2024.1b1", True),  # Alpha to beta
        ("2024.1b1", "2024.1rc1", True),  # Beta to release candidate
        # Complex versions
        ("2024.1.0.0", "2024.1.0.1", True),  # Four-part version
        ("2024.1.post1", "2024.2", True),  # Post-release version
        ("2024.1.dev1", "2024.1", True),  # Development version
        # Edge cases
        ("2024.1", "2024.1", False),  # Same version
        (
            "invalid",
            "2024.1",
            True,
        ),  # Invalid current version (fallback to string comparison)
        (
            "2024.1",
            "invalid",
            False,
        ),  # Invalid upstream version (fallback to string comparison)
    ],
)
def test_version_comparison(current_version, upstream_version, expected):
    """Test various version comparison scenarios"""
    result = is_newer_version(current_version, upstream_version)
    assert result == expected, (
        f"Version comparison failed for {current_version} vs {upstream_version}. "
        f"Expected {expected}, got {result}"
    )
