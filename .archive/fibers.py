from dataclasses import dataclass, field
from typing import NotRequired, TypedDict, Optional, Dict
from numpy import typing as npt
import numpy as np
from abaqus_input_file import surface_nest_type


@dataclass
class incomplete_fiber:
    tie_nodes: int
    intersect_nodes: list[int]


class surface_intersect(TypedDict):
    nset: np.ndarray
    center: npt.NDArray[np.float64]


class intersect_nset_type(TypedDict):
    surface: NotRequired[surface_intersect]


@dataclass
class FiberData:
    name: str
    elset: Optional[np.ndarray] = None
    surface_elset: Optional[np.ndarray] = None
    nset: Optional[np.ndarray] = None
    nodes: Optional[np.ndarray] = None
    surface_nset: Optional[np.ndarray] = None
    surface_nodes: Optional[np.ndarray] = None
    intersect_nset: surface_nest_type = field(default_factory=surface_nest_type)
    orientation: Optional[np.ndarray] = None
    orientation_ID: Optional[str] = None
    actual_orientation: Optional[np.ndarray] = None
    orientation_diff: Optional[np.ndarray] = None
