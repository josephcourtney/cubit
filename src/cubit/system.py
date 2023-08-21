from collections.abc import Iterable
from copy import copy
from enum import Enum
from fractions import Fraction
from typing import NotRequired, Optional, Self, TypedDict, Union, overload
from typing_extensions import Unpack

from ._base import Default, MultitonMeta, NumberLike, Sentinel

UNIT_REGISTRY: dict[
    str,
    Union["Unit", "CompositeUnit"],
] = {}

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
    ],
)


class ScalingFactor(metaclass=MultitonMeta, key=("factor",)):
    def __init__(
        self,
        name: str,
        symbol: str,
        factor: NumberLike,
    ):
        self.name: str = name
        self.symbol: str = symbol
        self.factor: NumberLike = factor

    def __copy__(self):
        return type(self)(self.name, self.symbol, self.factor)

    def __repr__(self):
        return f"<{self.name}({self.symbol}) = {self.factor:1.0e}>"

    __str__ = __repr__

    @overload
    def __mul__(self, other: Self) -> Self:
        ...

    @overload
    def __mul__(self, other: NumberLike) -> "Quantity":
        ...

    def __mul__(self, other):
        match other:
            case ScalingFactor():
                return type(self)(
                    "+".join((self.name, other.name)),
                    "+".join((self.symbol, other.symbol)),
                    self.factor * other.factor,
                )
            case int() | float() | complex() | Fraction():
                return Quantity(other, self * unum)
            case _:
                return NotImplemented

    def __rmul__(self, other: NumberLike) -> "Quantity":
        return self.__mul__(other)

    @overload
    def __truediv__(self, other: Self) -> Self:
        ...

    @overload
    def __truediv__(self, other: NumberLike) -> "Quantity":
        ...

    def __truediv__(self, other):
        match other:
            case ScalingFactor():
                return type(self)(
                    "+".join((self.name, other.name)),
                    "+".join((self.symbol, other.symbol)),
                    self.factor / other.factor,
                )
            case int() | float() | complex() | Fraction():
                return Quantity(1 / other, self * unum)
            case _:
                return NotImplemented

    def __rtruediv__(self, other: NumberLike) -> "Quantity":
        match other:
            case int() | float() | complex() | Fraction():
                return Quantity(other, CompositeUnit((unum / self,), (1,)))
            case _:
                return NotImplemented


uni: ScalingFactor = ScalingFactor("", "", 1e0)


class QuantityData(TypedDict):
    value: NotRequired[NumberLike]
    unit: NotRequired[Optional["CompositeUnit"]]

class Quantity:
    def __init__(
        self,
        value: NumberLike,
        unit: Optional["CompositeUnit"] = None,
    ):
        self.value = value
        if unit is None:
            self.unit: CompositeUnit = CompositeUnit(
                component_units=(unum,),
                component_powers=(1,),
            )
        elif isinstance(unit, Unit):
            self.unit = CompositeUnit(
                component_units=(unit,),
                component_powers=(1,),
            )
        elif isinstance(unit, CompositeUnit):
            self.unit = unit
        else:
            msg = (
                "unit can only be of type Unit or CompositeUnit. If unit is None,"
                + " it defaults to non-dimensinoal"
            )
            raise TypeError(msg)

    def __copy__(self):
        return Quantity(self.value, self.unit)

    def but(
        self,
        **kwargs: Unpack[QuantityData],
    ) -> Self:
        return type(self)(
            **(
                QuantityData(
                    {
                        "value": self.value,
                        "unit": self.unit,
                    },
                )
                | kwargs
            ),
        )


    def __hash__(self):
        return hash((self.unit, self.value))

    def __repr__(self) -> str:
        return f"{self.value} {self.unit}"

    def __eq__(self, other: object) -> bool:
        match other:
            case Quantity():
                return self.value == other.value and self.unit == other.unit
            case int() | float() | complex() | Fraction():
                return self.value == other and self.unit == unum
            case _:
                return False

    def __pow__(self, other: NumberLike) -> Self:
        match other:
            case int() | float() | complex() | Fraction():
                return type(self)(self.value**other, self.unit**other)
            case _:
                return NotImplemented

    def __neg__(self) -> Self:
        return type(self)(-self.value, self.unit)

    def __sub__(self, other: Self) -> Self:
        if self.unit != other.unit:
            msg = "Only quantities of the same type can be subtracted"
            raise TypeError(msg)
        return type(self)(self.value - other.value, self.unit)

    def __add__(self, other: Self) -> Self:
        if self.unit != other.unit:
            msg = "Only quantities of the same type can be added"
            raise TypeError(msg)
        return type(self)(self.value + other.value, self.unit)

    @overload
    def __mul__(self, other: Self) -> Self:
        ...

    @overload
    def __mul__(self, other: NumberLike) -> Self:
        ...

    @overload
    def __mul__(self, other: ScalingFactor) -> Self:
        ...

    def __mul__(self, other):
        match other:
            case Quantity():
                return type(self)(self.value * other.value, self.unit * other.unit)
            case int() | float() | complex() | Fraction():
                return type(self)(self.value * other, self.unit)
            case ScalingFactor():
                return type(self)(self.value, self.unit * other)
            case _:
                return NotImplemented

    @overload
    def __rmul__(self, other: NumberLike) -> Self:
        ...

    @overload
    def __rmul__(self, other: ScalingFactor) -> Self:
        ...

    def __rmul__(self, other):
        return self.__mul__(other)

    @overload
    def __truediv__(self, other: Self) -> Self:
        ...

    @overload
    def __truediv__(self, other: NumberLike) -> Self:
        ...

    @overload
    def __truediv__(self, other: ScalingFactor) -> Self:
        ...

    def __truediv__(self, other):
        match other:
            case Quantity():
                return type(self)(self.value / other.value, self.unit / other.unit)
            case int() | float() | complex() | Fraction():
                return type(self)(self.value / other, self.unit)
            case ScalingFactor():
                return type(self)(self.value, self.unit / other)
            case _:
                return NotImplemented

    @overload
    def __rtruediv__(self, other: NumberLike) -> Self:
        ...

    @overload
    def __rtruediv__(self, other: ScalingFactor) -> Self:
        ...

    def __rtruediv__(self, other):
        match other:
            case int() | float() | complex() | Fraction():
                return Quantity(other / self.value, self.unit)
            case ScalingFactor():
                return Quantity(self.value, other / self.unit)
            case _:
                return NotImplemented


class CompositeUnitData(TypedDict):
    component_units: NotRequired[Iterable["Unit"]]
    component_powers: NotRequired[Iterable[NumberLike]]
    name: NotRequired[str | None]
    symbol: NotRequired[str | None]
    factor: NotRequired[NumberLike]


class CompositeUnit:
    def __init__(
        self,
        component_units: Iterable["Unit"],
        component_powers: Iterable[NumberLike],
        name: str | None = None,
        symbol: str | None = None,
        factor: NumberLike = 1,
    ):
        _unit_dict: dict[Unit, NumberLike] = {}
        for u, p in zip(component_units, component_powers, strict=True):
            factor *= u.scaling_factor.factor**p
            base_u = u.but(scaling_factor=uni)
            _unit_dict[base_u] = _unit_dict.get(base_u, 0) + p
        _unit_dict = {u: p for u, p in _unit_dict.items() if p != 0 and u != unum}
        self.factor = factor
        self.component_units = tuple(_unit_dict.keys())
        self.component_powers = tuple(_unit_dict.values())
        self.name = name
        self.symbol = symbol
        UNIT_REGISTRY[str(self)] = self

    @classmethod
    def from_quantity(cls, q: Quantity, **kwargs):
        if isinstance(q.unit, Unit):
            component_units = [q.unit]
            component_powers = [1]
        elif isinstance(q.unit, CompositeUnit):
            component_units = q.unit.component_units
            component_powers = q.unit.component_powers
        return cls(
            component_units=component_units,
            component_powers=component_powers,
            factor=q.value,
        ).but(**kwargs)

    def __copy__(self):
        return type(self)(
            self.component_units,
            self.component_powers,
            self.name,
            self.symbol,
            self.factor,
        )

    def but(
        self,
        **kwargs: Unpack[CompositeUnitData],
    ) -> Self:
        return type(self)(
            **(
                CompositeUnitData(
                    {
                        "component_units": self.component_units,
                        "component_powers": self.component_powers,
                        "name": self.name,
                        "symbol": self.symbol,
                        "factor": self.factor,
                    }
                )
                | kwargs
            ),
        )

    def decompose(self):
        return self.but(name=None, symbol=None)

    @overload
    def __mul__(self, other: Self) -> Self:
        ...

    @overload
    def __mul__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __mul__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __mul__(self, other: Quantity) -> Quantity:
        ...

    def __mul__(self, other):
        match other:
            case CompositeUnit():
                return type(self)(
                    component_units=self.component_units + other.component_units,
                    component_powers=self.component_powers + other.component_powers,
                    factor=self.factor * other.factor,
                )
            case ScalingFactor():
                return type(self)(
                    component_units=self.component_units,
                    component_powers=self.component_powers,
                    factor=self.factor * other.factor,
                )
            case int() | float() | complex() | Fraction():
                return Quantity(other, self)
            case Quantity():
                return Quantity(other.value, other.unit * self)
            case _:
                return NotImplemented

    @overload
    def __rmul__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __rmul__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __rmul__(self, other: Quantity) -> Quantity:
        ...

    def __rmul__(self, other):
        match other:
            case ScalingFactor():
                return self.__mul__(other)
            case int() | float() | complex() | Fraction():
                return self.__mul__(other)
            case Quantity():
                return Quantity(other.value, other.unit * self)
            case _:
                return NotImplemented

    @overload
    def __truediv__(self, other: Self) -> Self:
        ...

    @overload
    def __truediv__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __truediv__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __truediv__(self, other: Quantity) -> Quantity:
        ...

    def __truediv__(self, other):
        match other:
            case CompositeUnit():
                return type(self)(
                    component_units=self.component_units + other.component_units,
                    component_powers=(self.component_powers + tuple(-e for e in other.component_powers)),
                    factor=self.factor / other.factor,
                )
            case ScalingFactor():
                return type(self)(
                    component_units=self.component_units,
                    component_powers=self.component_powers,
                    factor=self.factor / other.factor,
                )
            case int() | float() | complex() | Fraction():
                return Quantity(1 / other, self)
            case Quantity():
                return Quantity(1 / other.value, self / other.unit)
            case _:
                return NotImplemented

    @overload
    def __rtruediv__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __rtruediv__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __rtruediv__(self, other: Quantity) -> Quantity:
        ...

    def __rtruediv__(self, other):
        match other:
            case ScalingFactor():
                return type(self)(
                    component_units=self.component_units,
                    component_powers=tuple(-e for e in self.component_powers),
                    factor=other.factor / self.factor,
                )
            case int() | float() | complex() | Fraction():
                return Quantity(other, self**-1)
            case Quantity():
                return Quantity(other.value, other.unit / self)
            case _:
                return NotImplemented

    def __pow__(self, other: NumberLike) -> Self:
        return type(self)(
            component_units=self.component_units,
            component_powers=tuple(other * e for e in self.component_powers),
            factor=self.factor**other,
        )

    def __str__(self):
        if self.symbol is None:
            return " ".join(
                f"{unit}" if power == 1 else f"{unit}^{power}"
                for unit, power in zip(self.component_units, self.component_powers, strict=True)
            )
        return self.symbol

    def __repr__(self):
        return f"[{self}]"

    def __hash__(self):
        return hash((self.component_units, self.component_powers))

    def __eq__(self, other: object) -> bool:
        match other:
            case CompositeUnit():
                up_self = dict(zip(self.component_units, self.component_powers, strict=True))
                up_other = dict(zip(other.component_units, other.component_powers, strict=True))
                return (self.factor, up_self) == (other.factor, up_other)
            case Unit():
                up_self = dict(zip(self.component_units, self.component_powers, strict=True))
                up_other = dict(zip((other,), (1,), strict=True))
                return (self.factor, up_self) == (other.scaling_factor.factor, up_other)
            case _:
                return False

class UnitData(TypedDict):
    physical_dimension: NotRequired[PhysicalDimension]
    name: NotRequired[str]
    symbol: NotRequired[str]
    referent: NotRequired[str | None]
    scaling_factor: NotRequired[ScalingFactor]

class Unit(metaclass=MultitonMeta, key=("symbol", "scaling_factor", "referent")):
    def __init__(
        self,
        physical_dimension: PhysicalDimension,
        name: str,
        symbol: str,
        referent: str | None = None,
        scaling_factor: ScalingFactor = uni,
    ):
        self.physical_dimension = physical_dimension
        self.name = name
        self.symbol = symbol
        self.referent = referent
        self.scaling_factor = scaling_factor
        UNIT_REGISTRY[str(self)] = self

    @classmethod
    def get(cls, key):
        return UNIT_REGISTRY.get(key)

    @overload
    def __mul__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __mul__(self, other: CompositeUnit) -> CompositeUnit:
        ...

    @overload
    def __mul__(self, other: Self) -> CompositeUnit:
        ...

    @overload
    def __mul__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __mul__(self, other: Quantity) -> Quantity:
        ...

    def __mul__(self, other):
        match other:
            case ScalingFactor():
                return type(self)(
                    physical_dimension=self.physical_dimension,
                    name=self.name,
                    symbol=self.symbol,
                    referent=self.referent,
                    scaling_factor=self.scaling_factor * other,
                )
            case CompositeUnit():
                return CompositeUnit(
                    component_units=(*other.component_units, self),
                    component_powers=(*other.component_powers, -1),
                    factor=other.factor,
                )
            case Unit():
                return CompositeUnit(
                    component_units=(self, other),
                    component_powers=(1, 1),
                )
            case int() | float() | complex() | Fraction():
                return Quantity(
                    other,
                    CompositeUnit((self,), (1,)),
                )
            case Quantity():
                return Quantity(
                    other,
                    other.unit * self,
                )
            case _:
                return NotImplemented

    @overload
    def __rmul__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __rmul__(self, other: ScalingFactor) -> Self:
        ...

    @overload
    def __rmul__(self, other: Quantity) -> Quantity:
        ...

    @overload
    def __rmul__(self, other: CompositeUnit) -> CompositeUnit:
        ...

    def __rmul__(self, other):
        return self * other

    def but(
        self,
        **kwargs: Unpack[UnitData],
    ) -> Self:
        return type(self)(
            **(
                UnitData(
                    {
                        "physical_dimension": self.physical_dimension,
                        "name": self.name,
                        "symbol": self.symbol,
                        "referent": self.referent,
                        "scaling_factor": self.scaling_factor,
                    },
                )
                | kwargs
            ),
        )


    def decompose(self):
        return self

    @overload
    def __truediv__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __truediv__(self, other: Self) -> CompositeUnit:
        ...

    @overload
    def __truediv__(self, other: CompositeUnit) -> CompositeUnit:
        ...

    @overload
    def __truediv__(self, other: Quantity) -> Quantity:
        ...

    @overload
    def __truediv__(self, other: ScalingFactor) -> Self:
        ...

    def __truediv__(self, other):
        match other:
            case int() | float() | complex() | Fraction():
                return Quantity(1 / other, self)
            case Unit():
                return CompositeUnit(
                    component_units=(self, other),
                    component_powers=(1, -1),
                )
            case CompositeUnit():
                return CompositeUnit(
                    component_units=(*other.component_units, self),
                    component_powers=(
                        *tuple(-e for e in other.component_powers),
                        1,
                    ),
                    factor=1 / other.factor,
                )
            case Quantity():
                return Quantity(
                    1 / other.value,
                    self / other.unit,
                )
            case ScalingFactor():
                return self.but(
                    scaling_factor=self.scaling_factor / other,
                )
            case _:
                return NotImplemented

    @overload
    def __rtruediv__(self, other: NumberLike) -> Quantity:
        ...

    @overload
    def __rtruediv__(self, other: Self) -> CompositeUnit:
        ...

    @overload
    def __rtruediv__(self, other: CompositeUnit) -> CompositeUnit:
        ...

    @overload
    def __rtruediv__(self, other: ScalingFactor) -> CompositeUnit:
        ...

    @overload
    def __rtruediv__(self, other: Quantity) -> Quantity:
        ...

    def __rtruediv__(self, other):
        match other:
            case int() | float() | complex() | Fraction():
                return Quantity(other, self**-1)
            case Unit():
                return CompositeUnit(
                    component_units=(self, other),
                    component_powers=(-1, 1),
                )
            case CompositeUnit():
                return CompositeUnit(
                    component_units=(*other.component_units, self),
                    component_powers=(*other.component_powers, 1),
                    factor=other.factor,
                )
            case ScalingFactor():
                return CompositeUnit(
                    (self,),
                    (-1,),
                    factor=other.factor,
                )
            case Quantity():
                return other.but(unit=other.unit / self)
            case _:
                return NotImplemented

    def __pow__(self, power: NumberLike) -> CompositeUnit:
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


unum: Unit = Unit(
    physical_dimension=PhysicalDimension.NONDIMENSIONAL,
    name="unum",
    symbol="",
)
