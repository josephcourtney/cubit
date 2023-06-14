import importlib.resources
import itertools
import math
from dataclasses import dataclass

import pandas as pd

from .units import (
    ampere,
    coulomb,
    dalton,
    joule,
    kelvin,
    kilogram,
    meter,
    mole,
    second,
    tesla,
)

EPS = 1e-10

# Physical constants
C = 299792458.0 * meter / second
PLANCK_CONSTANT = 6.62606896e-34 * joule * second
HBAR = PLANCK_CONSTANT / (2 * math.pi)
MU0 = 4 * math.pi * 1e-7 * kilogram * meter / second**2 / ampere**2  # N A^-2
EPSILON0 = 1.0 / (MU0 * C**2)  # F m^-1
ELEMENTARY_CHARGE = 1.602176487e-19 * coulomb  # C
COULOMB_CONSTANT = 1.0 / (4 * math.pi * EPSILON0)  # N m^2 C^-2
ELECTRON_MASS = 9.1093835611e-31 * kilogram  # kg
PROTON_MASS = 1.67262189821e-27 * kilogram  # kg
NEUTRON_MASS = 1.67492747121e-27 * kilogram  # kg
BOHR_MAGNETON = ELEMENTARY_CHARGE * HBAR / (2 * ELECTRON_MASS)
NUCLEAR_MAGNETON = ELEMENTARY_CHARGE * HBAR / (2 * PROTON_MASS)
AMU = 1.66053904020e-27 * kilogram  # kg
AVOGADROS_CONSTANT = 1e3 / AMU * mole  # mol^-1
BOLTZMANN_K = 1.3806485279e-23 * joule / kelvin  # J K^-1
ALPHA = ELEMENTARY_CHARGE**2 / (4.0 * math.pi * EPSILON0 * HBAR * C)
BOHR_RADIUS = HBAR / (ELECTRON_MASS * C * ALPHA)

_nuclear_moment_path = (
    importlib.resources.files(__package__)
    / ".."
    / ".."
    / "data"
    / "nuclear_moments.csv"
)

_isotopes_path = (
    importlib.resources.files(__package__) / ".." / ".." / "data" / "isotopes.csv"
)

_isotope_quadrupolar_moment = None
_isotope_spin = None
_isotope_nuclear_g_factor = None
_isotope_gyromagnetic_ratio = None

_element_atomic_number = None
_element_name = None
_monoisotopic_mass = None
_isotope_natural_abundance = None


def import_moment_data():
    with importlib.resources.as_file(_nuclear_moment_path) as _path:
        _nuclear_moment_df = pd.read_csv(_path.resolve(), index_col=False)

        _isotope_quadrupolar_moment = {
            (r["symbol"], r["A"]): r["electric_quadrupole_moment_Cm2"]
            * coulomb
            * meter**2
            for i, r in _nuclear_moment_df.iterrows()
        }

        _isotope_spin = {
            (r["symbol"], r["A"]): r["spin"] for i, r in _nuclear_moment_df.iterrows()
        }

        _isotope_nuclear_g_factor = {
            (r["symbol"], r["A"]): -r["magnetic_dipole_moment_J_T"]
            * (joule / tesla)
            / (r["spin"] * NUCLEAR_MAGNETON)
            for i, r in _nuclear_moment_df.iterrows()
        }

        _isotope_gyromagnetic_ratio = {
            (r["symbol"], r["A"]): (
                -(r["magnetic_dipole_moment_J_T"] * (joule / tesla) / r["spin"])
                / PLANCK_CONSTANT
            )
            for i, r in _nuclear_moment_df.iterrows()
        }
    return (
        _isotope_quadrupolar_moment,
        _isotope_spin,
        _isotope_nuclear_g_factor,
        _isotope_gyromagnetic_ratio,
    )


def import_isotope_data():
    with importlib.resources.as_file(_isotopes_path) as _path:
        _isotopes_df = pd.read_csv(_path.resolve(), index_col=False)

        _element_atomic_number = {
            r["symbol"]: r["Z"] for i, r in _isotopes_df.iterrows()
        }

        _element_name = {r["symbol"]: r["name"] for i, r in _isotopes_df.iterrows()}

        # data derived from
        # G.Audi, M.Wang, A.H.Wapstra, F.G.Kondev, M.MacCormick, X.Xu, and B.Pfeiffer.
        # The Ame 2012 atomic mass evaluation (I). Chinese Physics C36 p. 1287-1602, December 2012.
        _monoisotopic_mass = {
            (r["symbol"], r["A"]): r["monoisotopic_mass"] * dalton
            for i, r in _isotopes_df.iterrows()
        }

        _isotope_natural_abundance = {
            (r["symbol"], r["A"]): r["natural_abundance"]
            for i, r in _isotopes_df.iterrows()
        }
    return (
        _element_atomic_number,
        _element_name,
        _monoisotopic_mass,
        _isotope_natural_abundance,
    )


@dataclass
class Element:
    """Element."""

    symbol: str  # atomic symbol, e.g. H for hydrogen
    name: str  # full name of the element
    atomic_number: int  # atomic number Z, the number of protons in the nucleus

    def __hash__(self):
        return hash((self.symbol, self.name, self.atomic_number))


@dataclass
class Isotope:
    """Isotope."""

    element: Element
    mass_number: int
    monoisotopic_mass: float
    natural_abundance: float
    spin: float
    nuclear_g_factor: float
    gyromagnetic_ratio: float
    quadrupolar_moment: float

    @property
    def isotuple(self):
        """isotuple."""
        return (self.element.symbol, self.mass_number)

    def larmor_freq_given_1H(self, proton_frequency):  # noqa: N802
        """larmor_freq_given_1H.

        Parameters
        ----------
        proton_frequency :
            proton_frequency
        """
        return (
            proton_frequency
            * self.gyromagnetic_ratio
            / _isotope_gyromagnetic_ratio[("H", 1)]
        )

    def __hash__(self):
        return hash(
            (
                self.element,
                self.mass_number,
                self.monoisotopic_mass,
                self.natural_abundance,
                self.spin,
                self.nuclear_g_factor,
                self.gyromagnetic_ratio,
                self.quadrupolar_moment,
            ),
        )

    def __repr__(self):
        return f"<Isotope: {self.element.symbol}-{self.mass_number}>"

    def __str__(self):
        return repr(self)


ELEMENTS = {}
ISOTOPES = {}
_manual_pref_order = [
    ("H", 1),
    ("N", 15),
    ("C", 13),
    ("P", 31),
    ("F", 19),
]
_pref_order = []

gyromagnetic_ratio_ratios = {}


def nmr_active_isotopes(element: Element | str):
    """nmr_active_isotopes.
        return a list of Isotopes of a given element that are NMR active.

    Parameters
    ----------
    element : Element|str
        element for which to retrieve NMR-active isotopes

    """
    if isinstance(element, str):
        element = ELEMENTS[element]
    elif isinstance(element, Element):
        pass
    else:
        msg = (
            "element must be a string containing the element's atomic symbol or an Element object",
        )
        raise TypeError(msg)
    return [
        iso
        for (symbol, A), iso in ISOTOPES.items()
        if ELEMENTS[symbol] == element and iso.spin != 0
    ]


(
    _isotope_quadrupolar_moment,
    _isotope_spin,
    _isotope_nuclear_g_factor,
    _isotope_gyromagnetic_ratio,
) = import_moment_data()
(
    _element_atomic_number,
    _element_name,
    _monoisotopic_mass,
    _isotope_natural_abundance,
) = import_isotope_data()

import_moment_data()
import_isotope_data()

ELEMENTS = {
    symbol: Element(symbol, _element_name[symbol], z)
    for symbol, z in _element_atomic_number.items()
}
ISOTOPES = {
    (symbol, A): Isotope(
        element=ELEMENTS[symbol],
        mass_number=A,
        monoisotopic_mass=m,
        natural_abundance=_isotope_natural_abundance.get((symbol, A), 0.0) / 100.0,
        spin=_isotope_spin.get((symbol, A), 0.0),
        nuclear_g_factor=_isotope_nuclear_g_factor.get((symbol, A), 0.0),
        gyromagnetic_ratio=_isotope_gyromagnetic_ratio.get((symbol, A), 0.0),
        quadrupolar_moment=_isotope_quadrupolar_moment.get((symbol, A), 0.0),
    )
    for (symbol, A), m in _monoisotopic_mass.items()
}

_pref_order = _manual_pref_order + sorted(
    [iso for iso in _isotope_natural_abundance if iso not in _manual_pref_order],
    key=lambda iso: -_isotope_natural_abundance.get(iso, 0.0),
)
isotope_preference = {iso: i for i, iso in enumerate(_pref_order)}
for isotuple_0, isotuple_1 in itertools.combinations(
    _isotope_nuclear_g_factor.keys(),
    2,
):
    if not (
        isotuple_0 in _isotope_nuclear_g_factor
        and isotuple_1 in _isotope_nuclear_g_factor
    ):
        continue
    i_0 = ISOTOPES[isotuple_0]
    i_1 = ISOTOPES[isotuple_1]
    ng_0 = _isotope_nuclear_g_factor[isotuple_0]
    ng_1 = _isotope_nuclear_g_factor[isotuple_1]
    if abs(ng_0.value) > EPS and abs(ng_1.value) > EPS:
        gyromagnetic_ratio_ratios[(i_0, i_1)] = ng_0 / ng_1
        gyromagnetic_ratio_ratios[(i_1, i_0)] = ng_1 / ng_0
