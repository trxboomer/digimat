import scripts.add_fiber_orientation as afo
from scripts.RVE_generation import (
    generate_daf_file as generate_daf,
    run_daf_files as run_daf,
)
import os
import datetime
from loguru import logger
import shutil

"""
Each execution of the script will follow these steps:

1. A template file must be provided with the correct RVE parameters
2. A directory where outputs will be placed. If the directory is not empty, a new sub-directory will be made
Output structure will look like this:
|-> Output Directory
    |-> Template Directory
        |-> Original Template (.daf)
        |-> Digimat Log (.txt)
        |-> Script log (.txt)
        |-> Digimat Input (dir)
        |-> Digimat Output (dir)
        |-> Abaqus Input Files (dir)
"""
template_file_name = "Template"
new_daf_name = "test"
num_samples = 2
template_directory = r"C:\Users\harryhz\Documents\digimat_scripts\digimat\Template"
output_dir = r"D:\digimat_test"

now = datetime.datetime.now()
timestamp = now.strftime("%Y%m%d_%H-%M")
new_dir = f"{output_dir}\\{new_daf_name}-{timestamp}"

digimat_in_dir = f"{new_dir}\\digimat_inp"
digimat_out_dir = f"{new_dir}\\digimat_out"

abaqus_inp_dir = f"{new_dir}\\abaqus_inp"

all_dir = [new_dir, digimat_in_dir, digimat_out_dir, abaqus_inp_dir]

for dir in all_dir:
    os.mkdir(dir)

logger.add(
    f"{new_dir}\\script.log",  # Log file name with timestamp
    format="{time} {level} {message}",  # Custom format
)

logger.info("Created new directories")

src = f"{template_directory}\\{template_file_name}.daf"
dst = f"{new_dir}\\Template.daf"

shutil.copy(src, dst)

logger.info(f"Copied Template daf file from {src} to {dst}")

generate_daf(
    new_daf_name=new_daf_name,
    num_samples=num_samples,
    template_directory=template_directory,
    output_dir=digimat_in_dir,
)

logger.success("Created new daf files based off template")

run_daf(daf_file_path=digimat_in_dir, output_path=digimat_out_dir, log_path=new_dir)

afo.batched_run(input_path=digimat_out_dir, output_path=abaqus_inp_dir)
