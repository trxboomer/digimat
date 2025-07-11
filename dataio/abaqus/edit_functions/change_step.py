from dataio.abaqus.edit_functions.TemplateEditFunction import TemplateEditFunction


class add_step(TemplateEditFunction):
    """Creates a new step using the *Include

    Args:
        TemplateEditFunction (_type_): _description_
    """

    def __init__(self, step_name: str, step_lines: str, end_file: bool = True) -> None:
        self.step_name = step_name
        self.step_lines = step_lines
        self.end_file = end_file

    def description(self) -> str:
        return "Creates a new step in the abaqus input file"

    def common_name(self) -> str:
        return "Add Step"

    def check_line(self, lines: list[str]) -> bool:
        if any(self.step_name in line for line in lines):
            return True
        else:
            return False

    def process_line(self, lines: list[str]) -> tuple[list[str], int]:

        return super().process_line(lines)
