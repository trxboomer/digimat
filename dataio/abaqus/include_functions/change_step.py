import os


def add_step(
    input_file: str,
    input_path: str,
    step_names: list[str],
    step_path: str,
    output_path: str,
    no_step: bool = True,
):
    """Creates a input and adds a new step to it using the *Include keyword provided by Abaqus

    Args:
        input_file (str): Input file of interest, including extension name
        step_names (list[str]): list of .inc files that contains steps
    """

    for step_file in step_names:
        step_name = step_file[:-4]
        output_file_path = f"{output_path}\\{input_file[:-4]}-{step_name}.inp"
        
        with open(f"{step_path}\\{step_file}") as step:
            step_lines = step.readlines()
        with open(output_file_path, "a") as file:
            file.write(f"*INCLUDE, INPUT={input_file}\n")
            file.write(step_lines)
            
            
def main(input_path, step_path):
    input_files = [f for f in os.listdir(input_path) if f.endswith(".inc")]
    
    step_files = [f for f in step_path if f.endswith(".inp")]
    
    step_lines: dict = {}
    
    for file in step_files:
        f = open(f"{step_path}\\{file}","r")
        
        step_lines.update(file,step_lines)
        
    for input in input_files:
        
