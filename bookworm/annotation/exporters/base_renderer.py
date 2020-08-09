# coding: utf-8

from abc import ABCMeta, abstractmethod
from io import StringIO


class BaseRenderer(metaclass=ABCMeta):
    """Renders a list of items (Comments or Quotes."""

    name = None
    """The name of this renderer."""

    display_name = None
    """The display name of this renderer."""

    output_ext = None
    """File extension of the output for this renderer."""

    def __init__(self, items, options, filter_options):
        self.items = items
        self.options = options
        self.book = (
            self.items[0].book.title if filter_options.book_id is not None else None
        )
        self.tag = filter_options.tag
        self.section = filter_options.section_title

    @abstractmethod
    def start_document(self):
        """Begin this document."""

    @abstractmethod
    def end_document(self):
        """End this document."""

    @abstractmethod
    def render_item(self, item):
        """Render a single item."""

    @abstractmethod
    def render_to_file(self):
        """Render the items to the output file."""


class TextRenderer(BaseRenderer, metaclass=ABCMeta):
    """A renderer that renders its content to a string buffer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = StringIO()

    def render_to_file(self):
        self.start_document()
        for item in self.items:
            self.render_item(item)
        self.end_document()
        text = self.output.getvalue()
        self.output.close()
        with open(self.options.output_file, "w", encoding="utf8") as file:
            file.write(text)
        return self.options.output_file
