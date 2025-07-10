import re

whitespace_re = re.compile(r"\s+", flags=re.UNICODE)


def line_to_list(line: str, delimiter: str = ",") -> list[str]:
    # Remove all whitespace (Unicode) and split by comma
    line = whitespace_re.sub("", line)
    return line.split(delimiter)
