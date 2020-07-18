# coding: utf-8

from abc import ABCMeta, abstractmethod
from io import StringIO


class BaseRenderer(metaclass=ABCMeta):
    """Renders a list of items to a string."""

    name = None
    """The name of this renderer."""

    display_name = None
    """The display name of this renderer."""

    output_ext = None
    """File extension of the output for this renderer."""

    def __init__(self, items, title):
        self.items = items
        self.title = title
        self.output = StringIO()
        self._done_sections = set()

    @abstractmethod
    def start_document(self):
        """Begin this document."""

    @abstractmethod
    def end_document(self):
        """End this document."""

    @abstractmethod
    def start_section(self, title):
        """Begin a new section."""

    @abstractmethod
    def end_section(self):
        """End the current section."""

    @abstractmethod
    def render_item(self, item):
        """Render a single item."""

    def render(self):
        self.start_document()
        for item in self.items:
            if item.section_identifier not in self._done_sections:
                if self._done_sections:
                    self.end_section()
                self.start_section(item.section_title)
                self._done_sections.add(item.section_identifier)
            self.render_item(item)
        self.end_document()
        text = self.output.getvalue()
        self.output.close()
        return text
