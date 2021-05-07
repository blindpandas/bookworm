#!/usr/bin/env python
# -*- coding: utf-8 -*- #

from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))
from contentblocks import *
sys.path.pop(0)

PATH = 'content'
AUTHOR = 'Blind Pandas Team'
SITEURL = 'https://getbookworm.com'
SITENAME = 'Bookworm'
SITESUBTITLE = "The universally accessible document reader"
TIMEZONE = 'Africa/Khartoum'
DEFAULT_LANG = 'en'
DEFAULT_CATEGORY  = 'Uncategorised'
RELATIVE_URLS = True
DEVELOPMENT = True
LOAD_CONTENT_CACHE = False
DIRECT_TEMPLATES = ['index',]

# Re-map URLs
ARTICLE_URL = 'blog/{slug}/'
ARTICLE_SAVE_AS = 'blog/{slug}/index.html'
ARTICLE_LANG_URL = 'blog/{lang}/{slug}'
ARTICLE_LANG_SAVE_AS = 'blog/{lang}/{slug}/index.html'
AUTHOR_URL = 'blog/author/{slug}.html'
AUTHOR_SAVE_AS = 'blog/author/{slug}.html'
CATEGORY_URL = 'blog/category/{slug}.html'
CATEGORY_SAVE_AS = 'blog/category/{slug}.html'
TAG_URL = 'blog/tag/{slug}.html'
TAG_SAVE_AS = 'blog/tag/{slug}.html'
AUTHORS_SAVE_AS = 'blog/authors.html'
CATEGORIES_SAVE_AS = 'blog/categories.html'
TAGS_SAVE_AS = 'blog/tags.html'
PAGE_URL = '{slug}'
PAGE_SAVE_AS = '{slug}/index.html'
PAGE_LANG_URL = '{lang}/{slug}'
PAGE_LANG_SAVE_AS  = '{lang}/{slug}/index.html'

# We don't need to generate the following
DRAFT_SAVE_AS = ''
DRAFT_LANG_SAVE_AS = ''
DRAFT_PAGE_SAVE_AS = ''
DRAFT_PAGE_LANG_SAVE_AS = ''

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Custom theme
THEME  = Path.cwd() / "theme"
THEME_STATIC_DIR = 'theme'

# Static files
STATIC_PATHS = ['static', 'extra/CNAME']
EXTRA_PATH_METADATA = {
    'extra/CNAME': {'path': 'CNAME'},
    'static/*': {'path': 'static/'},
    'static/images/favicon.ico': {'path': 'favicon.ico'},
}

# Plugins
PLUGIN_PATHS = ('plugins',)
PLUGINS = ('seo', 'htmlcompress', 'readtime',)

# SEO
SEO_REPORT = True  # To enable this feature
SEO_ENHANCER = True
IMAGE_PATH = 'static/images'

# OG properties
OG_LOCALE = "en_US"
HEADER_COVER = "static/images/logo512x512.png"
