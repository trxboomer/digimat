from typing import LiteralString
from TemplateAbaqusEditFunction import TemplateEditFunction as Template
from data_parsing import line_to_list
import numpy as np
import numpy.typing as npt
from ..math_util import vector_transformation as vt


class add_orientation(Template):
    def __init__(
        self, phase_name: str, orientation_list: npt.NDArray[np.float64]
    ) -> None:
        self.phase_name = phase_name
        self.orientation_list = orientation_list
        self.orientation_ID = 0
        self.lines_to_skip = 1

    @property
    def descriptor(self) -> LiteralString:
        return "Adds the orientation of the elset to the input file"

    @property
    def common_name(self) -> LiteralString:
        return "Add Orientation to Fiber"

    def check_line(self, line: str) -> bool:
        if "Solid Section" not in line or self.phase_name not in line:
            return False
        else:
            return True

    def next_orientation_ID(self):
        orientation_ID = f"Ori-{self.phase_name}-{self.orientation_ID}"
        self.orientation_ID += 1
        return orientation_ID

    def process_line(self, line: str) -> tuple[list[str], int]:
        """Add new lines defining orientation, and edit Solid Section initialization to add orientation parameter

        Args:
            line (str): line from Abaqus file

        Returns:
            tuple[list[str], int]: _description_
        """
        param_list = line_to_list(line)

        # logger.debug(f"Parameters list: {param_list}")
        fiber_name = param_list[1].split("=")[1]
        fiber_num = fiber_name.split("_")[1]
        row = self.orientation_list[int(fiber_num)]

        a_points = vt.spherical_to_cartesian(theta=row[1], phi=row[2])
        b_points = vt.perpendicular_vector(a_points)
        orientation_name = self.next_orientation_ID()
        orientation = np.append(a_points, b_points)

        new_lines: list[str] = [f"*Orientation, name={orientation_name}\n"]
        new_lines.append(", ".join(f"{x:6e}" for x in orientation) + "\n")
        new_lines.append("3, 0.\n")
        new_lines.append(f"{line}, orientation={orientation_name}\n")

        return new_lines, self.lines_to_skip
