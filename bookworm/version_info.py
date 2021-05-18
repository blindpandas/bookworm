# coding: utf-8

from dataclasses import dataclass, asdict
from bookworm import app


PRE_TYPE_REPLACEMENT_MAP = {
    'dev': 'dev',
    'alpha': 'a',
    'beta': 'b',
    'rc': 'rc',
}
PRE_TYPE_AS_NUMBER = {
    'dev': 0,
    'a': 1,
    'b': 2,
    'rc': 3,
}
POST_TYPE_AS_NUMBER = {
    'post': 0
}


@dataclass
class VersionInfo:
    major: int
    minor: int
    pre: str
    pre_type: str
    pre_number: int
    post: str
    post_type: str
    post_number: int

    @classmethod
    def from_version_string(cls, version_string):
        return cls(**app.get_version_info(version_string))

    def get_components(self):
        return (
            self.major,
            self.minor,
            self.pre_type,
            self.pre_number,
            self.post_type,
            self.post_number
        )

    @property
    def is_pre_release(self):
        return self.pre is not None

    @property
    def is_final(self):
        return not self.is_pre_release

    def __str__(self):
        return "".join(self.get_components())

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
