
import logging

import lxml.etree

from .http import plain_get

logger = logging.getLogger(__name__)

_LOC = '//*[local-name()="loc"]/text()'
_IS_INDEX = 'boolean(/*[local-name()="sitemapindex"])'


def _locs(xml):
    root = lxml.etree.fromstring(xml.encode('utf-8'))
    return bool(root.xpath(_IS_INDEX)), [str(loc).strip() for loc in root.xpath(_LOC)]


def discover_urls(index_url, keep=None, follow=None, max_depth=3):
    pending = [(index_url, 0)]
    seen_sitemaps = set()
    found = []
    found_seen = set()

    while pending:
        url, depth = pending.pop(0)
        if url in seen_sitemaps or depth > max_depth:
            continue
        seen_sitemaps.add(url)
        try:
            is_index, locs = _locs(plain_get(url))
        except Exception:
            logger.exception('Fallo al leer sitemap %s', url)
            continue

        for loc in locs:
            if is_index:
                if follow is None or follow(loc):
                    pending.append((loc, depth + 1))
            elif (keep is None or keep(loc)) and loc not in found_seen:
                found_seen.add(loc)
                found.append(loc)

    return found
