from functools import wraps

from ui4.utils import decorator_argument_wrapper


def test_decorator_arguments_wrapper__no_change_in_regular_use():

    @decorator_argument_wrapper
    def add_one(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            return value + 1
        return wrapper

    @add_one
    def return_five():
        return 5

    assert return_five() == 6
    assert return_five.__name__ == 'return_five'


def test_decorator_arguments_wrapper__with_arguments():

    @decorator_argument_wrapper
    def add_some(func, some=1):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            return value + some
        return wrapper

    @add_some
    def return_five():
        return 5

    assert return_five() == 6

    @add_some(2)
    def return_six():
        return 6

    assert return_six() == 8

    @add_some(some=3)
    def return_seven():
        return 7

    assert return_seven() == 10


def test_decorator_arguments_wrapper__in_a_method():

    @decorator_argument_wrapper
    def add_some(func, some=1):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            return value + some
        return wrapper

    class Adder:

        @add_some
        def return_five(self):
            return 5

        @add_some(3)
        def return_seven(self):
            return 7

    adder = Adder()

    assert adder.return_five() == 6
    assert adder.return_seven() == 10
    assert adder.return_five.__name__ == 'return_five'
