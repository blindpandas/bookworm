# coding: utf-8


import os
import winsound
from urllib.parse import urlparse

AUDIO_BOOKMARK_PREFIX = "audio: "
START_URI_AT = len(AUDIO_BOOKMARK_PREFIX)


def create_audio_bookmark_name(uri):
    return AUDIO_BOOKMARK_PREFIX + uri


def process_audio_bookmark(bookmark):
    if not bookmark.startswith(AUDIO_BOOKMARK_PREFIX):
        return False
    filepath = audio_uri_to_filepath(bookmark[START_URI_AT:])
    winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
    return True


def audio_uri_to_filepath(uri):
    path = urlparse(uri).path
    return os.path.abspath(path.lstrip("/"))
