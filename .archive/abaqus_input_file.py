import os
from typing import NotRequired, TypedDict
import numpy as np
import numpy.typing as npt
import linecache as lc
import my_types as mt, fibers, orientation
import re
from loguru import logger
import sys


class InputFileError(Exception):
    """Custom exception for errors in the InputFile class."""

    def __init__(self, message: str):
        super().__init__(message)


class keyword_info(TypedDict):
    start_line: int
    # Not required for *Surface, *NODE, *Element, *Orientation, *SolidSection
    generate: NotRequired[bool]


class cache_type(TypedDict):
    Surface: dict[str, keyword_info]
    Elset: dict[str, keyword_info]
    Nset: dict[str, keyword_info]
    NODE: dict[str, keyword_info]
    Element: dict[str, keyword_info]
    Orientation: dict[str, keyword_info]
    SolidSection: dict[str, keyword_info]


class grouped_fibers_type(TypedDict):
    fibers: list[fibers.FiberData]
    nodes: np.ndarray  # Combined fiber nodes


class surface_nest_type(TypedDict):
    xinfall: NotRequired[np.ndarray]
    yinfall: NotRequired[np.ndarray]
    zinfall: NotRequired[np.ndarray]
    xsupall: NotRequired[np.ndarray]
    ysupall: NotRequired[np.ndarray]
    zsupall: NotRequired[np.ndarray]
    all: NotRequired[np.ndarray]


class AbaqusInputFile:
    keywords = (
        "*Surface",
        "*Elset",
        "*Nset",
        "*NODE",
        "*Element",
        "*Orientation",
        "*SolidSection",
    )
    surface_keywords = [
        "xinfall",
        "yinfall",
        "zinfall",
        "xsupall",
        "ysupall",
        "zsupall",
    ]
    reference_surface = ["xinfall", "yinfall", "zinfall"]
    opposite_surfaces = {
        "xinfall": "xsupall",
        "yinfall": "ysupall",
        "zinfall": "zsupall",
        "xsupall": "xinfall",
        "ysupall": "yinfall",
        "zsupall": "zinfall",
    }

    def __init__(
        self,
        filename: str,
        path: str,
        fiber_name_list: list[str],
        matrix_name_list: list[str],
    ) -> None:

        self.isValid: bool = True
        self.error_messages: list[str] = []
        self.filename = filename
        self.file_path: str = path + filename

        if not os.path.isfile(self.file_path):
            self.error(f"Could not find file: {self.filename}")

        self.file = open(self.file_path, "r")

        self.cache: cache_type = self.cache_file()
        self.all_nodes_start: int = self.cache["NODE"]["ALL_NODES"]["start_line"]
        self.all_elements_start: int = self.cache["Element"]["ALL_ELEMENTS"][
            "start_line"
        ]

        if self.check_element_type():
            self.error(f"Element type for {self.filename} is not valid for this script")

        self.surf_nset: surface_nest_type = self.get_model_surface()
        self.model_center = self.get_model_center()
        self.dimensions = self.get_model_dimensions()

        self.fiber_name: str = self.get_fiber_name(fiber_name_list)
        self.fiber_list: dict[str, fibers.FiberData] = {}
        self.get_all_fibers()
        self.intersect_fibers: dict[str, list[fibers.FiberData]] = {
            surface: [] for surface in self.surface_keywords
        }
        self.intersect_fibers.update({"all": []})
        self.grouped_fibers: list[grouped_fibers_type] = []
        self.individual_fibers: list[fibers.FiberData] = []
        self.orientation_ID = -1

    def error(self, message: str):
        self.error_messages.append(message)
        self.isValid = False

    @staticmethod
    def append_new_values(
        current_values: np.ndarray | list[int | np.float64],
        possible_values: np.ndarray | list[int | np.float64],
    ) -> np.ndarray:
        return np.append(current_values, np.setdiff1d(possible_values, current_values))

    @staticmethod
    def line_to_list(line: "str") -> list["str"]:
        line = re.sub(r"\s+", "", line, flags=re.UNICODE)
        param_list = line.split(",")

        return param_list

    @staticmethod
    def organize_key(
        param_list: list[str], line_no: int
    ) -> dict[str, dict[str, int | bool]] | None:
        keyword: str = param_list[0]
        if keyword == "*Surface":
            name = param_list[2].split("=")[1]
            return {name: {"start_line": line_no}}

        if keyword in ["*Elset", "*Nset"]:
            name = param_list[1].split("=")[1]
            generate = False
            if "generate" in param_list:
                generate = True
            return {name: {"start_line": line_no, "generate": generate}}

        if keyword == "*NODE":
            name = param_list[1].split("=")[1]
            return {name: {"start_line": line_no}}

        if keyword == "*Element":
            name = param_list[2].split("=")[1]
            return {name: {"start_line": line_no}}

        if keyword == "*Orientation":
            name = param_list[1].split("=")[1]
            return {name: {"start_line": line_no}}

        if keyword == "*SolidSection":
            name = param_list[1].split("=")[1]
            return {name: {"start_line": line_no}}

        else:
            logger.warning(
                "Key could not be organized, ensure that the key is correctly spelt, and that it is listed above"
            )
        return None

    @staticmethod
    def get_face_nodes(nodes: np.ndarray, face_type: str) -> np.ndarray:
        # Only works for DC3D4

        face_num = int(face_type[1:])

        if face_num == 1:
            return np.delete(nodes, 3)

        elif face_num == 2:
            return np.delete(nodes, 2)

        elif face_num == 3:
            return np.delete(nodes, 0)

        elif face_num == 4:
            return np.delete(nodes, 1)

        return nodes

    def check_element_type(self):
        element_params = self.line_to_list(
            line=lc.getline(self.file_path, lineno=self.all_elements_start)
        )

        element_type = element_params[1].split("=")[1]

        if element_type != "DC3D4":

            return True

    def get_model_center(self) -> tuple[np.float64, np.float64, np.float64]:
        # Flatten all surface node lists and remove duplicates
        surface_nset: np.ndarray = self.surf_nset["all"]

        surface_nodes = self.get_nodes(surface_nset)

        x_coords, y_coords, z_coords = zip(*surface_nodes)
        center = tuple(
            (min(coords) + max(coords)) / 2 for coords in (x_coords, y_coords, z_coords)
        )
        return center

    def get_model_dimensions(self):
        surface_nset = self.surf_nset["all"]

        surface_nodes = self.get_nodes(surface_nset)

        x_coords, y_coords, z_coords = zip(*surface_nodes)
        dimensions = tuple(
            (max(coords) - min(coords)) for coords in (x_coords, y_coords, z_coords)
        )
        return dimensions

    def read_lines(self, start_line: int, break_point: str) -> list["str"]:
        line_no = start_line

        content: list[str] = []
        while True:
            line = lc.getline(self.file_path, line_no)
            if break_point in line:
                break

            content.append(line)
            line_no += 1

        return content

    def get_set(self, info: keyword_info) -> npt.NDArray[np.int64]:
        start_line = info["start_line"] + 1
        if info.get("generate", True):
            elements_range = lc.getline(self.file_path, lineno=start_line)

            elements_range = list(map(int, elements_range.split(",")))
            return np.arange(
                elements_range[0], elements_range[1] + 1, elements_range[2]
            )

        else:
            temp_list: list[int] = []
            temp = self.read_lines(start_line, "*")

            # temp = [x.split(",") for x in temp]
            for x in temp:
                x = self.line_to_list(x)
                x = list(map(int, x))

                temp_list.extend(x)

            return np.array(temp_list)

    def get_nodes(self, nset: np.ndarray) -> np.ndarray:
        temp_node: list[list[np.float64]] = []
        for temp in nset:
            line_no = self.all_nodes_start + temp
            line = lc.getline(self.file_path, line_no)
            line = line[:-1].split(",")
            line = list(map(np.float64, line[1:]))
            temp_node.append(line)
        return np.array(temp_node)

    def cache_file(self) -> cache_type:
        self.file.seek(0)

        cache: cache_type = {
            "Element": {},
            "Surface": {},
            "Elset": {},
            "Nset": {},
            "NODE": {},
            "Orientation": {},
            "SolidSection": {},
        }
        # logger.debug(f"Initialized cache format {cache}")
        for idx, line in enumerate(self.file):
            if line[0] != "*":
                continue

            param_list = self.line_to_list(line)

            if param_list[0] in self.keywords:

                new_item = self.organize_key(param_list, line_no=idx + 1)
                if new_item is None:
                    continue
                cache[param_list[0][1:]].update(new_item)  # type: ignore
        return cache

    def get_model_surface(self) -> surface_nest_type:
        nset_cache = self.cache["Nset"]

        self.surf_nset: surface_nest_type = {
            "xinfall": np.array([], dtype=int),
            "yinfall": np.array([], dtype=int),
            "zinfall": np.array([], dtype=int),
            "xsupall": np.array([], dtype=int),
            "ysupall": np.array([], dtype=int),
            "zsupall": np.array([], dtype=int),
            "all": np.array([], dtype=int),
        }
        for surface in self.surface_keywords:
            surf_nset: np.ndarray = self.get_set(nset_cache[surface])

            self.surf_nset[surface] = surf_nset

            self.surf_nset["all"] = np.append(self.surf_nset["all"], surf_nset)

        self.surf_nset["all"] = np.unique(self.surf_nset["all"])
        return self.surf_nset

    def get_fiber_name(self, fiber_name_list: list[str]) -> str:
        for name in self.cache["Elset"]:
            if any(name in fiber_name for fiber_name in fiber_name_list):
                return name
        self.error(f"Fiber name not found in fiber name list.")
        return "Unknown Name"

    def get_all_fibers(self):
        for name in self.cache["Elset"]:
            name_len = len(self.fiber_name) + 1
            if f"{self.fiber_name}_" in name[:name_len]:
                self.fiber_list.update({name: fibers.FiberData(name=name)})

    def get_fiber_elset(self):
        elset_cache = self.cache["Elset"]

        for fiber in self.fiber_list.values():
            fiber.elset = self.get_set(elset_cache[fiber.name])

    def get_fiber_surface_elset(self):
        surface_cache = self.cache["Surface"]
        elset_cache = self.cache["Elset"]

        for fiber in self.fiber_list.values():
            info = surface_cache[f"Surf-{fiber.name}"]

            element_lists = self.read_lines(
                start_line=info["start_line"] + 1,
                break_point="*",
            )
            elements: list[tuple[int, str]] = []
            for element_set in element_lists:
                elset_params = self.line_to_list(element_set)
                # logger.debug(f"Elset param: {elset_params}")
                elset_info = elset_cache[elset_params[0]]
                elset = self.get_set(info=elset_info)
                # logger.debug(f"Fiber surface elset: {elset}")
                elements.extend([(element, elset_params[1]) for element in elset])

            fiber.surface_elset = np.array(elements)

    def get_fiber_nset(self) -> None:
        for fiber in self.fiber_list.values():
            temp_fiber_nodes = np.array([], dtype=int)
            for element in fiber.elset:
                line = lc.getline(
                    filename=self.file_path, lineno=self.all_elements_start + element
                )
                line = list(map(int, line.split(",")))

                temp_fiber_nodes = np.append(
                    temp_fiber_nodes, self.append_new_values(temp_fiber_nodes, line[1:])
                )
            fiber.nset = np.sort(temp_fiber_nodes.astype("int64"))

    def get_fiber_surface_nset(self) -> None:
        for fiber in self.fiber_list.values():
            temp_fiber_nodes: np.ndarray = []

            for element in fiber.surface_elset:
                line = self.line_to_list(
                    lc.getline(
                        filename=self.file_path,
                        lineno=self.all_elements_start + int(element[0]),
                    )
                )

                nodes = np.array(list(map(np.int64, line[1:])))
                face_nodes = self.get_face_nodes(nodes, face_type=element[1])
                temp_fiber_nodes = self.append_new_values(temp_fiber_nodes, face_nodes)

            fiber.surface_nset = np.sort(temp_fiber_nodes.astype("int64"))

    def get_fiber_nodes(self):
        for fiber in self.fiber_list.values():
            fiber.nodes = self.get_nodes(fiber.nset)

    def get_fiber_surface_nodes(self):
        for fiber in self.fiber_list.values():
            fiber.surface_nodes = self.get_nodes(fiber.surface_nset)

    def get_intersect_center(
        self, intersect_nset: npt.NDArray[np.int64]
    ) -> npt.NDArray[np.int64]:
        intersect_nodes = self.get_nodes(nset=intersect_nset)
        x_coords, y_coords, z_coords = zip(*intersect_nodes)
        center = np.array(
            [
                (min(coords) + max(coords)) / 2
                for coords in (x_coords, y_coords, z_coords)
            ]
        )
        return center

    def check_fiber_intersect(self):
        intersect_nodes: np.ndarray
        for fiber in self.fiber_list.values():
            for surface, surf_nset in self.surf_nset.items():
                intersect_nodes = np.intersect1d(
                    np.asarray(fiber.nset), np.asarray(surf_nset), assume_unique=True
                )

                if any(intersect_nodes):
                    fiber.intersect_nset.update(
                        {
                            surface: {
                                "nset": intersect_nodes,
                                "center": self.get_intersect_center(intersect_nodes),
                            }
                        }
                    )

                    self.update_intersect_dict(fiber)

    def update_intersect_dict(self, fiber):
        for intersecting_surface in fiber.intersect_nset:
            self.intersect_fibers[intersecting_surface].append(fiber)
            if (
                fiber.name
                not in {obj.name: obj for obj in self.intersect_fibers["all"]}.values()
            ):
                self.intersect_fibers["all"].append(fiber)

    def calculate_opposite_center(
        self, reference_center: np.ndarray[np.float64], surface: "str"
    ):
        axes = ["x", "y", "z"]
        transform_axis = axes.index(surface[0])
        opposite_center = reference_center
        opposite_center[transform_axis] = reference_center[transform_axis] * -1
        opposite_center += self.model_center
        return opposite_center

    def get_fiber_pairs(self):

        fiber_list = self.intersect_fibers["all"]

        print(len(fiber_list))
        fiber_num_list = np.array(
            [int(fiber.name.split("_")[1]) for fiber in self.intersect_fibers["all"]]
        )
        fiber_num_list = np.sort(fiber_num_list)
        n = 0
        while n < len(fiber_list):
            fiber_num = fiber_num_list[n]
            fiber = self.fiber_list[f"{self.fiber_name}_{fiber_num}"]
            num_pairs = len(fiber.intersect_nset.values())

            paired = [fiber]

            fiber_num = int(fiber.name.split("_")[1])
            for num in range(num_pairs):
                paired.append(self.fiber_list[f"{self.fiber_name}_{fiber_num+num+1}"])
                n += 1
            self.grouped_fibers.append({"fibers": paired})
            n += 1

    def combine_grouped_fibers(self):
        def mirror_fiber(nodes, axis_OI, difference):
            mirrored_nodes = nodes.copy()  # Make a copy to avoid changing the original
            mirrored_nodes[:, axis_OI] = mirrored_nodes[:, axis_OI] + difference
            return mirrored_nodes

        logger.debug("Combining grouped fibers...")
        for group in self.grouped_fibers:

            fiber = group["fibers"][0]
            base_surface = fiber.intersect_nset.keys()
            combined_fiber_nodes = list(fiber.surface_nodes.copy())

            for surface in base_surface:
                opposite_surface = self.opposite_surfaces[surface]

                fibers_on_surface = [
                    f
                    for f in group["fibers"]
                    if opposite_surface in f.intersect_nset.keys()
                ]

                if not fibers_on_surface:
                    logger.warning(
                        f"Could not find fiber for opposite surface after grouping fibers {fiber.name}"
                    )

                else:
                    opposite_fiber = fibers_on_surface[0]

                axis_OI = next(
                    (
                        i
                        for i, s in enumerate(self.reference_surface)
                        if s.startswith(surface[0])
                    ),
                    -1,
                )
                fiber_intersect_node = fiber.intersect_nset[surface]["center"]
                opposite_intersect_node = opposite_fiber.intersect_nset[
                    opposite_surface
                ]["center"]
                surface_diff = (
                    fiber_intersect_node[axis_OI] - opposite_intersect_node[axis_OI]
                )

                transformed_fibers = mirror_fiber(
                    opposite_fiber.surface_nodes, axis_OI, surface_diff
                )
                combined_fiber_nodes.extend(transformed_fibers)

            combined_fiber_nodes = np.unique(combined_fiber_nodes, axis=0)
            group.update({"nodes": (np.array(combined_fiber_nodes))})

    def next_orientation_ID(self, material_name: str):
        self.orientation_ID += 1
        return f"Ori-{material_name}-{self.orientation_ID}"

    def fiber_orientation_from_file(self, fiber_name: str):
        start_line = self.cache["SolidSection"][fiber_name]["start_line"]

        orientation_name = self.line_to_list(
            lc.getline(filename=self.file_path, lineno=start_line)
        )
        orientation_name = orientation_name[3].split("=")[1]

        orientation_start_line = self.cache["Orientation"][orientation_name][
            "start_line"
        ]

        orientation = self.line_to_list(
            lc.getline(filename=self.file_path, lineno=orientation_start_line + 1)
        )

        return np.array(list(map(np.float64, (axis for axis in orientation))))

    def compare_fiber_orientation(self):
        def magnitude(vec: np.ndarray) -> np.floating:
            return np.linalg.norm(vec)

        # Use angle between vectors as difference
        def angle_diff(u: np.ndarray, v: np.ndarray) -> np.floating:
            cos_angle = np.clip(np.dot(u, v), -1.0, 1.0)
            return np.arccos(cos_angle)  # in radians

        def orientation_tensor(orientations: np.ndarray) -> np.ndarray:
            a_ij = np.zeros((3, 3))
            for p in orientations:
                a_ij += np.outer(p, p)
            a_ij /= len(orientations)

            return a_ij

        difference_list = []
        estimate_list = []
        actual_list = []
        magnitudes = []
        epsilon = 1e-8

        for fiber in self.fiber_list.values():
            fiber.actual_orientation = self.fiber_orientation_from_file(fiber.name)
            actual: np.ndarray = fiber.actual_orientation[:3]
            estimate: np.ndarray = fiber.orientation.rectangle_system[0]

            mag_actual = magnitude(actual)
            mag_estimate = magnitude(estimate)
            if mag_actual < epsilon or mag_estimate < epsilon:
                logger.warning(f"Zero magnitude for fiber {fiber.name}")
                continue

            unit_vec_actual = actual / mag_actual
            unit_vec_estimate = estimate / mag_estimate

            neg_unit_vec_estimate = -unit_vec_estimate

            diff = angle_diff(unit_vec_actual, unit_vec_estimate)
            neg_diff = angle_diff(unit_vec_actual, neg_unit_vec_estimate)

            if diff < neg_diff:
                actual_difference = diff
                estimate_list.append(unit_vec_estimate)
            else:
                actual_difference = neg_diff
                estimate_list.append(neg_unit_vec_estimate)

            actual_list.append(unit_vec_actual)
            difference_list.append(actual_difference)
            magnitudes.append(actual_difference)
            fiber.orientation_diff = np.rad2deg(actual_difference)

        mean_diff = np.mean(difference_list)
        logger.debug(
            f"Average Orientation Difference (degrees): {np.rad2deg(mean_diff)}"
        )
        logger.debug(
            f"Max Orientation Difference (degrees): {np.rad2deg(np.max(difference_list))}"
        )
        logger.debug(
            f"Min Orientation Difference (degrees): {np.rad2deg(np.min(difference_list))}"
        )
        logger.debug(
            f"Estimated Orientation Tensor:\n{orientation_tensor(estimate_list)}"
        )
        logger.debug(f"Actual Orientation Tensor:\n{orientation_tensor(actual_list)}")

    def fiber_orientation(self, debug: bool = False):
        self.get_all_fibers()
        self.get_fiber_surface_elset()
        self.get_fiber_surface_nset()
        self.get_fiber_surface_nodes()
        self.get_fiber_elset()
        self.get_fiber_nset()
        self.check_fiber_intersect()
        self.get_fiber_pairs()
        self.combine_grouped_fibers()

        if any(self.intersect_fibers["all"]):

            self.individual_fibers = [
                fiber
                for fiber in self.fiber_list.values()
                if not any(fiber.name == f.name for f in self.intersect_fibers["all"])
            ]

        else:
            self.individual_fibers = self.fiber_list.values()

        for fiber in self.individual_fibers:
            fiber.orientation = orientation.fiber_orientation(
                self.next_orientation_ID(self.fiber_name), fiber.surface_nodes
            )
        if self.grouped_fibers:
            for group in self.grouped_fibers:
                group_orientation = orientation.fiber_orientation(
                    self.next_orientation_ID(self.fiber_name), group["nodes"]
                )
                for fiber in group["fibers"]:
                    fiber.orientation = group_orientation

        if debug:
            self.compare_fiber_orientation()

    def pretty(self, d, f, indent=0):
        for key, value in d.items():
            f.write("\t" * indent + str(key) + "\n")
            if isinstance(value, dict):
                self.pretty(value, indent + 1)
            else:
                f.write("\t" * (indent + 1) + str(value) + "\n")

    def debug_file(self, out_dest):
        with open(f"{out_dest}/{self.filename[:-4]}-DEBUG.txt", "w") as f:
            f.write("Intersecting Fibers\n")
            for surface, fibers in self.intersect_fibers.items():
                f.write(f"{surface}\n")
                for fiber in fibers:
                    f.write(f"{fiber.name}\n")

            f.write("GROUPED FIBERS\n")

            for group in self.grouped_fibers:
                f.write("New group\n")
                for fiber in group["fibers"]:
                    f.write(f"{fiber.name}\n")

            f.write("INDIVIDUAL FIBERS\n")
            for fiber in self.individual_fibers:
                f.write(f"{fiber.name}\n")

            f.write("FIBER ORIENTATION\n")

            for fiber in self.fiber_list.values():
                f.write(f"{fiber.name}\n")
                f.write(f"Actual Orientation: {fiber.actual_orientation[:3]}\n")
                f.write(
                    f"Estimated Orientation: {fiber.orientation.rectangle_system[0]}\n"
                )
                f.write(f"Difference: {fiber.orientation_diff}\n")

            f.write("Surface Nodes\n")
            for surface, nset in self.surf_nset.items():
                f.write(f"{surface}\n")
                f.write(f"{nset}\n")

    def debug_logs(self):
        # Debug
        grouped_orientation = []
        individual_orientation = []
        for group in self.grouped_fibers:
            for fiber in group["fibers"]:
                grouped_orientation.append(fiber.orientation_diff)

        for fiber in self.individual_fibers:
            individual_orientation.append(fiber.orientation_diff)

        logger.debug(
            f"Grouped fiber average orientation difference {np.average(grouped_orientation)}"
        )
        logger.debug(
            f"Individual fiber average orientation difference: {np.average(individual_orientation)}"
        )
