from tabnanny import check
from typing import Literal, LiteralString
from .TemplateAbaqusEditFunction import TemplateEditFunction as Template
from .data_parsing import line_to_list
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


class change_material_property(Template):
    isotropy = Literal["Isotropic", "Anisotropic", "Orthotropic"]
    property_names = Literal["Conductivity", "Specific heat"]

    skip_lines = 1

    def __init__(
        self,
        material_name: str,
        property_name: property_names,
        new_isotropy: isotropy,
        new_values: tuple[float, ...],
    ) -> None:
        self.reached_material_properties = False
        self.material_name = material_name
        self.property_name = property_name
        self.new_isotropy = new_isotropy
        self.new_values = new_values
        self.check_inputs()
        self.isotropy_type = self.get_isotropy_type()
        pass

    def check_inputs(self):
        if self.new_isotropy == "Isotropic" and len(self.new_values) != 1:
            raise ValueError(
                f"Isotropic properties should only have one value, not {len(self.new_values)}"
            )
        elif (
            self.new_isotropy == "Anisotropic"
            or self.new_isotropy == "Orthotropic"
            and len(self.new_values) != 3
        ):
            raise ValueError(
                f"{self.new_isotropy} properties should have 3 values, not {len(self.new_values)}"
            )

    def get_isotropy_type(self):
        if self.new_isotropy == "Orthotropic":
            return ", type=ORTHO"
        if self.new_isotropy == "Isotropic":
            return ""

    def description(self):
        return "Changes the property of interest for a given material."

    def common_name(self) -> str:
        return "Change Material Properties"

    def check_line(self, lines: list[str]) -> bool:
        for line in lines:
            if self.reached_material_properties and self.property_name in line:
                return True

            else:
                if "Material" in line and self.material_name in line:
                    self.reached_material_properties = True

        return False

    def process_line(self, lines: list[str]) -> tuple[list[str], int]:
        new_lines: list[str] = []
        for line in lines:
            if self.property_name in line:
                new_lines.append(f"*{self.property_name}{self.isotropy_type}\n")
                value_line = ",".join(f"{x:6e}" for x in self.new_values) + "\n"
                new_lines.append(value_line)

            else:
                new_lines.append(line)

        self.reached_material_properties = False
        return new_lines, self.skip_lines
