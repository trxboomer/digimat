from __init__ import (
    AbaqusInputFile,
    DigimatPhaseOrientationFile,
    OrientationFileError,
    FiberData,
)
from loguru import logger


class add_phase_orientation(AbaqusInputFile, DigimatPhaseOrientationFile):
    """Add fiber orientation retrieved from Digimat RVE generation to Abaqus input file."""

    def __init__(
        self,
        filename: str,
        path: str,
        fiber_name_list: list[str],
        matrix_name_list: list[str],
        inclusion_name: str = "Fiber",
        debug: bool = False,
    ):
        AbaqusInputFile.__init__(
            self,
            filename=filename,
            path=path,
            fiber_name_list=fiber_name_list,
            matrix_name_list=matrix_name_list,
        )
        DigimatPhaseOrientationFile.__init__(
            self,
            filename=f"{self.phase_name}_orientation.txt",
            path=".",
            phase_name="fiber",
            debug=debug,
        )
        self.inclusion_name: str = inclusion_name
        self.get_all_fibers()

        self.phase_orientation = self.get_phase_orientation()
        self.orientation_ID = 0

    def next_orientation_ID(self, material_name: str):
        orientation_ID = f"Ori-{material_name}-{self.orientation_ID}"
        self.orientation_ID += 1
        return orientation_ID

    def add_orientation(self, line: str):
        if "Solid Section" not in line or self.fiber_name not in line:
            return line

        param_list = self.line_to_list(line)

        # logger.debug(f"Parameters list: {param_list}")
        fiber_name = param_list[1].split("=")[1]
        fiber = self.fiber_list[fiber_name]
        new_lines: str = f"*Orientation, name={fiber.orientation_ID}\n"
        new_lines += ", ".join(f"{x:6e}" for x in fiber.orientation) + "\n"
        new_lines += "3, 0.\n"
        new_lines += f"{line}, orientation={fiber.orientation_ID}\n"

        return new_lines

    @staticmethod
    def header(kwargs: dict[str, bool]):
        header = "**Modification parameters:"
        for k, v in kwargs.items():
            header += f"** {k}: {v}\n"
        header += "\n"
        # logger.debug(f"File Header: {header}")  # Separate header from content
        return header

    def create_file(self, out_dest: str):
        kwargs = {"Fiber Orientation": True}

        self.file.seek(0)
        with open(f"{out_dest}/{self.filename[:-4]}-modified.inp", "a") as f:
            f.write(self.header(kwargs=kwargs))
            for line in self.file:
                f.write(self.add_orientation(line))

    def run(
        self,
        new_file: bool = False,
        output_path: str = ".",
    ):
        for row in self.phase_orientation:
            current_phase = self.fiber_name + f"_{row[0]}"

            if current_phase not in self.fiber_list:
                logger.error(f"Phase {current_phase} not found in fiber list.")
                continue

            self.fiber_list[current_phase].orientation = row[1:7]
            self.fiber_list[current_phase].orientation_ID = self.next_orientation_ID(
                self.fiber_name
            )

        if new_file:
            self.create_file(out_dest=output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print(
            "Usage: python add_fiber_orientation.py <file name> <file path> <fiber_name_list> <matrix_name_list> [<inclusion_name>]"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    fiber_name_list = sys.argv[2].split(",")
    matrix_name_list = sys.argv[3].split(",")
    inclusion_name = sys.argv[4] if len(sys.argv) > 4 else "Fiber"

    modifier = add_phase_orientation(
        filename=input_file,
        path=".",
        fiber_name_list=fiber_name_list,
        matrix_name_list=matrix_name_list,
        inclusion_name=inclusion_name,
    )
    modifier.run(new_file=True, output_path=".")
