# coding: utf-8

from dataclasses import dataclass, field
from pydantic import BaseModel
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class RemoteJsonResource:
    url: str
    model: BaseModel

