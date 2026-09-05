
from .fronius import FroniusScraper
from .autosolar import AutoSolarScraper
from .cec import CECScraper
from .cec_battery import CECBatteryScraper
from .cec_inverter import CECInverterScraper

SCRAPERS = {
    'fronius': FroniusScraper(),
    'autosolar': AutoSolarScraper(),
    'cec': CECScraper(),
    'cec-baterias': CECBatteryScraper(),
    'cec-inversores': CECInverterScraper(),
}


def get_scraper(brand):
    return SCRAPERS.get(brand.lower())


def available():
    return sorted(SCRAPERS.keys())
