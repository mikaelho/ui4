import inspect

import pytest

from ui4 import ge
from ui4 import high
from ui4 import le
from ui4 import maximum
from ui4 import minimum
from ui4 import wide

from ui4.animation import _animation_context
from ui4.animation import animation
from ui4.animation import AnimationSpec
from ui4.core import Anchor
from ui4.core import AnchorContainer
from ui4.core import Core
from ui4.core import Events


class TestIdentity:

    def test_identity(self, is_view_id):
        view1 = Core()
        view2 = Core()

        class NotView:
            id = 'foobar'
    
        assert NotView().id != is_view_id
        assert view1.id == is_view_id
        assert view2.id == is_view_id
        assert view1.id != view2.id

        assert Core.get_view(view2.id) == view2


class TestHierarchy:

    def test_hierarchy(self):
        view1 = Core()
        view2 = Core(parent=view1)
    
        assert view2 in view1.children
    
        view3 = Core()
    
        with pytest.raises(AttributeError):
            view1.children.append(view3)
    
        view2.parent = view3
    
        assert view2 not in view1.children
    
        view4 = Core(children=[view1, view2])
    
        assert view1 in view4.children
        assert view2 in view4.children
        assert not view3.children
    
    def test_container_hierarchy(self):
        parent = Core(
            container=Core()
        )
        child = Core(parent=parent)
        
        assert child.parent == parent
        assert child._parent == parent.container
        assert parent.children == (child,)
        assert parent._children == [parent.container]
    

class TestRender:
    
    def test_renderer_registration(self):
        view = Core()
        
        assert len(view._renderers) == 3
    
    def test_container_rendering(self):
        parent = Core(
            container=Core()
        )
        child = Core(parent=parent)
    
        render_result = parent._render()
        for view_id in (parent.id, parent.container.id, child.id):
            assert view_id in render_result
    
    
class TestAnchor:

    def test_anchor_identity(self):
        view1 = Core()
        view2 = Core()

        a = Anchor(target_view=view1, target_attribute='left')
        b = Anchor(target_view=view1, target_attribute='left')

        assert a == b

        a = Anchor(target_view=view1, target_attribute='left')
        b = Anchor(target_view=view2, target_attribute='left')

        assert a != b

        a = Anchor(target_view=view1, target_attribute='left', source_view=view2, source_attribute='right')
        b = Anchor(target_view=view1, target_attribute='left', source_view=view2, source_attribute='left')

        assert a == b

        a = Anchor(target_view=view1, target_attribute='left')
        b = Anchor(target_view=view1, target_attribute='left', comparison='>')

        assert a != b

        a = Anchor(target_view=view1, target_attribute='left', comparison='>',
                   source_view=view2, source_attribute='right')
        b = Anchor(target_view=view1, target_attribute='left', comparison='>',
                   source_view=view2, source_attribute='right')

        assert a == b

        a = Anchor(target_view=view1, target_attribute='left', comparison='>',
                   source_view=view2, source_attribute='right')
        b = Anchor(target_view=view1, target_attribute='left', comparison='>',
                   source_view=view2, source_attribute='left')

        assert a != b

        a = Anchor(target_view=view1, target_attribute='left', comparison='>',
                   source_view=view2, source_attribute='right')
        b = Anchor(target_view=view1, target_attribute='left', comparison='<',
                   source_view=view2, source_attribute='right')

        assert a != b

    def test_anchor_as_dict(self, is_view_id):
        view = Core()
        anchor = Anchor(target_view=view, target_attribute='bar', modifier=16)

        assert anchor.as_dict() == {
            'a0': 'bar',
            'a5': 16
        }
        
    def test_anchor_as_json(self):
        view = Core()
        animation = AnimationSpec(
            duration=0.5,
            ease='ease-in',
            start_delay=1,
            end_delay=2,
            direction='alternate',
            iterations=3,
        )
        anchor = Anchor(
            target_view=view, 
            target_attribute='bar', 
            multiplier=2,
            animation=animation,
        )
        
        assert (
            anchor.as_json() == 
            '{"a0":"bar","a4":2,'
            '"a7":0.5,"a8":"ease-in","a9":1,"a10":2,"a11":"alternate","a12":3}'
        )

    def test_anchor_multipliers_and_modifiers(self):
        anchor = Anchor()
        anchor * 12 / 4 + 3 - 1

        assert anchor.multiplier == 3
        assert anchor.modifier == 2


class TestAnchorProperties:

    def test_anchors_basic(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        assert view1._constraints == set()

        view1.center_x = view2.left

        anchor = view1._constraints.pop()
        assert type(anchor) == Anchor
        assert anchor.target_view == view1
        assert anchor.target_attribute == 'center_x'
        assert anchor.comparison == '='
        assert anchor.source_view == view2
        assert anchor.source_attribute == 'left'
        
    def test_anchors_combo(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()

        view2.center = view1.center

        anchor_x = Anchor(target_view=view2, target_attribute='center_x', comparison='=',
                          source_view=view1, source_attribute='center_x')
        anchor_y = Anchor(target_view=view2, target_attribute='center_y', comparison='=',
                          source_view=view1, source_attribute='center_y')
        assert view2._constraints == {anchor_x, anchor_y}

    def test_anchors_dock(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        
        view2.dock = view1.top_left
        assert view2.parent == view1
        
        top_anchor = Anchor(target_view=view2, target_attribute='top', comparison='=',
                            source_view=view1, source_attribute='top')
        left_anchor = Anchor(target_view=view2, target_attribute='left', comparison='=',
                             source_view=view1, source_attribute='left')
        assert view2._constraints == {top_anchor, left_anchor}
        
    def test_anchors_center(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        
        view2.dock = view1.center
        assert view2.parent == view1
        
    def test_anchors_gt(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        view4 = anchor_view()

        anchor = Anchor(target_view=view2, target_attribute='left', comparison='>',
                        source_view=view1, source_attribute='center_x')
    
        view2.left.gt(view1.center_x)

        assert view2._constraints == {anchor}

        view3.left = ge(view1.center_x)

        anchor.target_view = view3
        assert view3._constraints == {anchor}

        view4.left > view1.center_x  # noqa: Optional syntactic sugar (or poison)

        anchor.target_view = view4
        assert view4._constraints == {anchor}

    def test_anchors_lt(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        view4 = anchor_view()

        anchor = Anchor(
            target_view=view2, target_attribute='left', 
            comparison='<',
            source_view=view1, source_attribute='center_x')

        view2.left.lt(view1.center_x)

        assert view2._constraints == {anchor}

        view3.left = le(view1.center_x)

        anchor.target_view = view3
        assert view3._constraints == {anchor}

        view4.left < view1.center_x  # noqa: Optional syntactic sugar (or poison)

        anchor.target_view = view4
        assert view4._constraints == {anchor}

    def test_anchors_autorelease(self, anchor_view):
        view = anchor_view()
        
        view.left = 100
        view.width = 200
        
        locked = {anchor.target_attribute for anchor in view._constraints}
        assert locked == {'left', 'width'}
        
        view.right = 300
        
        locked = {anchor.target_attribute for anchor in view._constraints}
        assert locked == {'right', 'width'}
        
        view.top = 400
        view.bottom = 500
        
        locked = {anchor.target_attribute for anchor in view._constraints}
        assert locked == {'right', 'width', 'top', 'bottom'}
        
        view.center_y = 600
        locked = {anchor.target_attribute for anchor in view._constraints}
        assert locked == {'right', 'width', 'top', 'center_y'}


class TestExtendedAnchors:
        
    def test_maximum(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        
        view1.width = view2.height
        
        view1.width = maximum(view2.width, view3.width)
        
        assert len(view1._constraints) == 1
        anchor = list(view1._constraints)[0]
        assert type(anchor) == AnchorContainer
        assert anchor.as_dict() == {
            'a0': 'width',
            'a1': '=',
            'key': 'max',
            'list': [
                {'a2': 'id2', 'a3': 'width'},
                {'a2': 'id3', 'a3': 'width'}
            ]
        }
        
        view1.height.maximum(view2.height, view3.height).lt(300)
        assert len(view1._constraints) == 3
        for anchor in view1._constraints:
            if type(anchor) is Anchor:
                assert anchor.comparison == '<'

    def test_minimum(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        
        view1.width = view2.height
        
        view1.width = minimum(view2.width, view3.width)
        
        assert len(view1._constraints) == 1
        anchor = list(view1._constraints)[0]
        assert type(anchor) == AnchorContainer
        assert anchor.as_dict() == {
            'a0': 'width',
            'a1': '=',
            'key': 'min',
            'list': [
                {'a2': 'id2', 'a3': 'width'},
                {'a2': 'id3', 'a3': 'width'}
            ]
        }
        
        view1.height.minimum(view2.height, view3.height).ge(300)
        assert len(view1._constraints) == 3
        for anchor in view1._constraints:
            if type(anchor) is Anchor:
                assert anchor.comparison == '>'
                
    def test_container_with_animation(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        
        with animation():
            view1.width = minimum(view2.width, view2.height)
            
        anchor = list(view1._constraints)[0]
        assert anchor.as_dict() == {
            'a0': 'width',
            'a1': '=',
            'key': 'min',
            'list': [
                {'a2': 'id2', 'a3': 'width'},
                {'a2': 'id2', 'a3': 'height'}
            ],
            'a7': 0.3,
        } 

    def test_high_and_wide(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        
        view1.width = (
            high(view2.width),
            wide(view3.height),
        )
        
        assert len(view1._constraints) == 2
        for anchor in view1._constraints:
            assert anchor.target_attribute == 'width'
            assert (
                anchor.source_attribute == 'width' and anchor.require == 'high'
            ) or (
                anchor.source_attribute == 'height' and anchor.require == 'wide'
            )
            
            assert anchor.as_dict()['a6'] in ('high', 'wide')
            
    
class TestEvents:
    
    def test_event_handler_decorator(self):    
        view = Core()
        
        with pytest.raises(ValueError):
            @view
            def on_nonexistent_event(_):
                pass
                
        @view
        def on_click(_):
            pass
            
        assert inspect.isfunction(view.on_click)  # noqa: Too clever for PyCharm
        assert view._render_events() == {
            'hx-post': '/event',
            'hx-trigger': 'click'
        }

    def test_get_roots(self):
        view1 = Core()
        view2 = Core(parent=view1)
        view3 = Core(parent=view2)
        view4 = Core(parent=view1)
        
        assert Core._get_roots() == set()

        view4._mark_dirty()
        assert Core._get_roots() == {view4}

        view3._mark_dirty()
        assert Core._get_roots() == {view3, view4}

        view2._mark_dirty()
        assert Core._get_roots() == {view2, view4}

        view1._mark_dirty()
        assert Core._get_roots() == {view1}

    def test_event_generator(self):
        view = Core()
        assert view._animation_id is None
    
        @view
        def on_click(data):
            data.value = 1
            yield
            data.value = 2

        # First click
        update = view._process_event('click', view)

        assert view.value == 1
        assert len(Events._animation_generators) == 1

        # Return after animation complete
        animation_id = next(iter(Events._animation_generators.keys()))
        view._process_event_loop(animation_id)

        assert view.value == 2
        assert len(Events._animation_generators) == 0
    
        # Restart
        view._process_event('click', view)
        assert view.value == 1
        animation_id = next(iter(Events._animation_generators.keys()))
        view._process_event_loop(animation_id)
        assert view.value == 2




class TestStyleProperties:
        
    def test_base_setter_and_render(self):
        view = Core()
        
        assert view not in Core._get_dirties()
        
        view._set_css_property(
            'text_color',
            (1, 1, 1, 1),
            'color', 
            'rgba(255,255,255,255)',
        )
        
        assert view in Core._get_dirties()

        rendered = view._render_props()

        assert rendered == {
            'style': 'color:rgba(255,255,255,255)',
        }
        
    def test_animated_css_properties(self):
        view = Core()
        
        with animation():
            view._set_css_property(
                'corner_radius',
                '50%',
                'border-radius', 
                '50%',
            )
        with animation(
            duration=2.0,
            ease='ease-func',
            direction='alternate',
            iterations='forever',
            start_delay=1,
            end_delay=2,
        ):
            view._set_css_property(
                'alpha',
                0.5,
                'opacity', 
                '50%',
            )
        view._animation_id = 'abc123'
            
        rendered = view._render_props()
        
        assert rendered == {
            'ui4css':
                '[{"key":"border-radius","value":"50%","animation":{"a7":0.3}},'
                '{"key":"opacity","value":"50%",'
                '"animation":{"a7":2.0,"a8":"ease-func","a9":1,"a10":2,"a11":"alternate","a12":Infinity}}]',
            'ui4anim': 'abc123',
        }

    def test_properties__generic(self):
        Core.corner_radius = Core._css_plain_prop('corner_radius', 'border-radius')
        
        view = Core()
        view.corner_radius = '25%'
        assert view._properties['corner_radius'] == '25%'
        assert view._css_properties['border-radius'] == '25%'
        assert view.corner_radius == '25%'
        
        view.corner_radius = 8
        assert view._properties['corner_radius'] == 8
        assert view._css_properties['border-radius'] == '8px'
        assert view.corner_radius == 8

    def test_properties__color(self):
        Core.text_color = Core._css_color_prop('text_color', 'color')
        
        view = Core()
        
        view.text_color = 'cyan'
        assert view.text_color.name == 'cyan'
        assert view._css_properties['color'] == 'rgba(0,255,255,255)'

    def test_properties__bool(self):
        Core.bold = Core._css_bool_prop('bold', 'font-weight', 'bold')
        
        view = Core()
        
        view.bold = True
        assert view._css_properties['font-weight'] == 'bold'
        
        view.bold = False
        assert view._css_properties['font-weight'] is None
        
    def test_properties__mapping(self):
        Core.scrollable = Core._css_mapping_prop('scrollable', 'overflow', {
            True: 'auto',
            'horizontal': 'auto hidden',
            'vertical': 'hidden auto',            
        })
        
        view = Core()
        
        view.scrollable = True
        assert view._css_properties['overflow'] == 'auto'
        
        view.scrollable = False
        assert view._css_properties['overflow'] == None

