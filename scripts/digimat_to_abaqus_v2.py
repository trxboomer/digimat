from digimat_scripts.scripts import add_fiber_orientation as afo
from digimat_scripts.dataio.digimat import RVE_generation as rve
from digimat_scripts.dataio.abaqus.include_functions import add_include as include
from digimat_scripts.script_utils import change_extension
import os
import datetime
from loguru import logger
import shutil
import numpy as np


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

#Make sure that the analysis name in the daf file is "Template"
template_file_name = "SSDM-4"
new_daf_name = "SSDM-4"
description = "testt"
num_samples = 3
template_directory = r"Y:\Students\Zhou_Harry\abaqus\template"
temp_dir = r"C:\Users\harryhz\Documents\abaqus\temp"
output_dir = r"Y:\Students\Zhou_Harry\abaqus\working"

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

# Logging
logger.add(
    f"{new_dir}\\script.log",  # Log file name with timestamp
    format="{time} {level} {message}",  # Custom format
)

logger.info("Created new directories")

src = f"{template_directory}\\{template_file_name}.daf"
dst = f"{new_dir}\\Template.daf"

shutil.copy(src, dst)

logger.info(f"Copied Template daf file from {src} to {dst}")

# Generate the .daf files that will be used

num_generated = 0
total_generated = 0


actual_FOT = np.array([[ 0.79,-0.01,0.01],
                       [-0.01, 0.11,   0],
                       [ 0.01, 0   , 0.1]])
while num_generated < num_samples:
    daf_name= f"{new_daf_name}_{total_generated}"
    print(daf_name)
    rve.generate_single_daf(
        new_daf_name=daf_name,
        template_directory=new_dir,
        output_dir=digimat_in_dir,
    )

    logger.success("Created new daf files based off template")

    # RVE generation
    rve.create_rve(daf_file_path=digimat_in_dir,daf_name=daf_name,output_path=digimat_out_dir, log_path=new_dir)
    
    # Error handling during RVE generation
    digimat_log_filename = f"{digimat_out_dir}/logs/output-{daf_name}.txt"
    
    error_check = False
    with open(digimat_log_filename,"r") as f:
        for line in f:
            if line == "# DIGIMAT FE ERROR : Generation of matrix phase failed.":
                error_check = True
                break
            elif line == "Error: Meshing failed.  Please try using a smaller element size or a higher number of refinement steps.":
                error_check = True
                break
            
    if error_check == True:
        total_generated +=1
        continue
    
    #prints the fiber orientation tensor for the current RVE
    rve_FOT = afo.check_fiber_orientation_tensor(input_filename=daf_name, input_path=digimat_out_dir)
    print(rve_FOT)
    
    if num_generated == 0:
        FOT_list = np.array([rve_FOT,])
        
            #add fiber orientation
        afo.run(
        input_filename = f"{daf_name}",
        input_path=digimat_out_dir,
        output_path=abaqus_inp_dir,
        break_point="STEP",
        )
        
        change_extension.main(filename=f"{daf_name}.inp",path = abaqus_inp_dir, new_extension="inc")
        num_generated +=1
        
    else:
        current_FOT_list = np.append(FOT_list,rve_FOT[None,:,:],axis = 0)
        print(current_FOT_list)
         
        old_average_FOT = FOT_list.mean(axis=0)
        current_average_FOT = current_FOT_list.mean(axis=0)
        
        old_error = np.linalg.norm(old_average_FOT - actual_FOT, ord="fro")
        current_error = np.linalg.norm(current_average_FOT - actual_FOT, ord="fro")
        
        print(f"old tensor = {old_average_FOT}\nnew tensor = {current_average_FOT}\nold error = {old_error}, new error = {current_error}")
        
        if current_error < old_error:
            afo.run(
                input_filename = f"{daf_name}",
                input_path=digimat_out_dir,
                output_path=abaqus_inp_dir,
                break_point="STEP",
                )
        
            change_extension.main(filename=f"{daf_name}.inp",path = abaqus_inp_dir, new_extension="inc")
            FOT_list = current_FOT_list
            num_generated +=1
        
    total_generated += 1    
    
            

print(np.mean(FOT_list, axis=0))  

with open(f"{output_dir}\\description.txt", "w") as f:
    f.write(description)

logger.remove()

#shutil.move(f"{new_dir}", f"{output_dir}")
#  python -m digimat_scripts.scripts.digimat_to_abaqus_v2