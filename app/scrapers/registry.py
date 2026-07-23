
from .fronius import FroniusScraper
from .autosolar import AutoSolarScraper

SCRAPERS = {
    'fronius': FroniusScraper(),
    'autosolar': AutoSolarScraper(),
}


def get_scraper(brand):
    return SCRAPERS.get(brand.lower())


def available():
    return sorted(SCRAPERS.keys())
