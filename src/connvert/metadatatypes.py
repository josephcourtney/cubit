from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt
import physical_data

Quadrature = Enum("Quadrature", ["REAL", "IMAGINARY"])
Domain = Enum("Domain", ["TIME", "FREQUENCY"])
ExperimentalCollectionMode = Enum("ExperimentalCollectionMode", ["COMPLEX", "REAL"])
ScheduleType = Enum("ScheduleType", ["UNIFORM", "NONUNIFORM"])
AveragingMode = Enum("AveragingMode", ["UNIQUE", "AVERAGED", "SUMMED_AND_COUNTED"])
DataContainerType = Enum("DataContainerType", ["SINGLE_FILE", "MULTI_FILE", "STREAM"])
ByteOrder = Enum("ByteOrder", ["BIG_ENDIAN", "LITTLE_ENDIAN"])
Units = Enum("Units", ["UNKNOWN", "S", "HZ", "PPM", "PT"])
DigitizationStrategy = Enum(
    "DigitizationStrategy",
    ["MAGNITUDE", "TPPI", "STATES", "IMAGE", "ARRAY"],
)


@dataclass
class DimInfo:
    """DimInfo."""

    first_scale_point: float
    nucleus: physical_data.Isotope
    sweep_width: float
    carrier: float
    collection_mode: ExperimentalCollectionMode
    size: int
    spectral_frequency: float
    analysis_domain: Domain
    dimension: int
    imaginaries_negation: bool
    sign_alternation: bool
    name: str
    phase_0: float
    phase_1: float

    def clone(self):
        """clone."""
        return deepcopy(self)


@dataclass
class Schedule:
    """Schedule."""

    schedule_type: ScheduleType
    n_indels: int
    extent: tuple[int]
    n_dim: int


@dataclass
class DataSet:
    """DataSet."""

    n_dim: int
    dim_info: list[DimInfo]
    values: npt.NDArray
    # collection_schedule


allowed_conversions = [
    (np.float32, np.float32),
    (np.int32, np.float32),
    (np.int32, np.int32),
    (np.int16, np.float32),
    (np.int16, np.int32),
    (np.int16, np.int16),
    (np.float64, np.float32),
]


@dataclass
class FileSpecification:
    """FileSpecification."""

    container_type: DataContainerType
    filename_pattern: str
    dtype: npt.DTypeLike
    byte_order: ByteOrder
    dimension_sequence: tuple  # order of dimensions, slowest to fastest
    meta_data_blocks: list  # list of regions containing metadata
