import os
import shutil


def main(input_path: str, step_path: str, output_path: str):
    """
    Processes input and step files from specified directories, generating new files that
    combine input file references with the content of each step file, and organizes them
    into output directories.

    Parameters:
        input_path (str): Path to the directory containing '.inc' input files.
        step_path (str): Path to the directory containing '.inp' step files (should be a directory path, not a list).
        output_path (str): Path to the directory where output subdirectories and files will be created.

    Workflow:
        1. Collects all '.inc' files from the input directory.
        2. Collects all '.inp' files from the step directory.
        3. Reads all step files into memory.
        4. For each input file:
           a. Creates a subdirectory under the output path (named after the input file, without extension).
           b. Moves the input file into its corresponding subdirectory.
           c. For each step file:
              - Creates a new file in the output directory, named as '{input_name}-{step_name}' without extensions.
              - Writes an Abaqus-style *INCLUDE command referencing the input file.
              - Writes the entire content of the step file below the include command.

    Notes:
        - Uses '\\' as path separators; may need adjustment for cross-platform compatibility.
        - Overwrites files if their names already exist in the output directory.
        - Makes use of shutil and os modules for file and directory operations.
    """

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    input_files = [f for f in os.listdir(input_path) if f.endswith(".inc")]

    step_files = [f for f in os.listdir(step_path) if f.endswith(".inp")]

    step_lines: dict[str, list[str]] = {}

    for file in step_files:
        f = open(f"{step_path}/{file}", "r")

        step_lines.update({file: f.readlines()})

    for input in input_files:
        input_name = input[:-4]
        output_path_for_input = f"{output_path}/{input_name}"
        if not os.path.isdir(output_path_for_input):
            os.mkdir(output_path_for_input)

        shutil.move(f"{input_path}/{input}", f"{output_path_for_input}/{input}")

        for step_name, lines in step_lines.items():
            with open(f"{output_path}/{input_name}-{step_name[:-4]}", "w") as f:
                f.write(f"*INCLUDE, INPUT={input}\n")
                f.write("".join(lines))
