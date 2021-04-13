from pytest import fixture

from ui4.core import Anchors
from ui4.core import Core
from ui4.core import Events
from ui4.core import Identity
from ui4.core import Props


@fixture(autouse=True)
def clean_state():
    Core._clean_state()


@fixture
def is_view_id():
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
    yield IsViewID()
    
    
@fixture
def anchor_view():
    class AnchorCore(Core):
        top = Anchors.anchorprop('top')
        bottom = Anchors.anchorprop('bottom')
        left = Anchors.anchorprop('left')
        right = Anchors.anchorprop('right')
        width = Anchors.anchorprop('width')
        height = Anchors.anchorprop('height')
        center_x = Anchors.anchorprop('center_x')
        center_y = Anchors.anchorprop('center_y')
        center = Anchors.anchorprops('center_x', 'center_y')
        top_left = Anchors.anchordock('top_left')
        
    yield AnchorCore

