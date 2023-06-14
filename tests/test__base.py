import pytest
from pytest_check import check

from connvert._base import MultitonMeta


def test_MultitonMeta_multitonicity():
    class A(metaclass=MultitonMeta):
        def __init__(self, a, /, b, *args, c, d="d", **kwargs):
            pass

    with check:
        a_0 = A(1, 2, c=3, d=4)
        a_1 = A(1, b=2, c=3, d=4)
        assert a_0 == a_1
        a_2 = A(1, 2, c=3)
        a_3 = A(1, b=2, c=3)
        a_4 = A(1, b=2, c=3)
        assert a_2 == a_3
        assert a_3 == a_4
        a_5 = A(1, 2, -1, c=3, d=4)
        a_6 = A(1, 2, -1, c=3)
        a_7 = A(1, 2, c=3, d=4, e=0)
        a_8 = A(1, b=2, c=3, d=4, e=0)
        assert a_7 == a_8
        a_9 = A(1, 2, c=3, e=0)
        a_10 = A(1, b=2, c=3, e=0)
        assert a_9 == a_10
        a_11 = A(1, 2, -1, c=3, d=4, e=0)
        a_12 = A(1, 2, -1, c=3, e=0)

        snowflakes = [a_0, a_2, a_5, a_6, a_7, a_9, a_11, a_12]
        assert len(set(snowflakes)) == len(snowflakes)
