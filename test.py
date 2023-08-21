from rich.console import Console
from rich.markup import escape
from rich.table import Table

import cubit.units
from cubit.system import UNIT_REGISTRY
from cubit.units import CompositeUnit, Unit

console = Console()

table = Table(title="Base Units")

table.add_column("Name")
table.add_column("Type")
table.add_column("Symbol")
table.add_column("Representation")
table.add_column("Decomposition")
table.add_column("Decomposed Type")
for k, v in dict(UNIT_REGISTRY).items():
    if (
        isinstance(v, Unit)
        and v.referent is None
        and v.scaling_factor == cubit.units.uni
    ):
        d_v = v.decompose()
        table.add_row(
            v.name,
            type(v).__qualname__,
            repr(k),
            escape(repr(v)),
            escape(repr(d_v)),
            type(d_v).__qualname__,
        )
console.print(table)

table = Table(title="Derived Units with Special Names")
table.add_column("Name")
table.add_column("Type")
table.add_column("Symbol")
table.add_column("Representation")
table.add_column("Decomposition")
table.add_column("Decomposed Type")
for k, v in dict(UNIT_REGISTRY).items():
    if (
        isinstance(v, CompositeUnit)
        and (
            any(u.referent is not None for u in v.component_units) or v.name is not None
        )
    ) or (isinstance(v, Unit) and v.referent is not None):
        d_v = v.decompose()
        table.add_row(
            v.name,
            type(v).__qualname__,
            repr(k),
            escape(repr(v)),
            escape(repr(d_v)),
            type(d_v).__qualname__,
        )
console.print(table)
