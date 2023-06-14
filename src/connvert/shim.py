import contextlib
import enum
import io
import logging
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

import nmrglue as ng
import numpy as np

logging.basicConfig(filename="connvert.log", encoding="utf-8", level=logging.DEBUG)


# TODO: move information into json file and dynamically create enum
class FileFormat(enum.Enum):
    """FileFormat."""

    def __new__(cls, *args, **kwargs):  # noqa: ARG003
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value  # noqa: SLF001
        return obj

    def __init__(self, data_suffix, metadata_suffix):
        self.data_suffix = data_suffix
        self.metadata_suffix = metadata_suffix

    AZARA = "spc", "par"
    BRUKER_TOPSPIN = (), ()
    BRUKER_TOPSPIN4 = (), ()
    BRUKER_XWINNMR = (), ()
    CCPN_HDF5 = ("h5", "hdf5"), ()
    JEOL = ("jdf",), ()
    MAGRITEK = ("1d", "2d", "3d", "4d"), ("par",)
    TECMAG = ("tnt",), ()
    NMRGLUE_HDF5 = ("h5", "hdf5"), ()
    NMRPIPE_MULTIFILE = (
        "pipe",
        "fid",
        "ft",
        "ft1",
        "ft2",
        "ft3",
        "ft4",
        "smile",
    ), ()
    NMRPIPE_SINGLE_FILE = (
        "pipe",
        "fid",
        "ft",
        "ft1",
        "ft2",
        "ft3",
        "ft4",
        "smile",
    ), ()
    NMRVIEW = ("nv",), ()
    SPARKY_UCSF = ("ucsf",), ()
    VARIAN_VNMR = ("fid",), ()
    VARIAN_SPINSIGHT = (), ()
    XEASY = (), ()


FileFormat.NMRGLUE_FILETYPES = FileFormat.NMRGLUE_HDF5
FileFormat.NMRPIPE_FILETYPES = (
    FileFormat.NMRPIPE_MULTIFILE,
    FileFormat.NMRPIPE_SINGLE_FILE,
)
FileFormat.BRUKER_FILETYPES = (
    FileFormat.BRUKER_TOPSPIN,
    FileFormat.BRUKER_TOPSPIN4,
    FileFormat.BRUKER_XWINNMR,
)
FileFormat.VARIAN_FILETYPES = (FileFormat.VARIAN_VNMR, FileFormat.VARIAN_SPINSIGHT)


CONVERTERS = [
    # (in_format, out_format, binary, in_flag, out_flag)
]


@contextlib.contextmanager
def open_file(file, *args, **kwargs):
    if isinstance(file, io.IOBase):
        if args or kwargs:
            logging.warning(
                "trying to re-open a file-like object. Extra arguments are ignored. args=%s, kwargs=%s",
                args,
                kwargs,
            )
        yield file
    if isinstance(file, (str, bytes)):
        path = Path(file)
    if isinstance(path, Path):
        with path.open(*args, **kwargs) as f:
            yield f
        return
    msg = f"{file} is not a path or file-like"
    raise TypeError(msg)


def validate_path_nmrpipe(path):
    if isinstance(path, (str, bytes)):
        path = Path(path)
    if not path.exists():
        msg = f"no NMRPipe files found at {str(path)}"
        raise RuntimeError(msg)
    dir_path = path.parent() if path.is_dir() else path

    # check if path could be part of multi-part spectru
    match_obj = re.match(r"(.*)%(\d+)d(.*)", path.name)
    if match_obj:
        paths = path.glob(
            f"{match_obj.group(1)}{'[0-9]'*len(match_obj.group(2))}{match_obj.group(3)}",
        )
        file_format = FileFormat.NMRPIPE_MULTIFILE
    else:
        paths = dir_path.glob("*")
        file_format = FileFormat.NMRPIPE_SINGLE_FILE

    valid_paths = []
    for pipe_path in paths:
        with open_file(pipe_path, "rb") as f:
            header = f.read(4 * 3)
        header_numeric = np.frombuffer(header, np.float32)
        nmrpipe_byte_order_constant = 2.345
        if np.isclose(header_numeric[2], nmrpipe_byte_order_constant) or np.isclose(
            header_numeric[2].byteswap(),
            nmrpipe_byte_order_constant,
        ):
            valid_paths.append(pipe_path)
    if valid_paths:
        return file_format, valid_paths
    msg = f"no NMRPipe files found at {str(path)}"
    raise RuntimeError(msg)


def validate_path_bruker(path):
    if isinstance(path, (str, bytes)):
        path = Path(path)
    if path.exists():
        dir_path = path.parent() if path.is_dir() else path
        if (dir_path / "ser").exists() and (
            (dir_path / "acqus").exists() or (dir_path / "acqu").exists()
        ):
            return FileFormat.BRUKER_TOPSPIN, [dir_path]
    msg = f"no Bruker files found at {str(path)}"
    raise RuntimeError(msg)


def validate_path_rnmrtk(path):
    if isinstance(path, (str, bytes)):
        path = Path(path)
    if path.exists():
        dir_path = path.parent() if path.is_dir() else path
        if dir_path.glob("*.sec") and dir_path.glob("*.par"):
            return FileFormat.RNMRTK, [dir_path]
    msg = f"no RNMRTK files found at {str(path)}"
    raise RuntimeError(msg)


def validate_path_sparky(path):
    if isinstance(path, (str, bytes)):
        path = Path(path)
    if path.exists():
        path = path.parent() if path.is_dir() else path
        with path.open() as f:
            header = struct.unpack(">10s 4c 9s 26s 80s 3x l 40s 4x", f.read(180))
        if str(header[0].decode()).strip("\x00") == "UCSF NMR":
            return FileFormat.SPARKY_UCSF, [path]
    msg = f"no Sparky files found at {str(path)}"
    raise RuntimeError(msg)


def validate_path_varian(path):
    if isinstance(path, (str, bytes)):
        path = Path(path)
    if path.exists():
        dir_path = path.parent() if path.is_dir() else path
        if dir_path.glob("*.fid").exists() and (path / "procpar").exists():
            return FileFormat.VARIAN_VNMR, [dir_path]
    msg = f"no Varian/Agilent files found at {str(path)}"
    raise RuntimeError(msg)


def validate_path_azara(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_ccpn(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_jeol(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_magritek(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_tecmag(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_nmrglue_hdf5(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_nmrview(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def validate_path_xeasy(path):
    if isinstance(path, (str, bytes)):
        Path(path)
    return None, []


def guess_file_format(path, return_path=None):
    path_validators = [
        validate_path_nmrpipe,
        validate_path_bruker,
        validate_path_rnmrtk,
        validate_path_sparky,
        validate_path_varian,
        validate_path_azara,
        validate_path_ccpn,
        validate_path_jeol,
        validate_path_magritek,
        validate_path_tecmag,
        validate_path_nmrglue_hdf5,
        validate_path_nmrview,
        validate_path_xeasy,
    ]
    for f in path_validators:
        with contextlib.suppress(RuntimeError):
            file_format, valid_paths = f(path)
            break
    else:
        file_format, valid_paths = None, []

    if not valid_paths:
        raise FileNotFoundError

    if file_format is None:
        msg = "cannot determine file type"
        raise RuntimeError(msg)

    if not bool(return_path):
        return file_format, valid_paths
    return file_format


def nmrglue_read(path, file_format=None):
    if file_format is None:
        file_format = guess_file_format(path)

    if file_format in FileFormat.BRUKER_FILETYPES:
        submod = ng.bruker
    elif file_format in FileFormat.NMRPIPE_FILETYPES:
        submod = ng.pipe
    elif file_format == FileFormat.RNMRTK:
        submod = ng.rnmrtk
    elif file_format == FileFormat.SPARKY_UCSF:
        submod = ng.sparky
    elif file_format in FileFormat.VARIAN_FILETYPES:
        submod = ng.varian
    elif file_format == FileFormat.TECMAG:
        submod = ng.tecmag

    dic, data = submod.read(path)
    udic = submod.guess_udic(dic, data)
    return udic, data


def nmrglue_write(udic, data, path, file_format=None):
    if file_format in FileFormat.BRUKER_FILETYPES:
        submod = ng.bruker
    elif file_format in FileFormat.NMRPIPE_FILETYPES:
        submod = ng.pipe
    elif file_format == FileFormat.RNMRTK:
        submod = ng.rnmrtk
    elif file_format == FileFormat.SPARKY_UCSF:
        submod = ng.sparky
    elif file_format in FileFormat.VARIAN_FILETYPES:
        submod = ng.varian
    elif file_format == FileFormat.TECMAG:
        submod = ng.tecmag
    else:
        msg = f"cannot write file format = {file_format} using nmrglue"
        raise RuntimeError(msg)
    submod.write(path, udic, data)


def register_converters():
    converter_registry = {
        (
            FileFormat.NMRPIPE_SINGLE_FILE,
            FileFormat.BRUKER_TOPSPIN,
        ): {
            "./nmrpipe/com/pipe2ser.com": lambda path_in, path_out: subprocess.run(
                ["./nmrpipe/com/pipe2ser.com", "-in", path_in, "-out", path_out],
                capture_output=True,
            ),
        },
        (
            FileFormat.NMRPIPE_SINGLE_FILE,
            FileFormat.NMRPIPE_MULTIFILE,
        ): {
            "./nmrpipe/nmrbin.linux212_64/pipe2xyz": lambda path_in, path_out: subprocess.run(
                [
                    "./nmrpipe/nmrbin.linux212_64/pipe2xyz",
                    "-in",
                    path_in,
                    "-out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.NMRPIPE_MULTIFILE,
            FileFormat.NMRPIPE_SINGLE_FILE,
        ): {
            "./nmrpipe/nmrbin.linux212_64/xyz2pipe": lambda path_in, path_out: subprocess.run(
                [
                    "./nmrpipe/nmrbin.linux212_64/xyz2pipe",
                    "-in",
                    path_in,
                    "-out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.JEOL,
            FileFormat.NMRPIPE_SINGLE_FILE,
        ): {
            "./nmrpipe/nmrbin.linux212_64/delta2pipe": lambda path_in, path_out: subprocess.run(
                [
                    "./nmrpipe/nmrbin.linux212_64/delta2pipe",
                    "-in",
                    path_in,
                    "-out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.BRUKER_TOPSPIN,
            FileFormat.NMRPIPE_SINGLE_FILE,
        ): {
            "./nmrpipe/nmrbin.linux212_64/bruk2pipe": lambda path_in, path_out: subprocess.run(
                [
                    "./nmrpipe/nmrbin.linux212_64/bruk2pipe",
                    "-in",
                    path_in,
                    "-out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.VARIAN_VNMR,
            FileFormat.NMRPIPE_SINGLE_FILE,
        ): {
            "./nmrpipe/nmrbin.linux212_64/var2pipe": lambda path_in, path_out: subprocess.run(
                [
                    "./nmrpipe/nmrbin.linux212_64/var2pipe",
                    "-in",
                    path_in,
                    "-out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.NMRVIEW,
            FileFormat.SPARKY_UCSF,
        ): {
            "./nmrfam-sparky/bin/nv2ucsf": lambda path_in, path_out: subprocess.run(
                ["./nmrfam-sparky/bin/nv2ucsf", path_in, path_out],
                capture_output=True,
            ),
        },
        (
            FileFormat.NMRPIPE_SINGLE_FILE,
            FileFormat.SPARKY_UCSF,
        ): {
            "./nmrfam-sparky/bin/pipe2ucsf": lambda path_in, path_out: subprocess.run(
                ["./nmrfam-sparky/bin/pipe2ucsf", path_in, path_out],
                capture_output=True,
            ),
        },
        (
            FileFormat.NMRPIPE_SINGLE_FILE,
            FileFormat.CCPN_HDF5,
        ): {
            "./CcpNmr-AnalysisAssign/bin/pipe2hdf5": lambda path_in, path_out: subprocess.run(
                [
                    "./CcpNmr-AnalysisAssign/bin/pipe2hdf5",
                    "--in",
                    path_in,
                    "--out",
                    path_out,
                ],
                capture_output=True,
            ),
        },
        (
            FileFormat.AZARA,
            FileFormat.SPARKY_UCSF,
        ): {
            "./azara/utility/azara2ucsf": lambda path_in, path_out: subprocess.run(
                ["./azara/utility/azara2ucsf", path_in.with_suffix(".par"), path_out],
                capture_output=True,
            ),
        },
        (
            FileFormat.SPARKY_UCSF,
            FileFormat.AZARA,
        ): {
            "./azara/utility/ucsf2azara": lambda path_in, path_out: subprocess.run(
                ["./azara/utility/ucsf2azara", path_in, path_out.with_suffix(".par")],
                capture_output=True,
            ),
        },
        (FileFormat.AZARA, FileFormat.XEASY): {
            "./azara/utility/azara2xeasy": lambda path_in, path_out: subprocess.run(
                ["./azara/utility/azara2xeasy", path_in.with_suffix(".par"), path_out],
                capture_output=True,
            ),
        },
    }

    # xyza2pipe utilities
    source_file_readers = {
        FileFormat.VARIAN_VNMR: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/vnmr2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
        FileFormat.BRUKER_XWINNMR: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/xwnmr2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
        FileFormat.AZARA: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/azara2pipe", "--in", path_in.with_suffix(".spc")],
            stdout=subprocess.PIPE,
        ),
        FileFormat.NMRVIEW: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/nv2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
        FileFormat.SPARKY_UCSF: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/ucsf2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
        FileFormat.XEASY: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/xeasy2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
        FileFormat.NMRPIPE_MULTIFILE: lambda path_in: subprocess.Popen(
            ["./xyza2pipe/bin/xyza2pipe", "--in", path_in],
            stdout=subprocess.PIPE,
        ),
    }

    target_file_writers = {
        FileFormat.AZARA: lambda pipe, path_out: subprocess.run(
            ["./xyza2pipe/bin/pipe2azara", "--out", path_out.with_suffix(".spc")],
            capture_output=True,
            stdin=pipe.stdout,
        ),
        FileFormat.NMRVIEW: lambda pipe, path_out: subprocess.run(
            ["./xyza2pipe/bin/pipe2nv", "--out", path_out],
            capture_output=True,
            stdin=pipe.stdout,
        ),
        FileFormat.SPARKY_UCSF: lambda pipe, path_out: subprocess.run(
            ["./xyza2pipe/bin/pipe2ucsf", "--out", path_out],
            capture_output=True,
            stdin=pipe.stdout,
        ),
        FileFormat.XEASY: lambda pipe, path_out: subprocess.run(
            ["./xyza2pipe/bin/pipe2xeasy", "--out", path_out],
            capture_output=True,
            stdin=pipe.stdout,
        ),
        FileFormat.NMRPIPE_MULTIFILE: lambda pipe, path_out: subprocess.run(
            ["./xyza2pipe/bin/pipe2xyza", "--out", path_out],
            capture_output=True,
            stdin=pipe.stdout,
        ),
    }

    # this closure factory is required to capture the values of file_format_in and file_format_out when called
    # in the loop below
    def build_converter(file_format_in, file_format_out):
        def convert(path_in, path_out):
            reader_process = source_file_readers[file_format_in](path_in)
            target_file_writers[file_format_out](reader_process, path_out)
            reader_process.wait()

        return convert

    for file_format_in in source_file_readers:
        for file_format_out in target_file_writers:
            converter_registry[
                (file_format_in, file_format_out)
            ] = converter_registry.get((file_format_in, file_format_out), {}) | {
                "./xyza2pipe/bin/xyza2pipe": build_converter(
                    file_format_in,
                    file_format_out,
                ),
            }

    return converter_registry


CONVERTER_REGISTRY = register_converters()


def convert_with_external_utility(in_path, out_path, in_format, out_format):
    compatible_converters = [
        (binary, in_flag, out_flag)
        for in_format, out_format, binary, in_flag, out_flag in CONVERTER_REGISTRY
    ]
    if not compatible_converters:
        msg = f"no suitable converter found to convert from {in_format} to {out_format}"
        raise RuntimeError(msg)
    binary, in_flag, out_flag = compatible_converters[0]
    result = subprocess.run(
        [binary, in_flag, in_path, out_flag, out_path],
        capture_output=True,
    )
    if result.returncode != 0:
        msg = (f"conversion of {in_path} ({in_format}) to {out_format} failed",)
        raise RuntimeError(msg)


def convert_file(in_path, out_path, in_format, out_format):
    return convert_with_external_utility(in_path, out_path, in_format, out_format)


def read_file(path, file_format=None):
    with contextlib.suppress(RuntimeError):
        return nmrglue_read(path, file_format)
    if file_format is None:
        file_format, valid_paths = guess_file_format(path)
        if not valid_paths:
            msg = f"no valid files found at {str(path)}"
            raise RuntimeWarning(msg)
        if len(valid_paths) > 1:
            msg = f"more than one valid file found at {str(path)}. please narrow selection to a single file."
            raise RuntimeWarning(msg)
        valid_path = valid_paths.pop()
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.chdir(tmp_dir_path)
        shutil.copytree(valid_paths, tmp_dir_path)
        convert_file(
            str(valid_path.absolute()),
            "out.pipe",
            in_format=file_format,
            out_format=FileFormat.NMRPIPE_SINGLE_FILE,
        )
        return nmrglue_read("out.pipe", file_format=FileFormat.NMRPIPE_SINGLE_FILE)


def write_file(path, file_format=None):
    with contextlib.suppress(RuntimeError):
        return nmrglue_read(path, file_format)
    if file_format is None:
        file_format, valid_paths = guess_file_format(path)
        if not valid_paths:
            msg = f"no valid files found at {str(path)}"
            raise RuntimeWarning(msg)
        if len(valid_paths) > 1:
            msg = f"more than one valid file found at {str(path)}. please narrow selection to a single file."
            raise RuntimeWarning(msg)
        valid_path = valid_paths.pop()
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.chdir(tmp_dir_path)
        shutil.copytree(valid_paths, tmp_dir_path)
        convert_file(
            str(valid_path.absolute()),
            "out.pipe",
            in_format=file_format,
            out_format=FileFormat.NMRPIPE_SINGLE_FILE,
        )
        return nmrglue_read("out.pipe", file_format=FileFormat.NMRPIPE_SINGLE_FILE)
