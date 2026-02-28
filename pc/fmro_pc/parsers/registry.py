from __future__ import annotations

from fmro_pc.parsers.base import Parser
from fmro_pc.parsers.generic_html import GenericHtmlParser

PARSER_REGISTRY: dict[str, Parser] = {
    "generic_html": GenericHtmlParser(),
}


def get_parser(name: str) -> Parser:
    parser = PARSER_REGISTRY.get(name)
    if parser is None:
        supported = ", ".join(sorted(PARSER_REGISTRY))
        raise ValueError(f"unknown parser '{name}'. Supported: {supported}")
    return parser
