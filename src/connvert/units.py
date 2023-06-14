# %%
from enum import Enum
from numbers import Number
from typing import Optional, Self

from ._base import MultitonMeta

PI = 3.1415926535897932384626433832795028841971693993751058

PhysicalDimension = Enum(
    "PhysicalDimension",
    [
        "NONDIMENSIONAL",
        "LENGTH",
        "MASS",
        "TIME",
        "CURRENT",
        "TEMPERATURE",
        "AMOUNT_OF_SUBSTANCE",
        "LUMINOUS_INTENSITY",
        "ANGLE",
    ],
)


class Referent:
    def __init__(self, name: str):
        self.name = name


class UnitType:
    pass


class ScalingFactor(metaclass=MultitonMeta):
    def __init__(self, name, symbol, factor):
        self._name = name
        self._symbol = symbol
        self.display_factor = factor

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def factor(self):
        return self.display_factor

    def __repr__(self):
        return f"<{self.name}({self.symbol}) = {self.factor:1.0e}>"

    __str__ = __repr__

    def __mul__(self, other: Self) -> Self:
        if isinstance(other, ScalingFactor):
            return type(self)(
                "+".join((self.name, other.name)),
                "+".join((self.symbol, other.symbol)),
                self.factor * other.factor,
            )
        if isinstance(other, Number):
            return Quantity(other, self * one)
        return NotImplemented

    def __rmul__(self, other: Self) -> Self:
        return self.__mul__(other)

    def __truediv__(self, other: Self) -> Self:
        if isinstance(other, type(self)):
            return type(self)(
                "+".join((self.name, other.name)),
                "+".join((self.symbol, other.symbol)),
                self.factor / other.factor,
            )
        if isinstance(other, Number):
            return Quantity(1 / other, self * one)
        if issubclass(type(other), UnitType):
            return self * (other**-1)
        return NotImplemented

    def __rtruediv__(self, other: Self) -> Self:
        if isinstance(other, type(self)):
            return type(self)(
                "/".join((self.name, other.name)),
                "/".join((self.symbol, other.symbol)),
                other.factor / self.factor,
            )
        if isinstance(other, Number):
            return Quantity(other, one / self)
        if issubclass(type(other), UnitType):
            return other * (uni / self)
        return NotImplemented


# SI prefixes
quetta = ScalingFactor("quetta", "Q", 1e30)
ronna = ScalingFactor("ronna", "R", 1e27)
yotta = ScalingFactor("yotta", "Y", 1e24)
zetta = ScalingFactor("zetta", "Z", 1e21)
exa = ScalingFactor("exa", "E", 1e18)
peta = ScalingFactor("peta", "P", 1e15)
tera = ScalingFactor("tera", "T", 1e12)
giga = ScalingFactor("giga", "G", 1e9)
mega = ScalingFactor("mega", "M", 1e6)
kilo = ScalingFactor("kilo", "k", 1e3)
hecto = ScalingFactor("hecto", "h", 1e2)
deca = ScalingFactor("deca", "da", 1e1)
uni = ScalingFactor("", "", 1e0)
deci = ScalingFactor("deci", "d", 1e-1)
centi = ScalingFactor("centi", "c", 1e-2)
milli = ScalingFactor("milli", "m", 1e-3)
micro = ScalingFactor("micro", "μ", 1e-6)
nano = ScalingFactor("nano", "n", 1e-9)
pico = ScalingFactor("pico", "p", 1e-12)
femto = ScalingFactor("femto", "f", 1e-15)
atto = ScalingFactor("atto", "a", 1e-18)
zepto = ScalingFactor("zepto", "z", 1e-21)
yocto = ScalingFactor("yocto", "y", 1e-24)
ronto = ScalingFactor("ronto", "r", 1e-27)
quecto = ScalingFactor("quecto", "q", 1e-30)

# IEC prefixes
yobi = ScalingFactor("yobi", "Yi", 2**80)
zebi = ScalingFactor("zebi", "Zi", 2**70)
exbi = ScalingFactor("exbi", "Ei", 2**60)
pebi = ScalingFactor("pebi", "Pi", 2**50)
tebi = ScalingFactor("tebi", "Ti", 2**40)
gibi = ScalingFactor("gibi", "Gi", 2**30)
mebi = ScalingFactor("mebi", "Mi", 2**20)
kibi = ScalingFactor("kibi", "ki", 2**10)


class Quantity:
    def __init__(
        self,
        value: Number,
        unit: Optional[UnitType] = None,
    ):
        self.value = value
        if unit is None:
            self.unit = CompositeUnit(
                component_units=(Unit(PhysicalDimension.NONDIMENSIONAL, "", ""),),
                component_powers=(1,),
            )
        elif isinstance(unit, Unit):
            self.unit = CompositeUnit(component_units=(unit,), component_powers=(1,))
        elif isinstance(unit, CompositeUnit):
            self.unit = unit
        else:
            msg = (
                "unit can only be of type Unit or CompositeUnit. If unit is None,"
                + " it defaults to non-dimensinoal"
            )
            raise TypeError(msg)

    def __hash__(self):
        return hash((self.unit, self.value))

    def __repr__(self) -> str:
        return f"{self.value} {self.unit}"

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.value == other.value and self.unit == other.unit
        if isinstance(other, Number):
            return self.value == other.value and self.unit == one
        return False

    def __pow__(self, other):
        if isinstance(other, Number):
            return Quantity(self.value**other, self.unit**other)
        return NotImplemented

    def __neg__(self):
        return Quantity(-self.value, self.unit)

    def __pos__(self):
        return self.clone()

    def __sub__(self, other):
        if isinstance(other, type(self)):
            if self.unit != other.unit:
                msg = "Only quantities of the same type can be subtracted"
                raise TypeError(msg)
            return Quantity(self.value - other.value, self.unit)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, type(self)):
            if self.unit != other.unit:
                msg = "Only quantities of the same type can be added"
                raise TypeError(msg)
            return Quantity(self.value + other.value, self.unit)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, type(self)):
            return Quantity(self.value * other.value, self.unit * other.unit)
        if isinstance(other, Number):
            return Quantity(self.value * other, self.unit)
        return Quantity(self.value, self.unit * other)

    def __rmul__(self, other: Self) -> Self:
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, type(self)):
            return Quantity(self.value / other.value, self.unit / other.unit)
        if isinstance(other, Number):
            return Quantity(self.value / other, self.unit)
        return Quantity(self.value, self.unit / other)

    def __rtruediv__(self, other):
        if isinstance(other, type(self)):
            return Quantity(other.value / self.value, other.unit / self.unit)
        if isinstance(other, Number):
            return Quantity(other / self.value, self.unit)
        return Quantity(self.value, other / self.unit)


class CompositeUnit(UnitType):
    def __init__(
        self,
        component_units: tuple[UnitType],
        component_powers: tuple[Number],
        _factor=1,
    ):
        self.display_factor = _factor
        _unit_dict = {}
        for u, p in zip(component_units, component_powers):
            self.display_factor *= u.scaling_factor.factor**p
            base_u = u.but(scaling_factor=uni)
            _unit_dict[base_u] = _unit_dict.get(base_u, 0) + p
        _unit_dict = {u: p for u, p in _unit_dict.items() if p != 0 and u != one}
        self._component_units = tuple(_unit_dict.keys())
        self._component_powers = tuple(_unit_dict.values())
        self._preferred_units = None

    @property
    def component_units(self):
        return self._component_units

    @property
    def component_powers(self):
        return self._component_powers

    def __mul__(self, other) -> Self:
        if isinstance(other, CompositeUnit):
            return CompositeUnit(
                component_units=self.component_units + other.component_units,
                component_powers=self.component_powers + other.component_powers,
                _factor=self.display_factor * other.display_factor,
            )
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(*self.component_units, other),
                component_powers=(*self.component_powers, 1),
                _factor=self.display_factor,
            )
        if isinstance(other, ScalingFactor):
            return CompositeUnit(
                component_units=self.component_units,
                component_powers=self.component_powers,
                _factor=self.display_factor * other.factor,
            )
        if isinstance(other, Number):
            return Quantity(other, self)
        return NotImplemented

    def __rmul__(self, other) -> Self:
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, CompositeUnit):
            return CompositeUnit(
                component_units=self.component_units + other.component_units,
                component_powers=self.component_powers
                + tuple([-e for e in other.component_powers]),
                _factor=self.display_factor / other.display_factor,
            )
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(*self.component_units, other),
                component_powers=(*self.component_powers, -1),
                _factor=self.display_factor,
            )
        if isinstance(other, ScalingFactor):
            return CompositeUnit(
                component_units=self.component_units,
                component_powers=self.component_powers,
                _factor=self.display_factor / other.factor,
            )
        if isinstance(other, Number):
            return Quantity(1 / other, self)
        return NotImplemented

    def __rtruediv__(self, other):
        # other / self
        if isinstance(other, CompositeUnit):
            return CompositeUnit(
                component_units=other.component_units + self.component_units,
                component_powers=other.component_powers
                + tuple([-e for e in self.component_powers]),
                _factor=other.display_factor / self.display_factor,
            )
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(*self.component_units, other),
                component_powers=(*tuple([(-e) for e in self.component_powers]), 1),
                _factor=1 / self.display_factor,
            )
        if isinstance(other, ScalingFactor):
            return CompositeUnit(
                component_units=self.component_units,
                component_powers=tuple([-e for e in self.component_powers]),
                _factor=other.factor / self.display_factor,
            )
        if isinstance(other, Number):
            return Quantity(other, self**-1)
        return NotImplemented

    def __pow__(self, other: Number):
        if isinstance(other, Number):
            return CompositeUnit(
                component_units=self.component_units,
                component_powers=tuple([other * e for e in self.component_powers]),
                _factor=self.display_factor**other,
            )
        return NotImplemented

    def __repr__(self):
        return (
            "["
            + " ".join(
                f"{unit}^{power}"
                for unit, power in zip(self.component_units, self.component_powers)
            )
            + "]"
        )

    def __hash__(self):
        return hash((self.component_units, self.component_powers))

    def __eq__(self, other):
        up_self = dict(zip(self.component_units, self.component_powers))
        up_other = dict(zip(other.component_units, other.component_powers))
        return (self.display_factor, up_self) == (other.display_factor, up_other)


class Unit(UnitType, metaclass=MultitonMeta):
    def __init__(
        self,
        physical_dimension: PhysicalDimension,
        name: str,
        symbol: str,
        referent: Optional[Referent] = None,
        scaling_factor: Optional[ScalingFactor] = uni,
    ):
        self._physical_dimension = physical_dimension
        self._name = name
        self._symbol = symbol
        self._referent = referent
        self._scaling_factor = scaling_factor

    @property
    def physical_dimension(self):
        return self._physical_dimension

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def referent(self):
        return self._referent

    @property
    def scaling_factor(self):
        return self._scaling_factor

    def __mul__(self, other) -> Self:
        if isinstance(other, ScalingFactor):
            return Unit(
                physical_dimension=self.physical_dimension,
                name=self.name,
                symbol=self.symbol,
                referent=self.referent,
                scaling_factor=self.scaling_factor * other,
            )
        if isinstance(other, CompositeUnit):
            return other * self
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(self, other),
                component_powers=(1, 1),
            )
        if isinstance(other, Number):
            return Quantity(other, self)
        return NotImplemented

    def __rmul__(self, other) -> Self:
        return self * other

    def but(self, **kwargs) -> UnitType:
        return Unit(
            **(
                {
                    "physical_dimension": self.physical_dimension,
                    "name": self.name,
                    "symbol": self.symbol,
                    "referent": self.referent,
                    "scaling_factor": self.scaling_factor,
                }
                | kwargs
            ),
        )

    def __truediv__(self, other):
        if isinstance(other, Number):
            return Quantity(1 / other, self)
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(self, other),
                component_powers=(1, -1),
            )
        return NotImplemented

    def __rtruediv__(self, other: UnitType):
        if isinstance(other, Number):
            return Quantity(other, self**-1)
        if isinstance(other, Unit):
            return CompositeUnit(
                component_units=(self, other),
                component_powers=(-1, 1),
            )
        return NotImplemented

    def __pow__(self, power: Number):
        return CompositeUnit(
            component_units=(self,),
            component_powers=(power,),
        )

    def __hash__(self):
        return hash(
            (
                self.physical_dimension,
                self.name,
                self.symbol,
                self.referent,
                self.scaling_factor,
            ),
        )

    def __str__(self):
        s = self.symbol
        if self.referent:
            s += f"[{self.referent}]"
        if self.scaling_factor:
            s = self.scaling_factor.symbol + s
        return s

    def __repr__(self):
        return f"[{self}]"


# SI base units
one = Unit(physical_dimension=PhysicalDimension.NONDIMENSIONAL, name="", symbol="")
second = Unit(physical_dimension=PhysicalDimension.TIME, name="second", symbol="s")
meter = Unit(physical_dimension=PhysicalDimension.LENGTH, name="meter", symbol="m")
gram = Unit(physical_dimension=PhysicalDimension.MASS, name="gram", symbol="g")
ampere = Unit(physical_dimension=PhysicalDimension.CURRENT, name="ampere", symbol="A")
kelvin = Unit(
    physical_dimension=PhysicalDimension.TEMPERATURE,
    name="kelvin",
    symbol="K",
)
mole = Unit(
    physical_dimension=PhysicalDimension.AMOUNT_OF_SUBSTANCE,
    name="mole",
    symbol="mol",
)
candela = Unit(
    physical_dimension=PhysicalDimension.LUMINOUS_INTENSITY,
    name="candela",
    symbol="cd",
)
radian = Unit(
    physical_dimension=PhysicalDimension.ANGLE,
    name="radian",
    symbol="rad",
)

kilogram = kilo * gram

steradian = radian**2
turn = 2 * PI * radian

liter = 1e-3 * meter**3
hertz = turn / second
newton = kilo * gram * meter / second**2
joule = kilo * gram * meter**2 / second**2
watt = joule / second
coulomb = ampere * second
volt = joule / coulomb
farad = coulomb / volt
ohm = volt / ampere
siemens = 1 / ohm
weber = joule / ampere
tesla = volt * second / meter**2
henry = volt * second / ampere
lumen = coulomb * steradian
lux = lumen / meter**2
becquerel = one.but(referent="decays") / second
minute = 60 * second
hour = 60 * minute
barn = 1e-28 * meter**2
dalton = 1.66053906660e-27 * kilogram
