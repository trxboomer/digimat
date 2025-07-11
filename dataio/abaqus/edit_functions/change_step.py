import shutil


def add_step(
    input_file: str,
    input_path: str,
    step_names: list[str],
    output_path: str,
    no_step: bool = True,
):
    """Creates a input and adds a new step to it using the *Include keyword provided by Abaqus

    Args:
        input_file (str): Input file of interest, including extension name
        step_names (list[str]): list of .inc files that contains steps
    """
    original_input_path = f"{input_path}\\{input_file}"
    for step_file in step_names:
        step_name = step_file[:-3]
        output_file_path = f"{output_path}\\{input_file[:-3]}-{step_name}.inp"
        shutil.copy(original_input_path, output_file_path)

        with open(output_file_path, "a") as file:
            file.write(f"*INCLUDE, INPUT={step_name}")
