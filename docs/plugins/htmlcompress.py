# coding: utf-8

import logging
from htmlmin.minify import html_minify
from pelican import signals

log = logging.getLogger(__name__)


def run_htmlmin(path, context):
    with open(path, 'r', encoding='utf8') as htmlcontent:
        mincontent = html_minify (htmlcontent.read())
    with open(path, 'w', encoding='utf8') as file:
        file.write(mincontent)


def register():
    signals.content_written.connect(run_htmlmin)