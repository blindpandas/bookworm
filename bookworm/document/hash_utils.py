from bookworm.structured_text import CURRENT_CONTENT_HASH_VERSION


def get_persistent_content_hash(current_hash: str | None, legacy_hash: str | None):
    """Return the hash/version pair that should be persisted for future matches."""
    if current_hash is not None:
        return current_hash, CURRENT_CONTENT_HASH_VERSION
    if legacy_hash is not None:
        # Keep legacy hashes marked as legacy so path changes can still match them.
        return legacy_hash, None
    return None, CURRENT_CONTENT_HASH_VERSION
