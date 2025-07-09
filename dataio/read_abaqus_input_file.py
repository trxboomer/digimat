from typing import Literal, TypedDict
from io import TextIOWrapper
from loguru import logger
from data_parsing import line_to_list


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
) -> tuple[str, set_info | keyword_info] | None:
    keyword: str = param_list[0]
    if keyword == "*Surface":
        name = param_list[2].split("=")[1]
        return (name, {"start_line": line_no})

    if keyword in ["*Elset", "*Nset"]:
        name = param_list[1].split("=")[1]
        generate = False
        if "generate" in param_list:
            generate = True
        return (name, {"start_line": line_no, "generate": generate})

    if keyword == "*NODE":
        name = param_list[1].split("=")[1]
        return (name, {"start_line": line_no})

    if keyword == "*Element":
        name = param_list[2].split("=")[1]
        return (name, {"start_line": line_no})

    if keyword == "*Orientation":
        name = param_list[1].split("=")[1]
        return (name, {"start_line": line_no})
    if keyword == "*SolidSection":
        name = param_list[1].split("=")[1]
        return (name, {"start_line": line_no})

    else:
        logger.warning(
            "Key could not be organized, ensure that the key is correctly spelt, and that it is listed above"
        )
    return None


class AbaqusInputFileError(Exception):
    """Custom exception for errors related to Abaqus input files."""

    pass


class AbaqusInputFile:
    def __init__(self, filename: str, path: str):
        self.filename = filename
        self.path = path
        self.file = self.open_file()
        self.cache: cache_type = {
            "Surface": {},
            "NODE": {},
            "Element": {},
            "Orientation": {},
            "SolidSection": {},
            "Elset": {},
            "Nset": {},
        }
        self.phase_name_list: list[str] = []

    def open_file(self) -> TextIOWrapper:
        """Open the Abaqus input file and return the file object."""
        try:
            file = open(f"{self.path}/{self.filename}", "r")
            logger.info(f"Opened Abaqus input file: {self.filename}")
            return file
        except FileNotFoundError:
            raise AbaqusInputFileError(
                f"Abaqus input file {self.filename} not found at {self.path}."
            )

    def cache_keywords(self, keyword_args: tuple[Literal[keywords]]) -> None:
        """Create a cache based on the selected keywords

        Args:
            file (TextIOWrapper): file objet to read the Abaqus input file

        Returns:
            nodes_type: _description_
        """

        self.file.seek(0)  # Reset file pointer to the beginning

        for line_no, line in enumerate(self.file):
            if "*" not in line:
                continue

            params = line_to_list(line)

            key = params[0][1:]  # Remove the asterisk from the keyword
            if key not in keyword_args:
                continue

            result = organize_key(params, line_no)
            if result is not None:
                name, info = result
                self.cache[key][name] = info  # type: ignore

        for key in keyword_args:
            if self.cache[key] == {}:
                logger.warning(f"No {key} found in the file.")
        logger.success(
            "Cache created successfully with the following keywords: {}", keyword_args
        )

    def get_phase_name(
        self, potential_phase_name: list[str], return_name: bool = False
    ) -> str:
        if "Elset" not in self.cache:
            self.cache_keywords(("Elset",))
        for name in self.cache["Elset"]:
            if any(name in phase_name for phase_name in potential_phase_name):
                self.phase_name_list.append(name)

                if return_name:
                    return name
        raise AbaqusInputFileError(f"Fiber name not found in fiber name list.")

    def get_all_phase(
        self,
        phase_name: str | None = None,
        phase_name_list: list[str] | None = None,
        return_list: bool = False,
    ) -> list[str] | None:
        """Update the phase_name_list attribute with all instances of the given phase name or list of phase names.
        If no phase name is provided, a phase name will be retrieved from the phase_name_list.

        Args:
            phase_name (str | None, optional): Name of the phase to search for. Defaults to None.
            phase_name_list (list[str] | None, optional): List of potential phase names. Defaults to None.
            return_list (bool, optional): bool for whether or not to return the names of each instance. Defaults to False.

        Returns:
            list[str] | None: list of instance names of the phase
        """

        def main(phase_name: str):
            instance_counter = 0
            found_phase = True
            while found_phase is True:
                if (
                    self.cache["Elset"].get(f"{phase_name}_{instance_counter}")
                    is not None
                ):
                    self.phase_name_list.append(f"{phase_name}_{instance_counter}")
                    instance_counter += 1

                else:
                    found_phase = False

            if instance_counter == 0:
                raise AbaqusInputFileError(
                    f"Phase name {phase_name} not found in the file."
                )
            if return_list is True:
                return self.phase_name_list

        if phase_name is None and phase_name_list is None:
            raise AbaqusInputFileError(
                "Either phase_name or phase_name_list must be provided."
            )

        if phase_name is None and phase_name_list is not None:
            if "Elset" not in self.cache:
                self.cache_keywords(("Elset",))
            phase_name = self.get_phase_name(phase_name_list)

            main(phase_name)

        elif phase_name is not None and getattr(self, "phase_name_list") is not None:
            if phase_name not in self.phase_name_list:
                if not self.get_phase_name([phase_name]):
                    raise AbaqusInputFileError(
                        f"Phase name {phase_name} not found in the file."
                    )

            main(phase_name)
