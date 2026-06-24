from . import add_fiber_orientation as afo
from digimat_scripts.script_utils import change_extension
import numpy as np
import os

input_path = r"Y:\Students\Zhou_Harry\abaqus\working\Sensitivity Analysis\digimat_out"

FOT_list = []
filenames = [f for f in os.listdir(input_path) if f.endswith(f".inp")]
for file in filenames:
    print(file)
    FOT_list.append(afo.check_fiber_orientation_tensor(input_filename=file[:-4], input_path=input_path))
actual_FOT = np.array([[ 0.79,0,0],
                       [0, 0.11,   0],
                       [ 0, 0, 0.1]])

for orientation in FOT_list:
    print(orientation)
    print(np.linalg.norm(orientation - actual_FOT, ord="fro"))
average_FOT = np.array(FOT_list).mean(axis=0)
print(average_FOT)

print(np.linalg.norm(average_FOT - actual_FOT, ord="fro"))

afo.batched_run(
    input_path=input_path,   
    output_path=r"Y:\Students\Zhou_Harry\abaqus\working\Sensitivity Analysis\abaqus_inp",
    extension_type="inp",
    break_point="STEP",
)
change_extension.batch(path=r"Y:\Students\Zhou_Harry\abaqus\working\Sensitivity Analysis\abaqus_inp", old_extension="inp", new_extension="inc")