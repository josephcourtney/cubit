import inspect


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

    _instances = {}

    def __call__(cls, *args, **kwargs):
        sig = inspect.signature(cls.__init__)
        bound = sig.bind(None, *args, **kwargs)
        bound.apply_defaults()
        standardized_args = bound.arguments
        standardized_args.pop("self")
        standardized_args |= standardized_args.pop("kwargs", {})
        index = cls, tuple(sorted(standardized_args.items()))
        if index not in cls._instances:
            cls._instances[index] = super().__call__(
                *args,
                **kwargs,
            )
        return cls._instances[index]
