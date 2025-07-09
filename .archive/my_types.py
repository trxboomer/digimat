from typing import Annotated, Literal, TypeVar
import numpy as np
import numpy.typing as npt

DType = TypeVar("DType", bound=np.generic)

Array3x3 = Annotated[npt.NDArray[DType], Literal[3, 3]]
ArrayNN = Annotated[npt.NDArray[DType], Literal["N", "N"]]
ArrayNNN = Annotated[npt.NDArray[DType], Literal["N", "N", "N"]]
