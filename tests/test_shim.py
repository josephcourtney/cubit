import pytest

from connvert import shim


def test_open_file():
    # covers all typical inputs
    raise AssertionError


def test_validate_path_nmrpipe():
    # fails when path does not exist
    raise AssertionError
    # detects and globs for multi-part pattern
    raise AssertionError
    # checks each file for correct header
    raise AssertionError
    # correctly specializes file type to single-file
    raise AssertionError
    # correctly specializes file type to multi-file
    raise AssertionError


def test_validate_path_bruker():
    # fails when path does not exist
    raise AssertionError
    # checks for correct directory contents
    raise AssertionError
    # correctly specializes file type to topspin
    raise AssertionError
    # correctly specializes file type to topspin 4
    raise AssertionError
    # correctly specializes file type to xwinnmr
    raise AssertionError


def test_validate_path_rnmrtk():
    # fails when path does not exist
    raise AssertionError
    # checks for correct directory contents
    raise AssertionError


def test_validate_path_sparky():
    # fails when path does not exist
    raise AssertionError
    # checks file for correct header
    raise AssertionError


def test_validate_path_varian():
    # fails when path does not exist
    raise AssertionError
    # checks for correct directory contents
    raise AssertionError
    # correctly specializes file type to spinsight
    raise AssertionError
    # correctly specializes file type to vnmr
    raise AssertionError


def test_validate_path_azara():
    raise AssertionError


def test_validate_path_ccpn():
    raise AssertionError


def test_validate_path_ge():
    raise AssertionError


def test_validate_path_hms_ist():
    raise AssertionError


def test_validate_path_jeol():
    raise AssertionError


def test_validate_path_magritek():
    raise AssertionError


def test_validate_path_nmrglue_hdf5():
    raise AssertionError


def test_validate_path_nmrview():
    raise AssertionError


def test_validate_path_poky():
    raise AssertionError


def test_validate_path_xeasy():
    raise AssertionError


def test_guess_file_type():
    assert shim.guess_file_format("./nhsqc.ucsf") == 0

    # covers all file types
    raise AssertionError
    # returns correct file type
    raise AssertionError
    # when return_path is True, returns correct Path or set of Paths
    raise AssertionError


def test_nmrglue_read():
    # covers all supported file types
    raise AssertionError
    # fails on non-supported file types
    raise AssertionError
    # correctly guesses udic
    raise AssertionError


def test_convert_with_external_utility():
    # correctly matches input and output formats to correct utility
    raise AssertionError
    # routes path through multiple utilities if no single utility exists
    raise AssertionError
    # fails when no valid combination of conversion utilities exists
    raise AssertionError
    # fails gracefully when file is malformed
    raise AssertionError
    # correctly handles AZARA files where par and spc files do not have the same name
    raise AssertionError
    # implements nmrglue
    raise AssertionError


def test_convert_file():
    # calls internal methods for supported formats
    raise AssertionError
    # falls back to external utilities when necessary
    raise AssertionError
    # correctly matches input and output formats to correct utility
    raise AssertionError
    # fails gracefully when file is malformed
    raise AssertionError
