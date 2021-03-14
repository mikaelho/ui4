from pytest import fixture


class IsViewID:
    """
    Utility class for checking that a value is a valid view ID.
    """
    def __eq__(self, other):
        if other.startswith('id'):
            try:
                int(other[len('id'):])
                return True
            except:
                return False
        return False

@fixture
def is_view_id():
    yield IsViewID()