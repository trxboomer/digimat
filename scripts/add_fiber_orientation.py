from dataio.read_abaqus_input_file import AbaqusInputFile as rAbaqusIF
from dataio.write_abaqus_input_file import modify_file
from dataio.abaqus_edit_functions import add_orientation
from dataio.read_digimat_orientation import DigimatPhaseOrientationFile as digimatPOF


def main(
    input_filename: str,
    input_path: str,
    output_path: str,
    potential_phase_name: list[str] = ["Fiber"],
):
    original_file = rAbaqusIF(filename=filename, path=path)
    fiber_name = original_file.get_phase_name(
        potential_phase_name=potential_phase_name, return_name=True
    )
    fiber_orientation = digimatPOF()
    modify_file(
        output_path=output_path,
        edit_functions=add_orientation(
            phase_name=fiber_name, orientation_list=orientation_list
        ),
    )
