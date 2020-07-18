# coding: utf-8

from bookworm.concurrency import call_threaded
from bookworm.signals import _signals
from bookworm.logger import logger
from .core_renderers import MarkdownRenderer, HTMLRenderer, PlainTextRenderer


log = logger.getChild(__name__)
export_completed = _signals.signal("items/export/completed")


class Exporter:

    renderers = [PlainTextRenderer, HTMLRenderer, MarkdownRenderer]
    """A list of renderers."""

    def __init__(self, items, renderer_name, filename, doc_title):
        target_renderer = [
            rend for rend in self.renderers if rend.name == renderer_name
        ]
        assert target_renderer, f"Renderer {renderer_name} is not a valid renderer."
        self.renderer = target_renderer[0]
        self.items = items
        self.filename = filename
        self.doc_title = doc_title

    def render_to_str(self):
        """Render a list of items to a string."""
        return self.renderer(self.items, self.doc_title).render()

    def render_to_file(self):
        # XXX Shouldn't  this be run in a different thread?
        log.debug(f"Rendering items to file {self.filename}")
        content = self.render_to_str()
        with open(self.filename, "w", encoding="utf8") as file:
            file.write(content)
        export_completed.send(self, filename=self.filename)
        log.debug("Done writing")
