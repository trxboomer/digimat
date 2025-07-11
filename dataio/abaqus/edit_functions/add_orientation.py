from typing import Literal, LiteralString
from .TemplateEditFunction import TemplateEditFunction as Template
import numpy as np
import numpy.typing as npt
from math_util import vector_transformation as vt


class add_orientation(Template):
    def __init__(
        self, phase_name: str, orientation_list: npt.NDArray[np.float64]
    ) -> None:
        self.phase_name = phase_name
        self.orientation_list = orientation_list
        self.orientation_ID = 0
        self.lines_to_skip = 1

    def descriptor(self) -> LiteralString:
        return "Adds the orientation of the elset to the input file"

    def common_name(self) -> LiteralString:
        return "Add Orientation to Fiber"

    def check_line(self, lines: list[str]) -> bool:
        for line in lines:
            if "Solid Section" in line and f"{self.phase_name}" in line:
                return True

        return False

    def next_orientation_ID(self):
        orientation_ID = f"Ori-{self.phase_name}-{self.orientation_ID}"
        self.orientation_ID += 1
        return orientation_ID

    def process_line(self, lines: list[str]) -> tuple[list[str], int]:  # type: ignore
        """Add new lines defining orientation, and edit Solid Section initialization to add orientation parameter

        Args:
            line (str): line from Abaqus file

        Returns:
            tuple[list[str], int]: _description_
        """
        for line in lines:
            if "Solid Section" not in line or f"{self.phase_name}" not in line:
                continue

            new_lines: list[str] = []
            for fiber_num, row in enumerate(self.orientation_list):
                # logger.debug(f"Parameters list: {param_list}")
                row = self.orientation_list[int(fiber_num)]

                a_points = vt.spherical_to_cartesian(theta=row[0], phi=row[1])
                b_points = vt.perpendicular_vector(a_points)
                orientation_name = self.next_orientation_ID()
                orientation = np.append(a_points, b_points)

                new_lines.append(f"*Orientation, name={orientation_name}\n")
                new_lines.append(", ".join(f"{x:6e}" for x in orientation) + "\n")
                new_lines.append("3, 0.\n")
                new_lines.append(
                    f"*Solid Section, elset={self.phase_name}_{fiber_num}, material=Carbon_Fiber, orientation={orientation_name}\n"
                )
                new_lines.append(",\n")

        return new_lines, self.lines_to_skip
