from email.policy import default
from functools import cache
from typing import Literal, TypedDict, NotRequired
import numpy as np
from io import TextIOWrapper
from loguru import logger
import re
from collections import defaultdict


class keyword_info(TypedDict):
    start_line: int


class set_info(TypedDict):
    start_line: int
    generate: bool


KeywordName = str  # The name of the keyword_info

keywords = Literal[
    "Surface",
    "Elset",
    "Nset",
    "NODE",
    "Element",
    "Orientation",
    "SolidSection",
]


class cache_type(TypedDict):
    Surface: dict[KeywordName, keyword_info]
    NODE: dict[KeywordName, keyword_info]
    Element: dict[KeywordName, keyword_info]
    Orientation: dict[KeywordName, keyword_info]
    SolidSection: dict[KeywordName, keyword_info]
    Elset: dict[KeywordName, set_info]
    Nset: dict[KeywordName, set_info]


def organize_key(
    param_list: list[str], line_no: int
) -> dict[str, dict[str, int | bool]] | None:
    keyword: str = param_list[0]
    if keyword == "*Surface":
        name = param_list[2].split("=")[1]
        return {name: {"start_line": line_no}}

    if keyword in ["*Elset", "*Nset"]:
        name = param_list[1].split("=")[1]
        generate = False
        if "generate" in param_list:
            generate = True
        return {name: {"start_line": line_no, "generate": generate}}

    if keyword == "*NODE":
        name = param_list[1].split("=")[1]
        return {name: {"start_line": line_no}}

    if keyword == "*Element":
        name = param_list[2].split("=")[1]
        return {name: {"start_line": line_no}}

    if keyword == "*Orientation":
        name = param_list[1].split("=")[1]
        return {name: {"start_line": line_no}}

    if keyword == "*SolidSection":
        name = param_list[1].split("=")[1]
        return {name: {"start_line": line_no}}

    else:
        logger.warning(
            "Key could not be organized, ensure that the key is correctly spelt, and that it is listed above"
        )
    return None


whitespace_re = re.compile(r"\s+", flags=re.UNICODE)


def line_to_list(line: str) -> list[str]:
    # Remove all whitespace (Unicode) and split by comma
    line = whitespace_re.sub("", line)
    return line.split(",")


def cache_keywords(
    file: TextIOWrapper, keyword_args: tuple[Literal[keywords]]
) -> cache_type:
    """Create a cache based on the selected keywords

    Args:
        file (TextIOWrapper): file objet to read the Abaqus input file

    Returns:
        nodes_type: _description_
    """
    cache: cache_type = {
        "Surface": {},
        "NODE": {},
        "Element": {},
        "Orientation": {},
        "SolidSection": {},
        "Elset": {},
        "Nset": {},
    }

    file.seek(0)  # Reset file pointer to the beginning

    for line_no, line in enumerate(file):
        if "*" not in line:
            continue

        params = line_to_list(line)

        key = params[0][1:]  # Remove the asterisk from the keyword
        if key not in keyword_args:
            continue

        cache[key].update(organize_key(params, line_no))
