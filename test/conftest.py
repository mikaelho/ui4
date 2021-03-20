from pytest import fixture

from ui4.core import Anchors
from ui4.core import Core

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
        left = Anchors.anchorprop('left')
        center_x = Anchors.anchorprop('center_x')
        center_y = Anchors.anchorprop('center_y')
        center = Anchors.anchorprops('center_x', 'center_y')
        top_left = Anchors.anchordock('top_left')
        
    yield AnchorCore
