from ui4 import animation
from ui4.prop import prop
from ui4.view import View


class Switch(View):

    def __init__(self, on=False, **kwargs):
        super().__init__()

        self._base_height = 24

        self.width = 40
        self.height = self._base_height

        self._circle = View(
            parent=self,
            width=22,
            height=22,
            top=1,
            corner_radius=11,
            background_color='white',
        )
        self.corner_radius = '50%'
        self.apply(kwargs)

        self._properties['on'] = on
        self._set_state_appearance()

    @prop
    def on(self, *value):
        if not value:
            return self._properties.get('on', False)

        value = value[0]
        if value != self._properties.get('on'):
            self._mark_dirty()
            self._properties['on'] = value
            self._set_state_appearance_animated()

    def toggle(self):
        self.on = not self.on

    def _internal_on_click(self, view):
        self.toggle()
        event_handler = getattr(self, 'on_change', None)
        return event_handler and event_handler(view)

    def _set_state_appearance_animated(self):
        with animation(0.1):
            self._set_state_appearance()

    def _set_state_appearance(self):
        self._circle.left = not self.on and 1 or None
        self._circle.right = self.on and 1 or None
        self.background_color = (
            self.on and self.style.current_theme.primary
            or self.style.current_theme.inactive
        )

    @prop
    def corner_radius(self, *value):
        if not value:
            return super().corner_radius

        value = value[0]
        circle_value = value

        if type(value) is str and value.endswith('%'):
            value = float(value[:-1])/100 * self._base_height
            circle_value = value - 2

        View.corner_radius.fset(self, value)
        self._circle.corner_radius = circle_value
