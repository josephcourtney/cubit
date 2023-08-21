# import pytest
#
# from cubit import physical_data, units
#
# def test_import():
#    physical_data.import_isotope_data()
#    physical_data.import_moment_data()
#
#
# def test_isotope_gyromagnetic_ratio():
#    h1 = physical_data.ISOTOPES[("H", 1)]
#
#    expected = 5.58569468 * units.one
#    assert h1.nuclear_g_factor.unit == expected.unit
#    # assert h1.nuclear_g_factor.value == pytest.approx(expected.value)
#
#    # expected = 42.5774857e6
#    # assert h1.gyromagnetic_ratio.unit == expected.unit
#    # assert h1.gyromagnetic_ratio.value == pytest.approx(expected.value)
#
#    # h2 = physical_data.ISOTOPES[("H", 2)]
#    ## 2.86 milli electron barns
#    # expected = 2.86e-3 * physical_data.ELEMENTARY_CHARGE * units.barn
#    # assert ((h2.quadrupolar_moment - expected) / expected).value == pytest.approx(0)


# TODO: make CompositeUnit store all component units in base units
# TODO: make CompositeUnit fold all scaling factors into one multiplier and store preferred printing units
