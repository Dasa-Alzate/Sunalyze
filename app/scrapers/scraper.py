
from abc import ABC, abstractmethod

from . import http


class BrandScraper(ABC):
    brand = None
    kind = None
    requires_product_brand = False
    _force = False

    def fetch(self, ref, force=False):
        fetched = http.conditional_get(ref['url'], force=force,
                                       fingerprint=http.html_fingerprint)
        if fetched is None:
            return None
        ref['_fetched'] = fetched
        return fetched.text

    def remember(self, ref):
        http.remember(ref.pop('_fetched', None))

    @abstractmethod
    def discover(self):
        raise NotImplementedError

    @abstractmethod
    def parse(self, ref, raw):
        raise NotImplementedError
