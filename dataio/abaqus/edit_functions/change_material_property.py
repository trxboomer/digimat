from typing import Literal
from ..TemplateEditFunction import TemplateEditFunction as Template


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
