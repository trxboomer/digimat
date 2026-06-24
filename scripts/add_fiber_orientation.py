from typing import Literal
from digimat_scripts.dataio.abaqus.edit_functions.TemplateEditFunction import (
    TemplateEditFunction,
)
from digimat_scripts.dataio.abaqus.read_input_file import AbaqusInputFile as rAbaqusIF
from digimat_scripts.dataio.abaqus.write_input_file import modify_file
from digimat_scripts.dataio.abaqus.edit_functions.add_orientation import add_orientation
from digimat_scripts.dataio.abaqus.edit_functions.change_material_property import (
    change_material_property,
)
from digimat_scripts.dataio.digimat.read_orientation import (
    DigimatPhaseOrientationFile as digimatPOF,
)
import os
import zipfile
from loguru import logger
import numpy as np
from digimat_scripts.math_util import vector_transformation as vt

"""
Notes:
Abaqus input file and digimat zipped outputs should all be in the same directory (input_path variable)

1. read the orientation file, and extract theta and phi data
2. convert that into rectangular coordinates
3. create object using add orientation class
4. Create Abaqus Input file object
5. Provide that orientation class object as a argument for the modify_file initialization
"""


@logger.catch
def run(
    input_filename: str,
    input_path: str,
    output_path: str,
    break_point: str,
    potential_phase_name: list[str] = ["Fiber"],
):
    abaqus_original = rAbaqusIF(filename=f"{input_filename}.inp", path=input_path)

    abaqus_original.cache_keywords(("Elset",))
    fiber_name = abaqus_original.get_phase_name(
        potential_phase_name=potential_phase_name, return_name=True
    )

    orientation_file_name = (
        f"DefaultJobName_{input_filename}_{fiber_name}_orientation.txt"
    )
    zip_path = f"{input_path}\\DefaultJobName_{input_filename}.zip"  # TODO: Add correct name for zip_file
    if not os.path.exists(zip_path):
        raise FileNotFoundError(
            f"Input file zip file could not be found, search for the following path: {zip_path}"
        )

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extract(orientation_file_name, input_path)

    orientation_file = digimatPOF(orientation_file_name, input_path, fiber_name)
    orientation = orientation_file.get_csv(columns=("theta", "phi"))

    orientation_function = add_orientation(
        phase_name=fiber_name, orientation_list=orientation
    )

    fiber_conductivity = change_material_property(
        material_name="Carbon_Fiber",
        property_name="Conductivity",
        new_isotropy="Orthotropic",
        new_values=(6.83e-3, 2.18e-3, 2.18e-3),
    )

    all_functions: list[TemplateEditFunction] = [
        orientation_function,
        fiber_conductivity,
    ]

    new_file = modify_file(
        input_filename=input_filename,
        open_input_file=abaqus_original.file,
        output_path=output_path,
        edit_functions=all_functions,
    )

    new_file.copy_and_edit(break_point)

def check_fiber_orientation_tensor(    
    input_filename: str,
    input_path: str,
    potential_phase_name: list[str] = ["Fiber"]):
    abaqus_original = rAbaqusIF(filename=f"{input_filename}.inp", path=input_path)

    abaqus_original.cache_keywords(("Elset",))
    fiber_name = abaqus_original.get_phase_name(
        potential_phase_name=potential_phase_name, return_name=True
    )
    
    orientation_file_name = (
        f"DefaultJobName_{input_filename}_{fiber_name}_orientation.txt"
    )
    abaqus_original = rAbaqusIF(filename=f"{input_filename}.inp", path=input_path)

    abaqus_original.cache_keywords(("Elset",))
    fiber_name = abaqus_original.get_phase_name(
        potential_phase_name=potential_phase_name, return_name=True
    )
    zip_path = f"{input_path}\\DefaultJobName_{input_filename}.zip"  # TODO: Add correct name for zip_file
    if not os.path.exists(zip_path):
        raise FileNotFoundError(
            f"Input file zip file could not be found, search for the following path: {zip_path}"
        )

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extract(orientation_file_name, input_path)

    orientation_file = digimatPOF(orientation_file_name, input_path, fiber_name)
    orientation = orientation_file.get_csv(columns=("theta", "phi"))
    orientation_list = []
    for row in orientation:
        orientation_list.append(vt.angle_to_tensor(theta=row[0],phi = row[1]))
        
    #print(orientation_list)
    
    arr = np.array(orientation_list)
    average_orientation = arr.mean(axis=0)
    
    return average_orientation

    
    
def batched_run(
    input_path: str,
    output_path: str,
    break_point: str,
    extension_type: Literal["inp", "inc"],
):
    filenames = [f for f in os.listdir(input_path) if f.endswith(f".{extension_type}")]

    for file in filenames:
        run(
            input_filename=file[:-4],
            input_path=input_path,
            output_path=output_path,
            break_point=break_point,
        )


if __name__ == "__main__":
    run(
        input_filename="test_0",
        input_path=r"D:\digimat_test",
        output_path=r"D:\digimat_test\modified",
    )
