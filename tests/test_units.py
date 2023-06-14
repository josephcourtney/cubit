import itertools

import pytest

from connvert import units
from connvert.units import CompositeUnit, Quantity, ScalingFactor, Unit

example_types = [
    2,
    2.0,
    units.meter,
    units.second,
    units.milli,
    units.nano,
    (2 * units.meter),
    (2 * (units.meter / units.second)),
    (units.meter / units.second),
    (units.gram * units.meter),
]

type_combinations = {
    (int, int): int,
    (int, float): float,
    (int, ScalingFactor): Quantity,
    (int, Unit): Quantity,
    (int, CompositeUnit): Quantity,
    (int, Quantity): Quantity,
    (float, float): float,
    (float, ScalingFactor): Quantity,
    (float, Unit): Quantity,
    (float, CompositeUnit): Quantity,
    (float, Quantity): Quantity,
    (ScalingFactor, ScalingFactor): ScalingFactor,
    (ScalingFactor, Unit): Unit,
    (ScalingFactor, CompositeUnit): CompositeUnit,
    (ScalingFactor, Quantity): Quantity,
    (Unit, Unit): CompositeUnit,
    (Unit, CompositeUnit): CompositeUnit,
    (Unit, Quantity): Quantity,
    (CompositeUnit, CompositeUnit): CompositeUnit,
    (CompositeUnit, Quantity): Quantity,
    (Quantity, Quantity): Quantity,
}
type_combinations |= {k[::-1]: v for k, v in type_combinations.items()}

type_combinations_div = type_combinations | {
    (ScalingFactor, Unit): CompositeUnit,
}


@pytest.mark.parametrize(
    ("a", "b"),
    itertools.product(example_types, example_types),
    ids=lambda x: f"{type(x).__name__}",
)
def test_mul(a, b):
    c = a * b
    assert type(c) == type_combinations.get((type(a), type(b)), int)


@pytest.mark.parametrize(
    ("a", "b"),
    itertools.product(example_types, example_types),
    ids=lambda x: f"{type(x).__name__}",
)
def test_div(a, b):
    c = a / b
    if isinstance(a, int) and isinstance(b, (int, float)):
        assert type(c) == float
    else:
        assert type(c) == type_combinations_div.get((type(a), type(b)), int)
