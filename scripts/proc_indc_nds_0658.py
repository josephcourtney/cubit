import re
from numbers import Number
from pathlib import Path

import numpy as np
import pandas as pd

# data derived from NJ Stone, TABLE OF NUCLEAR MAGNETIC DIPOLE AND ELECTRIC QUADRUPOLE MOMENTS,
#     INDC International Nuclear Data Committee, 2014
# downloaded from https://www-nds.iaea.org/publications/indc/indc-nds-0658.pmoment_data on 23/03/2023
# converted to xlsx with https://www.adobe.com/acrobat/online/pmoment_data-to-excel.html
# header and footer removed manually, typos addressed, and exported as csv producing indc-nds-0658.csv


def convert_spin(r):
    r = str(r)
    for e in ["(", ")", "[", "]"]:
        r = r.replace(e, "")
    if r in ["unknown", "I", "nan"]:
        return None
    if r[-1] == "+":
        r = r[:-1]
    elif r[-1] == "-":
        r = r[-1] + r[:-1]
    if m := re.fullmatch(r"-?(\d+)/(\d+)", r):
        return -int(m[1]) / int(m[2])
    if m := re.fullmatch(r"(\d+)/(\d+)", r):
        return int(m[1]) / int(m[2])
    return int(r) if (m := re.fullmatch(r"-?(\d+)", r)) else repr(r)


def convert_half_life(r):
    if r == "stable":
        return np.inf
    if m := re.fullmatch(r"(\d+(?:\.\d+)?)\s?(\w+)", r):
        unit = m[2]
        multiplier = {
            "fs": 1e-15,
            "ps": 1e-12,
            "ns": 1e-9,
            "us": 1e-6,
            "ms": 1e-3,
            "s": 1,
            "m": 60,
            "min": 60,
            "h": 60 * 60,
            "d": 24 * 60 * 60,
            "y": 365.25 * 24 * 60 * 60,
        }
        return multiplier[unit] * float(m[1])
    return r


def remove_error(r):
    if isinstance(r, Number):
        return float(r)
    if m := re.fullmatch(r"\+?(-?\d+(?:\.\d+)?)(?:\(.*\))?", r):
        return float(m[1])
    return r


path_in = Path(__file__).parent / "indc-nds-0658.csv"
moment_data = pd.read_csv(path_in.resolve())
moment_data = moment_data.dropna(axis="columns", how="all")
moment_data["energy_level"] = moment_data["energy_level"].fillna(0.0)
moment_data[
    [
        "nucleus",
        "half_life",
        "spin",
        "magnetic_dipole_moment",
        "electric_quadrupole_moment",
    ]
] = moment_data[
    [
        "nucleus",
        "half_life",
        "spin",
        "magnetic_dipole_moment",
        "electric_quadrupole_moment",
    ]
].fillna(
    method="ffill",
)
moment_data = moment_data.dropna(subset="Recommended")
moment_data = moment_data.drop(columns="Recommended")

moment_data["Z"] = moment_data["nucleus"].apply(lambda x: x.split()[0])
moment_data["symbol"] = moment_data["nucleus"].apply(lambda x: x.split()[1])
moment_data["A"] = moment_data["nucleus"].apply(lambda x: x.split()[2])
moment_data = moment_data.drop(columns="nucleus")

moment_data["spin"] = moment_data["spin"].apply(convert_spin)
moment_data["half_life"] = moment_data["half_life"].apply(convert_half_life)
moment_data["magnetic_dipole_moment"] = (
    moment_data["magnetic_dipole_moment"].str.removesuffix("d").str.strip()
)

moment_data["magnetic_dipole_moment"] = moment_data["magnetic_dipole_moment"].apply(
    remove_error,
)

moment_data["electric_quadrupole_moment"] = (
    moment_data["electric_quadrupole_moment"].str.removesuffix("a").str.strip()
)
moment_data["electric_quadrupole_moment"] = (
    moment_data["electric_quadrupole_moment"].str.removesuffix("st").str.strip()
)
moment_data["electric_quadrupole_moment"] = moment_data["electric_quadrupole_moment"].apply(remove_error)

moment_data["magnetic_dipole_moment"] = pd.to_numeric(
    moment_data["magnetic_dipole_moment"],
)
moment_data["electric_quadrupole_moment"] = pd.to_numeric(
    moment_data["electric_quadrupole_moment"],
)

moment_data["magnetic_dipole_moment"] = (
    moment_data["magnetic_dipole_moment"] * 5.050783699e-27
)  # convert from nuclear magnetons to J/T
moment_data["electric_quadrupole_moment"] = (
    moment_data["electric_quadrupole_moment"] * 1.602176487e-19 * 1e-28
)  # convert to C*m^2

moment_data = moment_data[
    [
        "symbol",
        "Z",
        "A",
        "energy_level",
        "half_life",
        "spin",
        "magnetic_dipole_moment",
        "electric_quadrupole_moment",
    ]
]

moment_data.columns = pd.Index(
    [
        "symbol",
        "Z",
        "A",
        "energy_level_keV",
        "half_life_s",
        "spin",
        "magnetic_dipole_moment_J_T",
        "electric_quadrupole_moment_Cm2",
    ],
)
path_out = Path(__file__).parent.parent / "data" / "nuclear_moments.csv"
moment_data.to_csv(path_out.resolve())
