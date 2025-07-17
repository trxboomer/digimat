import itertools
import os
import shutil
from change_step import add_step
from loguru import logger


def check_directory(dir_path: str):
    include_dir: dict[str, list[str]] = {}
    with os.scandir(dir_path) as entries:
        directories = [entry.name for entry in entries if entry.is_dir()]

    if directories == []:
        raise FileNotFoundError(f"No include sets found in {dir_path}")

    for directory in directories:
        current_dir = f"{dir_path}{directory}"
        files = [
            f
            for f in os.listdir(current_dir)
            if os.path.isfile(os.path.join(current_dir, f)) and f.endswith(".inp")
        ]

        if files != []:
            include_dir.update({directory: files})

    logger.debug(f"Include sets found: {directories}")
    return include_dir


def create_partition_scheme(
    include_sets: dict[str, list[str]], lowest_group: str | None
):
    intermediate_sets = include_sets.copy()

    if lowest_group:
        del intermediate_sets[lowest_group]

    temp: list[list[str]] = []
    for set_name, set_values in intermediate_sets.items():
        temp1: list[str] = []
        for value in set_values:
            temp1.append(f"{set_name}-{value}")

        temp.append(temp1)

    if lowest_group:
        lowest_group_set = include_sets[lowest_group]
        return itertools.product(*temp), list(
            itertools.product(*temp, lowest_group_set)
        )

    return itertools.product(*temp), list(itertools.product(*temp))


def append_to_file(
    include_dir: str, input_dir: str, output_dir: str, lowest_group: str | None = None
):
    """ONLY WORKS FOR ADDING STEPS FOR NOW.

    For each input file, create a copy of the input file for each include file in the directory. Each sub directory should include a directory for each section that is being changed using *Include. New variations of the input file will be saved under the sub directory name. lowest group variable can be set to specify which Include set should be used to group the input files

    Input directory should follow this format:

    Input dir/
        └── Sub Dir/
            └── Include Set1/
                ├── include1.inc
                ├── include2.inc
                └── include3.inc
            └── Include Set2 (lowest group)/
                ├── include1.inc
                ├── include2.inc
                └── include3.inc

    Output dir/
        └── include1/
            └── Include Set2/
        └── include2/
            └── Include Set2/
        └── include3/
            └── Include Set2/

    Args:
        include_dir (str): Directory with the above structure
    """

    include_set = check_directory(include_dir)
    logger.debug(f"Sets to include {include_set}")
    input_files = [f for f in os.listdir(input_dir) if f.endswith("inp")]

    for input_file in input_files:
        input_file_dir = f"{output_dir}{input_file[:-4]}"
        os.mkdir(input_file_dir)
        for include_file in include_set["step"]:
            shutil.copy(
                f"{include_dir}/step/{include_file}",
                f"{input_file_dir}/{include_file}",
            )
        add_step(
            input_file=input_file,
            input_path=input_dir,
            step_names=include_set["step"],
            output_path=input_file_dir,
        )
        


if __name__ == "__main__":
    append_to_file(
        include_dir=r"/home/harry/Documents/abaqus/test-20250714_13-12/include/",
        input_dir=r"/home/harry/Documents/abaqus/test-20250714_13-12/abaqus_inp/",
        output_dir=r"/home/harry/Documents/abaqus/test-20250714_13-12/abaqus_inp_steps/",
    )
