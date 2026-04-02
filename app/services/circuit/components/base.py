"""Backward-compatibility re-export. Use component.py directly in new code."""

from ..component import Component as SVGComponent

Terminal = None  # terminals are no longer declared on components

__all__ = ["SVGComponent"]
