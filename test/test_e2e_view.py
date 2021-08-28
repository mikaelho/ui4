from ui4 import View


def test_view_basics(get_app, views, js_dimensions):

    def setup(root):
        rootlike = View(parent=root, center=root.center, width=600, height=400)

        views.middle = View(
            parent=rootlike, center=rootlike.center, width=200, height=100)
        views.on_the_left = View(parent=rootlike,
            center_y=views.middle.center_y, right=views.middle.left, left=rootlike.left, height=views.middle.height)
        views.on_the_right = View(parent=rootlike,
            center_y=views.middle.center_y, left=views.middle.right, right=rootlike.right, height=views.middle.height)
        views.above = View(parent=rootlike,
            center_x=views.middle.center_x, bottom=views.middle.top, top=rootlike.top, width=views.middle.width)
        views.below = View(parent=rootlike,
            center_x=views.middle.center_x, top=views.middle.bottom, bottom=rootlike.bottom, width=views.middle.width)

        views._apply(text=True, background_color='darkseagreen')

    with get_app(setup):
        assert js_dimensions(views.middle.id) == (200, 150, 200, 100)
        assert js_dimensions(views.on_the_left.id) == (8, 150, 184, 100)
        assert js_dimensions(views.on_the_right.id) == (408, 150, 184, 100)
        assert js_dimensions(views.above.id) == (200, 8, 200, 134)
        assert js_dimensions(views.below.id) == (200, 258, 200, 134)


def test_docking(get_app, views, js_dimensions):

    def setup(root):
        rootlike = View(parent=root, center=root.center, width=600, height=400)

        views.center = View(dock=rootlike.center)

        views.top_left = View(dock=rootlike.top_left)
        views.top_center = View(dock=rootlike.top_center)
        views.top_right = View(dock=rootlike.top_right)
        views.left_center = View(dock=rootlike.left_center)
        views.right_center = View(dock=rootlike.right_center)
        views.bottom_left = View(dock=rootlike.bottom_left)
        views.bottom_center = View(dock=rootlike.bottom_center)
        views.bottom_right = View(dock=rootlike.bottom_right)

        views.above = View(dock=views.center.above)
        views.below = View(dock=views.center.below)
        views.left_of = View(dock=views.center.left_of)
        views.right_of = View(dock=views.center.right_of)

        views._apply(text=True, width=100, height=50, background_color='darkseagreen')

    with get_app(setup):
        assert js_dimensions(views.center.id) == (250, 175, 100, 50)

        assert js_dimensions(views.top_left.id) == (8, 8, 100, 50)
        assert js_dimensions(views.top_center.id) == (250, 8, 100, 50)
        assert js_dimensions(views.top_right.id) == (492, 8, 100, 50)
        assert js_dimensions(views.left_center.id) == (8, 175, 100, 50)
        assert js_dimensions(views.right_center.id) == (492, 175, 100, 50)
        assert js_dimensions(views.bottom_left.id) == (8, 342, 100, 50)
        assert js_dimensions(views.bottom_center.id) == (250, 342, 100, 50)
        assert js_dimensions(views.bottom_right.id) == (492, 342, 100, 50)

        assert js_dimensions(views.above.id) == (250, 117, 100, 50)
        assert js_dimensions(views.below.id) == (250, 233, 100, 50)
        assert js_dimensions(views.left_of.id) == (142, 175, 100, 50)
        assert js_dimensions(views.right_of.id) == (358, 175, 100, 50)
