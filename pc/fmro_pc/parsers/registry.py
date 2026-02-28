from __future__ import annotations

from fmro_pc.parsers.base import Parser
from fmro_pc.parsers.boss_zhipin import BossZhipinParser
from fmro_pc.parsers.generic_html import GenericHtmlParser
from fmro_pc.parsers.liepin import LiepinParser
from fmro_pc.parsers.shixiseng import ShiXiSengParser

PARSER_REGISTRY: dict[str, Parser] = {
    "generic_html": GenericHtmlParser(),
    "boss_zhipin": BossZhipinParser(),
    "liepin": LiepinParser(),
    "shixiseng": ShiXiSengParser(),
}


def get_parser(name: str) -> Parser:
    parser = PARSER_REGISTRY.get(name)
    if parser is None:
        supported = ", ".join(sorted(PARSER_REGISTRY))
        raise ValueError(f"unknown parser '{name}'. Supported: {supported}")
    return parser
