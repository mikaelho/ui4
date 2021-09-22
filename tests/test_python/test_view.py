import pytest

from ui4 import View
from ui4 import portrait


@pytest.mark.usefixtures("constraints_class")
class TestView:

    def test_composite_properties(self):
        view1 = View()
        view2 = View(center=view1.center, size=(100,view1.height))
        view3 = View(position=view1.position)
        view4 = View(size=view1.size)
        view5 = View(frame=view1.frame)

        assert self.constraints(view2) == 'centerX=id1.centerX;centerY=id1.centerY;width=100;height=id1.height'
        assert self.constraints(view3) == 'left=id1.left;top=id1.top'
        assert self.constraints(view4) == 'width=id1.width;height=id1.height'
        assert self.constraints(view5) == 'left=id1.left;top=id1.top;width=id1.width;height=id1.height'

    def test_anchors_dock(self):
        view1 = View()
        view2 = View()
        view3 = View()
        view4 = View()
        view5 = View()

        view1.dock = view2.top_left
        assert view1.parent == view2
        assert self.constraints(view1) == 'top=id2.top;left=id2.left'

        view4.dock = view1.top
        view4.height = 100
        assert self.constraints(view4) == 'top=id1.top;left=id1.left;right=id1.right;height=100'

        view2.dock = view3.top + 16
        assert self.constraints(view2) == 'top=id3.top+16;left=id3.left+16;right=id3.right-16'

        view4.parent = view1
        view3.dock = view4.below
        assert view3.parent == view1
        assert self.constraints(view3) == 'top=id4.bottom;centerX=id4.centerX;width=id4.width'

        view5.dock = view4.above + 4
        assert self.constraints(view5) == 'bottom=id4.top-4;centerX=id4.centerX;width=id4.width'

    def test_anchors_docking_center(self):
        view1 = View()
        view2 = View()

        view2.dock = view1.center
        assert view2.parent == view1
        assert self.constraints(view2) == 'centerX=id1.centerX;centerY=id1.centerY'

    def test_anchors_fit_both(self):
        view1 = View()
        view2 = View()

        view1.fit = 'both'
        assert self.constraints(view1) == 'width=id1.fitWidth+0;height=id1.fitHeight+0'

        view2.fit = True
        assert self.constraints(view2) == 'width=id2.fitWidth+0;height=id2.fitHeight+0'

    def test_anchors_fit_width(self):
        view1 = View()

        view1.fit = 'width'
        assert self.constraints(view1) == 'width=id1.fitWidth+0'

    def test_anchors_fit_extra(self):
        view1 = View()

        view1.fit = 16
        assert self.constraints(view1) == 'width=id1.fitWidth+16;height=id1.fitHeight+16'

    def test_anchors_conditions(self):
        view1 = View()
        view2 = View()
        view3 = View()

        view2.left = portrait & view1.left
        assert self.constraints(view2) == 'portrait?left=id1.left'

        view3.left = portrait(view1) & view1.left
        assert self.constraints(view3) == 'portrait(id1)?left=id1.left'


    def test_anchors_multiple(self):
        view1 = View()
        view2 = View()

        view2.left = view1.right, portrait & view1.left

        assert self.constraints(view2) == 'left=id1.right;portrait?left=id1.left'

    def test_properties__font(self):
        view = View()
        view.font = 'Roboto', 'Arial', 'Verdana'

        assert view._render_props() == {
            'style': 'font-family:Roboto,Arial,Verdana',
        }
