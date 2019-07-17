# coding: utf-8

from bookworm.concurrency import call_threaded
from bookworm.signals import notes_export_completed
from bookworm.logger import logger
from .core_renderers import MarkdownRenderer, HTMLRenderer, PlainTextRenderer


log = logger.getChild(__name__)


class NotesExporter:

    renderers = [PlainTextRenderer, HTMLRenderer, MarkdownRenderer]
    """A list of renderers."""

    def __init__(self, notes, renderer_name, filename, doc_title):
        target_renderer = [
            rend for rend in self.renderers if rend.name == renderer_name
        ]
        assert target_renderer, f"Renderer {renderer_name} is not a valid renderer."
        self.renderer = target_renderer[0]
        self.notes = notes
        self.filename = filename
        self.doc_title = doc_title

    def render_to_str(self):
        """Render a list of notes to a string."""
        return self.renderer(self.notes, self.doc_title).render()

    def render_to_file(self):
        # XXX Shouldn't  this be run in a different thread?
        log.debug(f"Rendering notes to file {self.filename}")
        content = self.render_to_str()
        with open(self.filename, "w", encoding="utf8") as file:
            file.write(content)
        notes_export_completed.send(self, filename=self.filename)
        log.debug("Done writing")
