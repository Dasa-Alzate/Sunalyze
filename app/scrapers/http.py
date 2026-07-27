
import hashlib
import logging
import re
import time
import urllib.robotparser
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import lxml.html
import requests

from app.extensions import db
from app.models.scrape_cache import ScrapeCache

logger = logging.getLogger(__name__)

USER_AGENT = 'SunalyzeBot/0.1 (+catalog-sync; contact: ops@sunalyze.es)'
TIMEOUT = 20
PAUSE = 0.3

Fetched = namedtuple('Fetched', 'url text etag last_modified content_hash')

_robots = {}


class RobotsDisallowed(Exception):
    pass


def _url_hash(url):
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


_VOLATILE = re.compile(r'[0-9a-fA-F]{24,}')


def html_fingerprint(text):
    try:
        doc = lxml.html.fromstring(text)
    except Exception:
        return text
    for el in doc.xpath('//script | //style | //noscript'):
        el.drop_tree()
    visible = ' '.join(doc.text_content().split())
    links = ' '.join(sorted(set(doc.xpath('//a/@href'))))
    return _VOLATILE.sub('·', f'{visible}\n{links}')


def _digest(text, fingerprint):
    material = fingerprint(text) if fingerprint else text
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def _robots_for(url):
    parts = urlsplit(url)
    origin = (parts.scheme, parts.netloc)
    if origin in _robots:
        return _robots[origin]
    url = urlunsplit((parts.scheme, parts.netloc, '/robots.txt', '', ''))
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(url)
    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
        if resp.status_code == 200:
            parser.parse(resp.text.splitlines())
        else:
            parser.allow_all = True
    except Exception:
        logger.warning('No se pudo leer robots.txt de %s; se asume permitido', parts.netloc)
        parser = None
    _robots[origin] = parser
    return parser


def ensure_allowed(url):
    parser = _robots_for(url)
    if parser is not None and not parser.can_fetch(USER_AGENT, url):
        raise RobotsDisallowed(f'robots.txt prohíbe {url}')


def plain_get(url):
    ensure_allowed(url)
    resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
    time.sleep(PAUSE)
    resp.raise_for_status()
    return resp.text


def conditional_get(url, force=False, fingerprint=None, binary=False):
    ensure_allowed(url)
    entry = ScrapeCache.query.filter_by(url_hash=_url_hash(url)).first()
    headers = {'User-Agent': USER_AGENT}
    if entry and not force:
        if entry.etag:
            headers['If-None-Match'] = entry.etag
        if entry.last_modified:
            headers['If-Modified-Since'] = entry.last_modified

    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    time.sleep(PAUSE)

    if resp.status_code == 304:
        _bump(entry)
        return None
    resp.raise_for_status()

    if binary:
        body = resp.content
        digest = hashlib.sha256(body).hexdigest()
    else:
        body = resp.text
        digest = _digest(body, fingerprint)
    if entry and not force and entry.content_hash == digest:
        _bump(entry)
        return None

    return Fetched(url=url, text=body, etag=resp.headers.get('ETag'),
                   last_modified=resp.headers.get('Last-Modified'), content_hash=digest)


def remember(fetched):
    if fetched is None:
        return
    entry = ScrapeCache.query.filter_by(url_hash=_url_hash(fetched.url)).first()
    if entry is None:
        entry = ScrapeCache(url_hash=_url_hash(fetched.url), url=fetched.url[:500])
        db.session.add(entry)
    entry.etag = fetched.etag
    entry.last_modified = fetched.last_modified
    entry.content_hash = fetched.content_hash
    entry.fetched_at = datetime.utcnow()


def _bump(entry):
    if entry is not None:
        entry.hit_count = (entry.hit_count or 0) + 1
        entry.fetched_at = datetime.utcnow()
