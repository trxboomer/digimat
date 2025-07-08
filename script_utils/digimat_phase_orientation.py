from typing import Literal
import numpy as np
from numpy import typing as npt
from loguru import logger
from typing import Tuple, Union


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
        "inclusion nb": 0,
        "Z rotation": 1,
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
            with open(f"{self.path}{self.filename}", "r") as file:
                header = file.readline().strip().split(";")
                if not all(col in header for col in self.cols.keys()):
                    logger.error(
                        f"Orientation file {self.filename} does not contain all required columns."
                    )
                    return False
            logger.success(
                f"Orientation file {self.filename} in {self.path} found and validated."
            )
            return True
        except FileNotFoundError:
            logger.error(f"Orientation file {self.filename} not found at {self.path}.")
            return False

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

        data = np.genfromtxt(
            f"{self.path}{self.filename}",
            delimiter=";",
            skip_header=1,
            dtype=float,
            usecols=self.get_columns(columns),
        )
        logger.debug(f"Data shape: {self.data.shape}")

        logger.success(
            f"Orientation data loaded from {self.filename} for phase {self.phase_name}"
        )
        if data.size == 0:
            logger.error(
                f"No data found in {self.filename} for phase {self.phase_name}."
            )
            raise OrientationFileError(
                f"No data found in {self.filename} for phase {self.phase_name}."
            )
        return data

    @staticmethod
    def spherical_to_cartesian(
        theta: np.float64, phi: np.float64, r: int = 1
    ) -> npt.NDArray[np.float64]:
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        return np.array([x, y, z])

    @staticmethod
    def perpendicular_vector(
        vector: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        if not np.allclose(vector[:2], 0):
            temp_vector = np.array([0, 0, 1])
        else:
            temp_vector = np.array([1, 0, 0])

        normal_vector = np.cross(vector, temp_vector)
        return normal_vector / np.linalg.norm(
            normal_vector
        )  # Optional: make it a unit vector

    def get_phase_orientation(self):
        """Extracts spherical coordinates (theta, phi) from the orientation file and returns cartesian form + normal

        Returns:
            np.array: [fiber index, x, y, z, normal_x, normal_y, normal_z]
        """
        data = self.get_csv(columns=("theta", "phi"))
        phase_data = np.empty((data.shape[0], 7), dtype=np.float64)
        for idx, phase in enumerate(data):
            theta = phase[0]
            phi = phase[1]

            point_a = self.spherical_to_cartesian(theta, phi)
            point_b = self.perpendicular_vector(point_a)
            if self.debug:
                logger.debug(
                    f"Phase {idx} - Spherical: (theta={theta}, phi={phi}), Cartesian: {point_a}, Normal: {point_b}"
                )

            phase_data[idx] = np.concatenate((idx, point_a, point_b), axis=0)

        logger.success(f"Phase orientation data extracted from {self.filename}")
        return phase_data
