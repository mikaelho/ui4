from ui4 import Switch


def test_label_layout(get_app, views, driver, expect, js_style):
    def setup(root):
        views.switch1 = Switch(dock=root.top_center, on=True)
        views.switch2 = Switch(dock=views.switch1.below)

        @views.switch1
        def on_change(view):
            views.switch2.toggle()

    with get_app(setup):
        assert not views.switch2.on
        assert js_style(views.switch2.id, 'backgroundColor') == views.switch2.style.current_theme.inactive.css_rgb

        driver.find_element_by_id(views.switch1.id).click()

        assert expect(lambda: views.switch2.on)
        assert expect(
            lambda: js_style(views.switch2.id, 'backgroundColor') == views.switch2.style.current_theme.primary.css_rgb
        )
