# coding: utf-8

import requests
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
from bookworm.logger import logger


log = logger.getChild(__name__)


@dataclass
class RemoteJsonResource:
    url: str
    model: BaseModel

    def request_data(self):
        try:
            return requests.get(self.url).json()
        except requests.RequestException:
            raise ConnectionError(f"Failed to get url {self.url}")
        except ValueError:
            raise ValueError("Failed to parse JSON data obtained from {self.url}")

    def parse_data(self, data):
        try:
            return self.model.parse_obj(data)
        except ValidationError:
            log.exception("Failed to validate data against the model. \n{e.errors()}", exc_info=True)
            raise ValueError(f"Failed to parse data {data} against model {self.model}.")

    def get(self):
        return self.parse_data(self.request_data())
