import pathlib
import os


def main(filename: str, path: str, new_extension: str):
    p = pathlib.Path(f"{path}\\{filename}")
    return p.rename(p.with_suffix(f".{new_extension}"))


def batch(path: str, old_extension: str, new_extension: str):
    filenames = [f for f in os.listdir(path) if f.endswith(f".{old_extension}")]

    for name in filenames:
        main(filename=name, path=path, new_extension=new_extension)
