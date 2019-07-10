import pytest
from bookworm.document_formats.base import TOCItem


tree = TOCItem(
    title="Root",
    children=[
        TOCItem(title="a", children=[]),
        TOCItem(title="b", children=[]),
        TOCItem(
            title="c",
            children=[
                TOCItem(title="c1", children=[]),
                TOCItem(title="c2", children=[]),
            ],
        ),
        TOCItem(
            title="d",
            children=[
                TOCItem(
                    title="d1",
                    children=[
                        TOCItem(
                            title="d1.1",
                            children=[TOCItem(title="d1.1.1", children=[])],
                        ),
                        TOCItem(title="d1.2", children=[]),
                        TOCItem(
                            title="d1.3",
                            children=[TOCItem(title="d1.3.1", children=[])],
                        ),
                        TOCItem(title="d1.4", children=[]),
                    ],
                )
            ],
        ),
        TOCItem(title="e", children=[]),
    ],
)


def test_simple_traversal():
    assert len(tree) == 5
    assert tree[0].simple_next is tree[1]
    assert tree[0].simple_prev is tree
    assert tree[1].simple_next is tree[2]
    assert tree[1].simple_prev is tree[0]
    assert tree[2].simple_next is tree[3]
    assert tree[2][0].simple_next is tree[2][1]
    assert tree[2][0].simple_prev is tree[2]
    assert tree[2][1].simple_next is tree[3]
    assert tree[3][0][0].simple_prev is tree[3][0]
    assert tree[3][0][0].simple_next is tree[3][0][1]
    assert tree[3][0][3].simple_next is tree[4]
