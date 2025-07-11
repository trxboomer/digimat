# command to run this script from python is
# for lab pc:
# import os
# os.chdir(r"C:\MSC.Software\Digimat\working")
# exec(open('automatic_coupon_generation.py').read())

# for office pc:
# import os
# os.chdir(r"C:\MSC.Software\Digimat2018\Digimat\working")
# exec(open('automatic_coupon_generation.py').read())

import os
import math
from random import randint

# run digimat to get digimat generated .inps
# modify .daf file
# os.getcwd()

# adjust this
# pc="lab"
pc = "office"

batch_label = "_batch003_"  # adjust this
working_directory = r"C:\MSC.Software\Digimat\working"
digimat_path = r"C:\MSC.Software\Digimat\shortcuts\DigimatFE20181.bat"


def generate_daf_file(
    new_daf_name: str,
    num_samples: int,
    template_directory: str,
    output_dir: str,
    template_file_name: str = "Template",
):

    with open(f"{template_directory}/{template_file_name}.daf", "r") as in_file:
        template_daf_lines = in_file.readlines()

    fill_len = int(math.log10(num_samples)) + 1
    for i in range(num_samples):
        state_number = str(i).zfill(fill_len)
        name = f"{new_daf_name}_{state_number}"
        with open(f"{output_dir}/{name}.daf", "w") as out_file:
            for line in template_daf_lines:
                if line == "name = Template\n":
                    line = f"name = {name}\n"
                if line == "random_seed = 1\n":
                    line = f"random_seed = {str(randint(1**10, 9**10))}\n"
                out_file.write(line)


def run_daf_files(daf_file_path: str, output_path: str):

    filenames = [f for f in os.listdir(daf_file_path) if f.endswith(".daf")]
    for files in filenames:
        text = f"{digimat_path} -runFEWorkflow input={daf_file_path}\\{files} workingDir={output_path}"
        os.system(text)


if __name__ == "__main__":
    generate_daf_file(
        template_file_name="Template",
        new_daf_name="test",
        num_samples=5,
        template_directory=r"C:\Users\harryhz\Documents\digimat_scripts\digimat\Template",
        output_dir=r"C:\Users\harryhz\Documents\digimat_scripts\digimat\Template\test",
    )

    run_daf_files(
        daf_file_path=r"C:\Users\harryhz\Documents\digimat_scripts\digimat\Template\test",
        output_path=r"D:\digimat_test",
    )
