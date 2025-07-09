from io import TextIOWrapper
from loguru import logger
from read_abaqus_input_file import AbaqusInputFileError


class modify_file:
    def __init__(
        self,
        output_path: str,
        output_filename: str,
        open_input_file: TextIOWrapper | None = None,
        input_path: str | None = None,
        input_filename: str | None = None,
    ):

        if (
            open_input_file is None
            and input_path is not None
            and input_filename is not None
        ):
            self.read_input_file(filename=input_filename, path=input_path)
        pass

    def read_input_file(self, filename: str, path: str):

        try:
            file = open(f"{path}/{filename}", "r")
            logger.info(f"Opened Abaqus input file: {path}")
            return file
        except FileNotFoundError:
            raise AbaqusInputFileError(
                f"Abaqus input file {filename} not found at {path}."
            )
