from abc import abstractmethod


class TemplateEditFunction:
    """Template class that the edit_line function in write_abaqus_input_file module accepts"""

    def __init__(self) -> None:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def common_name(self) -> str:
        pass

    @abstractmethod
    def check_line(self, lines: list[str]) -> bool:
        """Function that determines if the current function is applicable to the given line

        Args:
            line (str): line from file

        Returns:
            bool: True if function should be applied to line, else False
        """
        pass

    @abstractmethod
    def process_line(self, lines: list[str]) -> tuple[list[str], int]:
        """Edit the line (and subsequent lines if nessassary)

        Args:
            line (str): line from file

        Returns:
            list[str]: list of lines to be added
            int: number of lines to skip after the current line
        """
        pass
