import numpy as np
import numpy.typing as npt


def spherical_to_cartesian(
    theta: np.float64, phi: np.float64, r: int = 1
) -> npt.NDArray[np.float64]:
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return np.array([x, y, z])


def perpendicular_vector(
    vector: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    if not np.allclose(vector[:2], 0):
        temp_vector = np.array([0, 0, 1])
    else:
        temp_vector = np.array([1, 0, 0])

    normal_vector = np.cross(vector, temp_vector)
    return normal_vector / np.linalg.norm(
        normal_vector
    )  # Optional: make it a unit vector
