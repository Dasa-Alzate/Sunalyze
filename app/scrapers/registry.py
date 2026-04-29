"""Registro de scrapers por marca. Añadir una marca = registrar su adapter."""

from .fronius import FroniusScraper

SCRAPERS = {
    'fronius': FroniusScraper(),
}


def get_scraper(brand):
    return SCRAPERS.get(brand.lower())


def available():
    return sorted(SCRAPERS.keys())
