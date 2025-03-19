# coding: utf-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod

from bookworm import typehints as t
from bookworm.utils import escape_html


class BaseSpeechConverter(metaclass=ABCMeta):
    __slots__ = []
    escape = staticmethod(escape_html)

    def convert(self, utterance, *, localeinfo: LocaleInfo = None):
        return (
            self.start(localeinfo)
            + "\n".join(
                getattr(self, element.kind.name)(element.content)
                for element in utterance
            )
            + self.end()
        )

    @abstractmethod
    def start(self, localeinfo): ...

    @abstractmethod
    def end(self): ...

    @abstractmethod
    def text(self, content): ...

    @abstractmethod
    def ssml(self, content): ...

    @abstractmethod
    def sentence(self, content): ...

    @abstractmethod
    def bookmark(self, content): ...

    @abstractmethod
    def pause(self, content): ...

    @abstractmethod
    def audio(self, content): ...

    @abstractmethod
    def start_paragraph(self, content): ...

    @abstractmethod
    def end_paragraph(self, content): ...

    @abstractmethod
    def start_voice(self, content): ...

    @abstractmethod
    def end_voice(self, content): ...

    @abstractmethod
    def start_emph(self, content): ...

    def end_emph(self, content): ...

    @abstractmethod
    def start_prosody(self, content): ...

    @abstractmethod
    def end_prosody(self, content): ...
