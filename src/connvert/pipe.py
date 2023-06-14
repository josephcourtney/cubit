# %%

import itertools
import re
import struct
from enum import Enum
from pathlib import Path

import metadatatypes
import numpy as np
import physical_data
from rich import print

EPS = 1e-10

# parameters without current known function
#     (40, "FDDMXVAL", 'f', 1),# unknown
#     (41, "FDDMXFLAG", 'f', 1),# unknown
#     (42, "FDDELTATR", 'f', 1),# unknown
#     (286, "FDSRCNAME", 'f', 1),# unknown
#     (290, "FDUSERNAME", 'f', 1),# unknown
#     (464, "FDOPERNAME", 'f', 1),# unknon
#     (297, "FDTITLE", 'f', 1),# unused
#     (312, "FDCOMMENT", 'f', 1),# unused
#     (266, "FDDOMINFO", 'f', 1),# unknown
#     (267, "FDMETHINFO", 'f', 1),# unknown
#     (3, "FDID", 'f', 1),# unknown
#     (478, "FDSCALE", 'f', 1),# unknown
#     (45, "FDNUSDIM", 'i', 1),# unknown
#     (97, "FDREALSIZE", 'i', 1),# obsolete
#     (444, "FDTHREADCOUNT", 'i', 1),# unknown
#     (445, "FDTHREADID", 'i', 1),# unknown
#     (370, "FDSCORE", 'f', 1),# unknown
#     (371, "FDSCANS", 'i', 1),# unknown
#     (419, "FDF2APODDF", 'f', 1),# unknown
# footer information (unused)
#     (359, "FDLASTBLOCK", 'f', 1),# unknown
#     (360, "FDCONTBLOCK", 'f', 1),# unknown
#     (361, "FDBASEBLOCK", 'f', 1),# unknown
#     (362, "FDPEAKBLOCK", 'f', 1),# unknown
#     (363, "FDBMAPBLOCK", 'f', 1),# unknown
#     (364, "FDHISTBLOCK", 'f', 1),# unknown
#     (365, "FD1DBLOCK", 'f', 1),# unknown
# display parameters (unnecessary)
#     (247, "FDMAX", 'f', 1),# maximum real part of data
#     (248, "FDMIN", 'f', 1),# minimum real part of data
#     (250, "FDSCALEFLAG", bool, 1),# True of max and min values are valid
#     (251, "FDDISPMAX", 'f', 1),# max value for display
#     (252, "FDDISPMIN", 'f', 1),# min value for display
#     (253, "FDPTHRESH", 'f', 1),# positive threshold for display
#     (254, "FDNTHRESH", 'f', 1),# negative threshold for display
# fields reserved for user (unused)
#     (70, "FDUSER1", 's', 8),
#     (71, "FDUSER2", 's', 8),
#     (72, "FDUSER3", 's', 8),
#     (73, "FDUSER4", 's', 8),
#     (74, "FDUSER5", 's', 8),
#     (76, "FDUSER6", 's', 8),
#     (14, "PLANELOC", 'i', 1),# unused
#     ((379, 378, 380, 381), "FDF1OBSMID", 'f', 1),# unknown
#     ((243, 111, 372, 373), "FDF1LB", 'f', 1),# unused
#     ((375, 374, 376, 377), "FDF1GB", 'f', 1),# unused
#     ((383, 382, 384, 385), "FDF1GOFF", 'f', 1),# unused
#     (106, "QUADFLAG", metadata.ExperimentalCollectionMode, 1)

nmrpipe_header_format = [
    (0, "MAGIC", "f", 1),  # should be 0.0
    (1, "FLTFORMAT", "f", 1),  # 4008636160.000000
    (2, "FLTORDER", "f", 1),  # constant equal to 2.345 if read with correct byte order
    (221, "TRANSPOSED", "?", 1),  # transposed T/F
    (9, "DIMCOUNT", "i", 1),  # number of dimensions
    (57, "PIPEFLAG", "?", 1),  # whether data is in stream T/F
    (75, "PIPECOUNT", "i", 1),  # number of functions in pipe
    (443, "SLICECOUNT0", "i", 1),  # number of slices in stream
    (446, "SLICECOUNT1", "i", 1),  # unknown
    (442, "FILECOUNT", "i", 1),  # number of files in complete data
    (447, "CUBEFLAG", "?", 1),  # unknown
    (77, "FIRSTPLANE", "i", 1),  # index of first z-plane in partition
    (78, "LASTPLANE", "i", 1),  # index of last z-plane in partition
    (65, "PARTITION", "i", 1),  # number of partitions
    (296, "YEAR", "f", 1),
    (294, "MONTH", "f", 1),
    (295, "DAY", "f", 1),
    (283, "HOURS", "f", 1),
    (284, "MINS", "f", 1),
    (285, "SECS", "f", 1),
    (135, "MCFLAG", "?", 1),  # magnitude calculation performed T/F
    (153, "NOISE", "f", 1),  # RMS noise estimate
    (180, "RANK", "f", 1),  # estimate of matrix rank
    (157, "TEMPERATURE", "f", 1),  # sample temperature ºC
    (158, "PRESSURE", "f", 1),  # sample pressure
    (399, "2DVIRGIN", "?", 1),  # whether data has been altered
    (199, "TAU", "f", 1),  # parameter for spectrum series
    (
        256,
        "2DPHASE",
        metadatatypes.DigitizationStrategy,
        1,
    ),  # digitization strategy: 0: magnitude, 1: tppi, 2: states, 3: image, 4: array
    ((24, 25, 26, 27), "DIMORDER", "i", 1),  # 2
    (
        (55, 56, 51, 54),
        "QUADFLAG",
        metadatatypes.ExperimentalCollectionMode,
        1,
    ),  # data type code
    ((229, 100, 11, 29), "SW", "f", 1),  # sweepwidth (Hz)
    ((475, 64, 476, 477), "AQSIGN", "i", 1),  # sign adjustment for FT
    ((222, 220, 13, 31), "FTFLAG", metadatatypes.Domain, 1),  # 0: time, 1: frequency
    ((387, 386, 388, 389), "TDSIZE", "i", 1),  # original time-domain size
    ((98, 96, 200, 201), "FTSIZE", "i", 1),  # size when FT was performed
    ((99, 219, 15, 32), "SIZE", "i", 1),  # size of each dimension
    ((18, 16, 20, 22), "LABEL", "s", 8),  # axis label
    ((218, 119, 10, 28), "OBS", "f", 1),  # observe frequency (MHz)
    ((80, 79, 81, 82), "CENTER", "i", 1),  # index of zero frequency point
    ((481, 480, 482, 483), "OFFPPM", "f", 1),  # offset for alignment (ppm)
    ((67, 66, 68, 69), "CAR", "f", 1),  # carrier position (ppm)
    ((245, 109, 60, 62), "P0", "f", 1),  # zeroth order phase
    ((246, 110, 61, 63), "P1", "f", 1),  # first order phase
    ((249, 101, 12, 30), "ORIG", "f", 1),  # frequency of last point (Hz)
    ((428, 95, 50, 53), "APOD", "i", 1),  # current valid time-domain size (pts)
    ((420, 415, 401, 406), "APODQ1", "f", 1),  # apodization parameter 1
    ((421, 416, 402, 407), "APODQ2", "f", 1),  # apodization parameter 2
    ((422, 417, 403, 408), "APODQ3", "f", 1),  # apodization parameter 3
    ((423, 418, 404, 409), "C1", "f", 1),  # scale of first point minus 1
    ((414, 413, 400, 405), "APODCODE", "f", 1),  # apodization function used
    ((437, 108, 438, 439), "ZF", "i", 1),  # negative zero fill size
    ((259, 257, 261, 263), "X1", "i", 1),  # extraction region start (pts)
    ((260, 258, 262, 264), "XN", "i", 1),  # extraction region end (pts)
    (
        (234, 152, 58, 59),
        "UNITS",
        metadatatypes.Units,
        1,
    ),  # 0: ?, 1: sec, 2: Hz, 3: ppm, 4: pts
]


def guess_nucleus(spectral_frequency, name):
    # determine nucleus for dimension by searching name for isotope name
    matched_nuclei = {}
    for idx, n in enumerate(name):
        m = re.search(r"(?P<atomic_number>\d+)(?P<element_symbol>\w+)", n)
        m = m or re.search(r"(?P<atomic_number>\d+)(?P<element_symbol>\w+)", n)
        if not m:
            continue
        atomic_number = int(m.group("atomic_number"))
        element_symbol = m.group("element_symbol").title()
        if (element_symbol, atomic_number) in physical_data.ISOTOPES:
            iso = physical_data.ISOTOPES[(element_symbol, atomic_number)]
            matched_nuclei[idx] = iso

    # find potential matches for remaining dimensions by comparing the ratio
    # of observe frequences to raitos of known gyromagnetic ratios. if the
    # ratio includes a previously matched nucleus, restrict the options using
    # that information
    potential_matches = {}
    for (i_f_0, f_0), (i_f_1, f_1) in itertools.combinations(
        enumerate(spectral_frequency),
        2,
    ):
        x = abs((f_0 + EPS) / (f_1 + EPS))
        for (i_0, i_1), r in physical_data.gyromagnetic_ratio_ratios.items():
            if abs((x - r) / x) > EPS:
                continue
            if (
                i_f_0 in matched_nuclei and i_0 == matched_nuclei[i_f_0]
            ) or i_f_0 not in matched_nuclei:
                potential_matches[i_f_1] = [*potential_matches.get(i_f_1, []), i_1]

    # sort potential matches according to preference order and choose the best option
    for i in range(len(name)):
        if i in matched_nuclei or i not in potential_matches:
            continue
        e = sorted(
            potential_matches[i],
            key=lambda iso: physical_data.isotope_preference.get(iso.isotuple, 1e3),
        )
        matched_nuclei[i] = e[0]

    return matched_nuclei


nmrpipe_byte_order_constant = 2.345
nmrpipe_header_size = 512


def read_nmrpipe_header(path):
    path = Path(path)
    with path.open("rb") as f:
        header = f.read(4 * nmrpipe_header_size)
    header_numeric = np.frombuffer(header, np.float32)
    if np.isclose(header_numeric[2], nmrpipe_byte_order_constant):
        pass
    else:
        header_numeric = header_numeric.byteswap()

    metadata = {}
    for _pos, name, dtype, size in nmrpipe_header_format:
        pos = (_pos,) if isinstance(_pos, int) else _pos
        metadata[name] = []
        for i in pos:
            if dtype == "s":
                raw_value = struct.unpack(
                    str(size) + "s",
                    header[4 * i : 4 * i + size],
                )[0]
                metadata[name] = raw_value.rstrip(b"\x00").decode("ascii")
            elif dtype == "f":
                metadata[name].append(header_numeric[i])
            elif dtype == "i":
                metadata[name].append(int(np.round(header_numeric[i])))
            elif dtype == "?":  # boolean
                metadata[name].append(header_numeric[i] > 0.5)  # noqa: PLR2004
            elif isinstance(dtype, type) and issubclass(dtype, Enum):
                metadata[name].append(dtype(1 + int(np.round(header_numeric[i]))))
            else:
                msg = ("header element description does not match known types",)
                raise ValueError(msg)
        if len(pos) == 1:
            metadata[name] = metadata[name][0]
    print(metadata)

    # guessed_nuclei = guess_nucleus(
    #     spectral_frequency=header_info["OBS"][: header_info["DIMCOUNT"]],
    #     name=header_info["LABEL"][: header_info["DIMCOUNT"]],
    # )

    # dim_order = header_info["DIMORDER"]
    # # dim_order[0], dim_order[1] = dim_order[1], dim_order[0]

    # dimensions = []
    # for dim in range(1, header_info["DIMCOUNT"] + 1):
    #     dim = dim_order.index(dim)
    #     aqsign = header_info["AQSIGN"][dim]
    #     dimensions.append(
    #         metadata.DimInfo(
    #             first_scale_point=header_info["C1"][dim] + 1.0,
    #             nucleus=guessed_nuclei.get(dim, None),
    #             sweep_width=header_info["SW"][dim],
    #             carrier=header_info["CAR"][dim],
    #             size=header_info["SIZE"][dim],
    #             spectral_frequency=header_info["OBS"][dim],
    #             analysis_domain=header_info["FTFLAG"][dim],
    #             dimension=header_info["DIMCOUNT"],
    #             name=header_info["LABEL"][dim],
    #             phase_0=header_info["P0"][dim],
    #             phase_1=header_info["P1"][dim],
    #             sign_alternation=aqsign in [1, 2, 17, 18],
    #             imaginaries_negation=aqsign in [16, 17, 18],
    #             collection_mode=header_info["QUADFLAG"][dim],
    #         )
    #     )

    # # byte_order
    # # dtype = float32
    # #

    # data = np.fromfile(
    #     file=path,
    #     dtype=np.dtype(byte_order_format + "f"),
    #     offset=nmrpipe_header_size * 4,
    # )

    # return dimensions, data


# test_path = "/home/nmrbox/jcourtney/Desktop/old/nih/gb3/test.fid"
# read_nmrpipe_header(test_path)
# # dim_info, data =
#
# #%%
#
# data_shape = []
# if dim_info[0].collection_mode == metadatatypes.ExperimentalCollectionMode.COMPLEX:
#     data_shape.append(2)
# data_shape.append(dim_info[0].size)
# for i in range(1, len(dim_info)):
#     if dim_info[i].collection_mode == metadatatypes.ExperimentalCollectionMode.COMPLEX:
#         data_shape.append(dim_info[i].size // 2)
#         data_shape.append(2)
#     else:
#         data_shape.append(dim_info[i].size)
#
#
# import nmrglue as ng
#
# dic, data = ng.pipe.read(test_path)
# udic = ng.pipe.guess_udic(dic, data)
# print(udic)
# print(dim_info)
# print(data.shape)
#
# #%%
#
# data_shape = [340 // 2, 2, 2, 1676]
# data = data.reshape(data_shape)
# data = data[:, :, 0, :] - 1j * data[:, :, 1, :]
# data = data[:, :, 72:]
# data = np.fft.fftshift(np.fft.fft(data, axis=2), axes=2)
# data = data.real
# data = data[:, 0, :] + 1j * data[:, 1, :]
# data = np.fft.fft(data, axis=0)
# data = data[:, : data.shape[1] // 2]
#
# import matplotlib.pyplot as plt
#
# mag = 10 * np.median(np.abs(data - np.median(data)))
# fig = plt.figure(dpi=300)
# ax = fig.add_subplot(1, 1, 1)
# levels = [-mag * 2.0**i for i in range(0, 5)][::-1] + [
#     mag * 2.0**i for i in range(0, 5)
# ]
# ax.contour(data[::-1], levels=levels, linewidths=0.2, colors="k")
# ax.set_aspect(5.0)
#
# plt.show()
# plt.close()
#
#
# #%%
#
# import numpy as np
# import torch
#
# direct_dims = 2
# size = [11, 2, 13, 2]
# tensor = torch.empty(size[::-1])
# tensor.to_sparse(len(size) - direct_dims)
#
# nnz = 3
# indices = torch.stack(
#     [torch.randint(0, size[-(i + 1)], (nnz,)) for i in range(len(size) - direct_dims)],
# )
# a = torch.sparse_coo_tensor(
#     indices=indices,
#     values=torch.empty([nnz] + size[:direct_dims][::-1]),
#     size=size[::-1],
# )
# # print(f'{a!r}')
# print(f"size: {a.size()}")
# print(a._indices().size(), a._values().size())
# print()
# print(f"num sparse indices: {a._indices().ndim}")
# print(f"nonzero slices: {a._indices().size(-1)}")
# print(f"dense slice size: {a._values().size()[1:]}")
