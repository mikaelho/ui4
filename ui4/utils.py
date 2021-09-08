from functools import wraps
from types import FunctionType
from types import MethodType


def decorator_argument_wrapper(func):
    """
    Decorator for decorating decorators to support optional arguments.

    Resulting decorator works both for functions and methods.
    """
    @wraps(func)
    def new_decorator(*args, **kwargs):
        if not kwargs:
            if len(args) == 1 and callable(args[0]):
                return func(args[0])
        return lambda real_func: func(real_func, *args, **kwargs)

    return new_decorator
