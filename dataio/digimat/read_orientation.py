from typing import Literal, Union, Tuple
import numpy as np
from numpy import typing as npt
from loguru import logger
from ..data_parsing import line_to_list


class OrientationFileError(Exception):
    pass


OrientationColumnName = Literal[
    "inclusion nb",
    "Z rotation",
    "theta",
    "phi",
    "rotMat11",
    "rotMat12",
    "rotMat13",
    "rotMat21",
    "rotMat22",
    "rotMat23",
    "rotMat31",
    "rotMat32",
    "rotMat33",
]


class DigimatPhaseOrientationFile:
    cols: dict[str, int] = {
        "inclusionnb": 0,
        "Zrotation": 1,
        "theta": 2,
        "phi": 3,
        "rotMat11": 4,
        "rotMat12": 5,
        "rotMat13": 6,
        "rotMat21": 7,
        "rotMat22": 8,
        "rotMat23": 9,
        "rotMat31": 10,
        "rotMat32": 11,
        "rotMat33": 12,
    }

    def __init__(self, filename: str, path: str, phase_name: str, debug: bool = False):
        """_summary_

        Args:
            filename (str): _description_
            path (str): _description_
            phase_name (str): _description_
            debug (bool, optional): _description_. Defaults to False.

        Raises:
            OrientationFileError: _description_
        """
        self.debug = debug
        self.filename = filename
        self.path = path
        self.phase_name = phase_name
        self.data: np.ndarray

        if not self.check_file():
            logger.error(f"Validation failed for {self.filename}")
            raise OrientationFileError(f"File check failed for {self.filename}")

    def check_file(self) -> bool:
        logger.info(f"Checking orientation file: {self.filename} at path: {self.path}")
        try:
            file = open(f"{self.path}/{self.filename}", "r")

        except FileNotFoundError:
            logger.error(f"Orientation file {self.filename} not found at {self.path}.")
            return False
        finally:
            header = line_to_list(file.readline(), delimiter=";")
            if any(col not in header for col in list(self.cols.keys())):
                logger.error(
                    f"Orientation file {self.filename} does not contain all required columns.\n Columns found: {header}\nColumns expected: {self.cols.keys()}"
                )
                return False
            logger.success(
                f"Orientation file {self.filename} in {self.path} found and validated."
            )
            return True

    def get_columns(
        self, columns: Union[Tuple[OrientationColumnName, ...], Tuple[Literal["all"],]]
    ) -> tuple[int, ...]:
        if "all" in columns:
            return tuple(self.cols.values())
        else:
            return tuple(idx for col, idx in self.cols.items() if col in columns)

    def get_csv(
        self, columns: Union[Tuple[OrientationColumnName, ...], Tuple[Literal["all"]]]
    ) -> npt.NDArray[np.float64]:

        logger.info(f"Reading orientation file: {self.filename} from path: {self.path}")

        self.data = np.genfromtxt(
            f"{self.path}/{self.filename}",
            delimiter=";",
            skip_header=1,
            dtype=float,
            usecols=self.get_columns(columns),
        )
        logger.debug(f"Data shape: {self.data.shape}")

        logger.success(
            f"Orientation data loaded from {self.filename} for phase {self.phase_name}"
        )
        if self.data.size == 0:
            logger.error(
                f"No data found in {self.filename} for phase {self.phase_name}."
            )
            raise OrientationFileError(
                f"No data found in {self.filename} for phase {self.phase_name}."
            )
        return self.data
