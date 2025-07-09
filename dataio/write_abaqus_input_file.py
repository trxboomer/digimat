from io import TextIOWrapper
from typing import List
from collections.abc import Callable
from loguru import logger
from read_abaqus_input_file import AbaqusInputFileError
from datetime import datetime
import os


class modify_file:
    def __init__(
        self,
        output_path: str,
        edit_functions: List[Callable[[str], list[str]]],
        output_filename: str | None = None,
        open_input_file: TextIOWrapper | None = None,
        input_path: str | None = None,
        input_filename: str | None = None,
    ):
        self.file: TextIOWrapper
        self.output_filename: str
        self.parse_args(
            open_input_file, input_path, input_filename, output_path, output_filename
        )
        self.output_path = output_path
        self.edit_functions = edit_functions
        self.output_file: TextIOWrapper = self.write_input_file()
        pass

    def parse_args(
        self,
        open_input_file: TextIOWrapper | None,
        input_path: str | None,
        input_filename: str | None,
        output_path: str,
        output_filename: str | None,
    ) -> bool | None:
        if not os.path.exists(output_path):
            logger.info(f"Created new directory for output files at {output_path}")
            os.mkdir(path=output_path)

        if output_filename is not None:
            self.output_filename = output_filename

        elif input_filename is not None:
            self.output_filename = input_filename

        else:
            raise ValueError(
                f"Invalid arguments: output_filename = {output_filename}, "
                f"input_filename = {input_filename}"
            )

        if open_input_file:
            self.input_file = open_input_file

        elif input_path and input_filename:
            self.file = self.read_input_file(filename=input_filename, path=input_path)

        else:
            raise ValueError(
                f"Invalid arguments: open_input_file={open_input_file}, "
                f"input_path={input_path}, input_filename={input_filename}. "
                "Either open_input_file or both input_path and input_filename must be provided."
            )

    def read_input_file(self, filename: str, path: str) -> TextIOWrapper:
        try:
            file = open(f"{path}/{filename}", "r")
            logger.info(f"Opened Abaqus input file: {path}")
            return file
        except FileNotFoundError:
            raise AbaqusInputFileError(
                f"Abaqus input file {filename} not found at {path}."
            )

    def write_input_file(self) -> TextIOWrapper:
        """Creates a TextIOWrapper object that will be used to write the new input file

        Args:
            filename (str):
            path (str): _description_

        Raises:
            FileExistsError: _description_

        Returns:
            TextIOWrapper: _description_
        """
        try:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            file = open(
                f"{self.output_path}/{self.output_filename}-{timestamp}.inp", "w"
            )
            logger.info(
                f"Created new input file for {self.output_filename} in {self.output_path}"
            )
            return file

        except FileExistsError:
            raise FileExistsError("File with the same name exists")

    def edit_line(self, line: str) -> list[str]:
        lines = [line]
        for func in self.edit_functions:
            lines = func(line)
        return lines

    def copy_and_edit(self):
        for line in self.input_file:
            new_lines = self.edit_line(line)

            for new_line in new_lines:
                self.output_file.write(new_line)
