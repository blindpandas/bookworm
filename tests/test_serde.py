# coding: utf-8

import msgpack
import pytest
import ujson

from bookworm.document import create_document
from bookworm.document.serde import dump_toc_tree, load_toc_tree
from bookworm.document.uri import DocumentUri


def test_serde_toc_tree(asset):
    uri = DocumentUri.from_filename(asset("epub30-spec.epub"))
    epub_document = create_document(uri)

    constructed = load_toc_tree(dump_toc_tree(epub_document.toc_tree))
    assert len(epub_document.toc_tree) == len(constructed)

    compare_pairs = zip(constructed.iter_children(), epub_document.toc_tree.iter_children())
    assert all(t.title == s.title for (t, s) in compare_pairs)



@pytest.mark.parametrize('library', [ujson, msgpack,])
def test_wire_serde(asset, library):
    uri = DocumentUri.from_filename(asset("epub30-spec.epub"))
    epub_document = create_document(uri)

    serialized = library.dumps(dump_toc_tree(epub_document.toc_tree))
    deserialized = library.loads(serialized)

    constructed = load_toc_tree(deserialized)
    compare_pairs = zip(constructed.iter_children(), epub_document.toc_tree.iter_children())
    assert all(t.title == s.title for (t, s) in compare_pairs)
