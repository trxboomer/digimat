from dataclasses import dataclass


def organize_key(param_list, line_no: int) -> dict["str":int]:
    keyword = param_list[0]
    if keyword == "*Surface":
        name = param_list[2].split("=")[1]
        return {name: {"start line": line_no}}

    if keyword in ["*Elset", "*Nset"]:
        name = param_list[1].split("=")[1]
        generate = False
        if "generate" in param_list:
            generate = True
        return {name: {"start line": line_no, "generate": generate}}

    if keyword == "*NODE":
        name = param_list[1].split("=")[1]

        return {name: {"start line": line_no}}

    if keyword == "*Element":
        name = param_list[2].split("=")[1]
        return {name: {"start line": line_no}}

    if keyword == "*Orientation":
        name = param_list[1].split("=")[1]
        return {name: {"start line": line_no}}

    if keyword == "*SolidSection":
        name = param_list[1].split("=")[1]
        return {name: {"start line": line_no}}

    else:
        logger.error(
            "Key could not be organized, ensure that the key is correctly spelt, and that it is listed above"
        )


@dataclass
class key:

    name: str
    start_line: int


@dataclass
class Set:
    name: str
    start_line: int
    generate: bool


@dataclass
class Orientation:
    name: str
    start_line: int


@dataclass
class SolidSection:
    name: str
    start_line: int
