import inspect
from fractions import Fraction
from typing import ClassVar, Union

class MultitonMeta(type):
    """MultitonMeta.
    Metaclass that makes the class a multiton keyed on the arguments
        supplied when creating the instance.

    Exmaple Use
    -----------
    class A(metaclass=MultitonMeta):
        def __init__(self, a, /, b, *args, c, d="d", **kwargs):
            pass

    a_0 = A(1, 2, c=3, d=4)
    a_1 = A(1, b=2, c=3, d=4)
    assert a_0 == a_1

    """

    _instances: ClassVar = {}

    def __new__(metacls, name, bases, namespace, key=None):  # noqa: N804
        cls = super().__new__(metacls, name, bases, namespace)
        cls.key = key
        return cls

    def __call__(cls, *args, **kwargs):
        sig = inspect.signature(cls.__init__)
        bound = sig.bind(None, *args, **kwargs)
        bound.apply_defaults()
        standardized_args = bound.arguments
        standardized_args.pop("self")
        standardized_args |= standardized_args.pop("kwargs", {})
        if cls.key is None:
            index = cls, tuple(sorted(standardized_args.items()))
        else:
            index = cls, tuple(sorted([(k, standardized_args[k]) for k in cls.key]))
        if index not in cls._instances:
            cls._instances[index] = super().__call__(
                *args,
                **kwargs,
            )
        return cls._instances[index]


NumberLike = Union[int, float, complex, Fraction]
