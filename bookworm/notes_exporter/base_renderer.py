# coding: utf-8

from abc import ABCMeta, abstractmethod


class BaseRenderer(metaclass=ABCMeta):
    """Renders a list of notes to a string."""

    name = None
    """The name of this renderer."""

    display_name = None
    """The display name of this renderer."""

    output_ext = None
    """File extension of the output for this renderer."""

    def __init__(self, notes, title):
        self.notes = notes
        self.title = title
        self.output = []
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
    def render_note(self, note):
        """Render a single note."""

    def render(self):
        self.start_document()
        for note in self.notes:
            if note.section_identifier not in self._done_sections:
                if self._done_sections:
                    self.end_section()
                self.start_section(note.section_title)
                self._done_sections.add(note.section_identifier)
            self.render_note(note)
        self.end_document()
        return "".join(self.output)
