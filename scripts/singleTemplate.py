from digimat_scripts.scripts import add_fiber_orientation as afo
from digimat_scripts.dataio.digimat import RVE_generation as rve
from digimat_scripts.dataio.abaqus.include_functions import add_include as include
from digimat_scripts.script_utils import change_extension
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
        |-> Script log (.txt)
        |-> Digimat Input (dir)
        |-> Digimat Output (dir)
            |-> Digimat Logs
        |-> Abaqus Input Files (dir)
"""
#  python -m digimat_scripts.scripts.digimat_to_abaqus_v3
# Make sure that the analysis name in the daf file is "Template"


def singleTemplate(template_file_name,new_daf_name,num_samples,template_directory,temp_dir,output_dir):
    job_name = f"{new_daf_name}"

    new_dir = f"{temp_dir}\\{job_name}"

    digimat_in_dir = f"{new_dir}\\digimat_inp"
    digimat_out_dir = f"{new_dir}\\digimat_out"

    abaqus_inp_dir = f"{new_dir}\\abaqus_inp"

    all_dir = [new_dir, digimat_in_dir, digimat_out_dir, abaqus_inp_dir]

    for dir in all_dir:
        if os.path.exists(dir):
            os.rmdir(dir)
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

    rve.generate_daf(
        new_daf_name=new_daf_name,
        num_samples=num_samples,
        template_directory=new_dir,
        output_dir=digimat_in_dir,
    )

    logger.success("Created new daf files based off template")

    rve.batched_run(
        daf_file_path=digimat_in_dir, output_path=digimat_out_dir, log_path=new_dir
    )

    logger.remove()

    shutil.move(f"{new_dir}", f"{output_dir}")

