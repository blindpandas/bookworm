# coding: utf-8

from abc import ABC, abstractmethod
from collections.abc import Iterator
from bookworm import typehints as t
from bookworm.utils import random_uuid
from bookworm.logger import logger

log = logger.getChild(__name__)

class BookshelfProvider:
    name: str = None
    display_name: t.TranslatableStr = None

    @abstractmethod
    def check(self) -> bool:
        """Checks the availability of this provider at runtime."""

    def __iter__(self):
        