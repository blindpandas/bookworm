from types import SimpleNamespace

import pytest

from bookworm import app
from bookworm.document import LinkTarget
from bookworm.document.formats import html as html_format
from bookworm.document.formats.html import WebHtmlDocument
from bookworm.document.uri import DocumentUri
from bookworm.structured_text import SemanticElementType


def make_wikipedia_document(html):
    document = WebHtmlDocument(
        DocumentUri(
            format="webpage",
            path="https://en.wikipedia.org/wiki/Sample",
            openner_args={},
        )
    )
    document.html_string = html
    document.parse_html()
    return document


def test_wikipedia_article_html_preserves_links_anchors_and_tables():
    html = WebHtmlDocument._build_wikipedia_article_html(
        "Sample",
        """
        <p>
            <a href="/wiki/Linked_article">article link</a>
            <a href="#Details">details link</a>
            <a href="/wiki/Sample#%E6%AD%B7%E5%8F%B2">history link</a>
        </p>
        <h2 id="Details">Details</h2>
        <h2 id="&#x6b77;&#x53f2;">&#x6b77;&#x53f2;</h2>
        <table>
            <tr><th>Language</th></tr>
            <tr><td>Python</td></tr>
            <tr><td><a href="/wiki/Table_link">table link</a></td></tr>
        </table>
        """,
        "https://en.wikipedia.org/wiki/Sample",
    )
    document = make_wikipedia_document(html)
    text = document.get_content()
    semantic_structure = document.get_document_semantic_structure()

    link_targets = {
        text[start:stop]: document.resolve_link((start, stop))
        for start, stop in semantic_structure[SemanticElementType.LINK]
    }

    assert link_targets["article link"] == LinkTarget(
        url="https://en.wikipedia.org/wiki/Linked_article",
        is_external=True,
    )
    assert link_targets["details link"].is_external is False
    start, stop = link_targets["details link"].position
    assert text[start:stop].strip() == "Details"
    assert link_targets["history link"].is_external is False
    start, stop = link_targets["history link"].position
    assert text[start:stop].strip() == "\u6b77\u53f2"
    assert len(semantic_structure[SemanticElementType.TABLE]) == 1
    table_markup = document.get_document_table_markup(0)
    assert "<th>Language</th>" in table_markup
    assert "<td>Python</td>" in table_markup
    assert "<td>table link</td>" in table_markup


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://en.wikipedia.org/wiki/Sample", ("en", "Sample")),
        ("https://en.m.wikipedia.org/wiki/Sample", ("en", "Sample")),
        (
            "https://zh-min-nan.wikipedia.org/wiki/Sample%20title",
            ("zh-min-nan", "Sample title"),
        ),
        ("https://en.wikipedia.org/wiki/Foo%2520Bar", ("en", "Foo%20Bar")),
        ("https://en.wikipedia.org/wiki/Sample?oldformat=true", None),
        ("https://foo.en.wikipedia.org/wiki/Sample", None),
        ("https://www.wikipedia.org/wiki/Sample", None),
        ("ftp://en.wikipedia.org/wiki/Sample", None),
    ],
)
def test_wikipedia_article_info_accepts_article_urls_only(url, expected):
    assert WebHtmlDocument._get_wikipedia_article_info(url) == expected


def test_wikipedia_article_lookup_uses_app_user_agent_and_does_not_preload(monkeypatch):
    page_calls = []

    class FakeMediaWiki:
        def __init__(self, lang, user_agent):
            self.lang = lang
            self.user_agent = user_agent

        def page(self, **kwargs):
            page_calls.append((self.lang, self.user_agent, kwargs))
            return SimpleNamespace(
                title="Sample",
                html="<p>Article</p>",
                url="https://en.wikipedia.org/wiki/Sample",
            )

    monkeypatch.setattr(html_format, "MediaWiki", FakeMediaWiki)

    html = WebHtmlDocument._get_wikipedia_article_html("https://en.wikipedia.org/wiki/Sample")

    assert page_calls == [
        (
            "en",
            app.user_agent(),
            {
                "title": "Sample",
                "auto_suggest": False,
                "preload": False,
            },
        )
    ]
    assert "Article" in html
