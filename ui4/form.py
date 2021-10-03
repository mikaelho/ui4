from functools import partial
from typing import Any

# from pydantic import BaseModel

from ui4.label import Label
from ui4.switch import Switch
from ui4.textfield import TextField
from ui4.view import View


def _create_textfield(field_type, parent, value, content_hint):
    return TextField(parent=parent, field_type=field_type, value=value, placeholder=content_hint)


def _create_switch(parent, value, content_hint):
    return Switch(parent=parent, on=value)


class Form(View):

    # Define all field type mappings that are not the default TextField.NORMAL
    from_data_type_to_form_view = {
        # Standard library types
        'int': partial(_create_textfield, TextField.NUMBER),
        'float': partial(_create_textfield, TextField.NUMBER),
        'Decimal': partial(_create_textfield, TextField.NUMBER),
        'bool': _create_switch,
        'datetime': partial(_create_textfield, TextField.DATETIME),
        'date': partial(_create_textfield, TextField.DATE),
        'time': partial(_create_textfield, TextField.TIME),

        # pydantic types
        'ConstrainedInt': partial(_create_textfield, TextField.NUMBER),
        'NegativeInt': partial(_create_textfield, TextField.NUMBER),
        'PositiveInt': partial(_create_textfield, TextField.NUMBER),
        'StrictInt': partial(_create_textfield, TextField.NUMBER),
        'ConstrainedFloat': partial(_create_textfield, TextField.NUMBER),
        'NegativeFloat': partial(_create_textfield, TextField.NUMBER),
        'PositiveFloat': partial(_create_textfield, TextField.NUMBER),
        'StrictFloat': partial(_create_textfield, TextField.NUMBER),
        'ConstrainedDecimal': partial(_create_textfield, TextField.NUMBER),
        'StrictBool': _create_switch,
        'EmailStr': partial(_create_textfield, TextField.EMAIL),
        'PastDate': partial(_create_textfield, TextField.DATE),
        'FutureDate': partial(_create_textfield, TextField.DATE),
    }

    def __init__(self, data: Any, **kwargs):
        super().__init__()
        if type(data) is type:
            self.model = data
            if hasattr(self.model, '__fields__'):
                self.data = self.model.construct()
            else:
                self.data = self.model()
        else:
            self.model = type(data)
            self.data = data
        self.views = {}
        self._create_form()
        self.apply(kwargs)

    @classmethod
    def types_with_specific_fields(cls):
        return tuple(cls.from_data_type_to_form_view.keys())

    def _create_form(self):

        for i, (attribute, attribute_type) in enumerate(self.model.__annotations__.items()):
            label_text, view = self._create_view(attribute, attribute_type)

            top_anchor = i == 0 and self.top or list(self.views.values())[-1].bottom
            label = Label(parent=self, text=label, left=self.left, top=top_anchor)
            view.left = label.right
            view.center_y = label.center_y
            self.views[attribute] = view

    def _create_view(self, attribute: str, attribute_type: Any):
        label_text = attribute.replace('_', ' ').capitalize()
        content_hint = ''

        # pydantic support
        if hasattr(self.model, '__fields__'):
            field = self.data.__fields__.get(attribute)
            label_text = field.title or label_text
            content_hint = getattr(field.field_info, 'description') or ''

        create_view_func = self.from_data_type_to_form_view.get(attribute_type.__name__)
        if not create_view_func:
            create_view_func = partial(_create_textfield, TextField.NORMAL)

        view = create_view_func(self, getattr(self.data, attribute), content_hint)

        return label_text, view
