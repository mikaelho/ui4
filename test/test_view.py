from ui4 import View
from ui4.core import ConstraintAnchor


class TestView:

    def test_composite_properties(self):
        view1 = View()
        view2 = View(
            center=view1.center,
            size=(100,view1.height)
        )
        view3 = View(
            position=view1.position,
        )
        view4 = View(
            size=view1.size,
        )
        view5 = View(
            frame=view1.frame,
        )

        assert view2._render_anchors()['ui4'] == 'centerX=id1.centerX;centerY=id1.centerY;width=100;height=id1.height'
        assert view3._render_anchors()['ui4'] == 'left=id1.left;top=id1.top'
        assert view4._render_anchors()['ui4'] == 'width=id1.width;height=id1.height'
        assert view5._render_anchors()['ui4'] == 'left=id1.left;top=id1.top;width=id1.width;height=id1.height'

    def test_anchors_dock(self, anchor_view):
        view1 = View()
        view2 = View()
        view3 = View()
        view4 = View()
        view5 = View()

        view1.dock = view2.top_left
        assert view1.parent == view2
        assert view1._render_anchors()['ui4'] == 'top=id2.top;left=id2.left'

        view2.dock = view3.bottom_left + 16
        assert view2._render_anchors()['ui4'] == 'bottom=id3.bottom-16;left=id3.left+16'

        view4.parent = view1
        view3.dock = view4.below
        assert view3.parent == view1
        assert view3._render_anchors()['ui4'] == 'top=id4.bottom;centerX=id4.centerX;width=id4.width'

        view5.dock = view4.above + 4
        assert view5._render_anchors()['ui4'] == 'bottom=id4.top-4;centerX=id4.centerX;width=id4.width'
