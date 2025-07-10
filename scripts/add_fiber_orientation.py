import pstats
from dataio.TemplateAbaqusEditFunction import TemplateEditFunction
from dataio.read_abaqus_input_file import AbaqusInputFile as rAbaqusIF
from dataio.write_abaqus_input_file import modify_file
from dataio.abaqus_edit_functions import add_orientation, change_material_property
from dataio.read_digimat_orientation import DigimatPhaseOrientationFile as digimatPOF
import os
import zipfile
from loguru import logger
import cProfile

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
def main(
    input_filename: str,
    input_path: str,
    output_path: str,
    potential_phase_name: list[str] = ["Fiber"],
):
    abaqus_original = rAbaqusIF(filename=f"{input_filename}.inp", path=input_path)

    abaqus_original.cache_keywords(("Elset",))
    fiber_name = abaqus_original.get_phase_name(
        potential_phase_name=potential_phase_name, return_name=True
    )

    orientation_file_name = f"{input_filename}_{fiber_name}_orientation.txt"
    zip_path = (
        f"{input_path}/{input_filename}.zip"  # TODO: Add correct name for zip_file
    )
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
    # TODO: Check material properties
    fiber_conductivity = change_material_property(
        material_name="Carbon_Fiber",
        property_name="Conductivity",
        new_isotropy="Orthotropic",
        new_values=(1, 1, 1),
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

    new_file.copy_and_edit()


if __name__ == "__main__":
    main(
        input_filename="Template",
        input_path="/home/harry/Documents/digimat/Template",
        output_path="/home/harry/Documents/digimat/Validation/modified",
    )
