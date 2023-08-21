from .system import CompositeUnit, PhysicalDimension, ScalingFactor, Unit, uni, unum

PI = 3.1415926535897932384626433832795028841971693993751058


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

# SI base units
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

turn = CompositeUnit.from_quantity(
    2 * PI * radian,
    name="turn",
    symbol="turn",
)
cycle = unum.but(name="cycle", referent="cycle")
disintegration = unum.but(name="disintegration", referent="disintegration")

# SI derived units
hertz = (cycle / second).but(name="hertz", symbol="Hz")
steradian = (radian**2).but(name="steradian", symbol="sr")
liter = (milli * meter**3).but(name="liter", symbol="L")
newton = (kilo * gram * meter / second**2).but(name="newton", symbol="N")
joule = (kilo * gram * meter**2 / second**2).but(name="joule", symbol="J")
watt = (joule / second).but(name="watt", symbol="W")
coulomb = (ampere * second).but(name="coulomb", symbol="C")
volt = (joule / coulomb).but(name="volt", symbol="V")
farad = (coulomb / volt).but(name="farad", symbol="F")
ohm = (volt / ampere).but(name="ohm", symbol="Ω")
siemens = (ohm**-1).but(name="siemens", symbol="S")
weber = (joule / ampere).but(name="weber", symbol="Wb")
tesla = (volt * second / meter**2).but(name="tesla", symbol="T")
henry = (volt * second / ampere).but(name="henry", symbol="H")
lumen = (coulomb * steradian).but(name="lumen", symbol="lm")
lux = (lumen / meter**2).but(name="lux", symbol="lx")
becquerel = (disintegration / second).but(name="becquerel", symbol="Bq")

minute = CompositeUnit(
    component_units=[second],
    component_powers=[1],
    factor=60,
    name="minute",
    symbol="min",
)
hour = CompositeUnit(
    component_units=[second],
    component_powers=[1],
    factor=3600,
    name="hour",
    symbol="h",
)
barn = CompositeUnit(
    component_units=[meter],
    component_powers=[2],
    factor=1e-28,
    name="barn",
    symbol="b",
)
dalton = CompositeUnit(
    component_units=[kilogram],
    component_powers=[2],
    factor=1.66053906660e-27,
    name="dalton",
    symbol="Da",
)
