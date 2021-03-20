import inspect

import pytest

from ui4 import ge
from ui4 import le
from ui4.core import Anchor
from ui4.core import Core
from ui4.core import Events
from ui4.core import _animation_context
from ui4.core import animation


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

        assert Core.views[view2.id] == view2


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
        
        assert len(view._renderers) == 2
    
    def test_container_rendering(self):
        parent = Core(
            container=Core()
        )
        child = Core(parent=parent)
    
        render_result = parent._render()
        for view_id in (parent.id, parent.container.id, child.id):
            assert view_id in render_result
    
    
class TestAnchor:

    def test_anchor_as_dict(self, is_view_id):
        view = Core()
        anchor = Anchor(target_view=view, target_attribute='bar', modifier=16)

        assert anchor.as_dict() == {
            'a0': 'bar',
            'a5': 16
        }
        
    def test_anchor_as_json(self):
        view = Core()
        anchor = Anchor(
            target_view=view, 
            target_attribute='bar', 
            multiplier=2,
            duration=0.5,
            ease_func='ease-in'
        )
        
        assert (anchor.as_json() == f'{{"a0":"bar","a4":2,"a6":0.5,"a7":"ease-in"}}')

    def test_anchor_multipliers_and_modifiers(self):
        anchor = Anchor()
        anchor * 12 / 4 + 3 - 1

        assert anchor.multiplier == 3
        assert anchor.modifier == 2


class TestAnchorProperties:

    def test_anchors_init(self):
        view = Core()
        assert view.halfgap == 4

    def test_anchors_basic(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        
        empty_constraints = {'=': {}, '>': {}, '<': {}}
        assert view1._constraints == empty_constraints

        view1.center_x = view2.left
        anchor = view1._constraints['=']['center_x'][0]
        assert type(anchor) == Anchor
        assert anchor.target_view == view1
        assert anchor.target_attribute == 'center_x'
        assert anchor.source_view == view2
        assert anchor.source_attribute == 'left'
        
    def test_anchors_combo(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()

        view2.center = view1.center
        
        assert view2._constraints['=']['center_x'][0].source_attribute == 'center_x'
        assert view2._constraints['=']['center_y'][0].source_attribute == 'center_y'

    def test_anchors_dock(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        
        view2.dock = view1.top_left
        assert view2.parent == view1
        
        top_anchor = view2._constraints['=']['top'][0]
        assert top_anchor.source_view == view1
        assert top_anchor.source_attribute == 'top'
        left_anchor = view2._constraints['=']['left'][0]
        assert left_anchor.source_view == view1
        assert left_anchor.source_attribute == 'left'
        
    def test_anchors_gt(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        view4 = anchor_view()
    
        view2.left.gt(view1.center_x)
        view3.left = ge(view1.center_x)
        view4.left > view1.center_x  # noqa: Optional syntactic sugar (or poison)

        view2_left = view2._constraints['>']['left'][0]
        view3_left = view3._constraints['>']['left'][0]
        view4_left = view4._constraints['>']['left'][0]
        assert view2_left == view3_left == view4_left

    def test_anchors_lt(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        view4 = anchor_view()

        view2.left.lt(view1.center_x)
        view3.left = le(view1.center_x)
        view4.left < view1.center_x  # noqa: Optional syntactic sugar (or poison)

        view2_left = view2._constraints['<']['left'][0]
        view3_left = view3._constraints['<']['left'][0]
        view4_left = view4._constraints['<']['left'][0]
        assert view2_left == view3_left == view4_left

    def test_anchors_eq(self, anchor_view):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()
        view4 = anchor_view()

        view2.left.eq(view1.center_x)
        view3.left = view1.center_x
        view4.left == view1.center_x  # noqa: Optional syntactic sugar (or poison)

        view2_left = view2._constraints['=']['left'][0]
        view3_left = view3._constraints['=']['left'][0]
        view4_left = view4._constraints['=']['left'][0]
        assert view2_left == view3_left == view4_left

    
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
        assert view._render_events() == "hx-post='/event' hx-trigger='click'"

    def test_get_roots(self):
        Events._dirties = set()
        
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
        assert view._event_generator is None
    
        @view
        def on_click(data):
            data.value = 1
            yield
            data.value = 2
        
        # Basic flow    
        view._process_event('click', view)
        assert view.value == 1
        assert inspect.isgenerator(view._event_generator)
        assert (
            view._render_events() == 
            "hx-post='/event' hx-trigger='click,next'"
        )
        view._process_event('next', view)
        assert view.value == 2
        assert view._event_generator is None
    
        # Restart
        view._process_event('click', view)
        assert view.value == 1
        view._process_event('click', view)
        assert view.value == 1
        view._process_event('next', view)
        assert view.value == 2
        
        view.value = 0
        view._process_event('next', view)
        assert view.value == 0
        
        
class TestAnimationContext:
    
    def test_animation_contextmanager(self):
        
        assert _animation_context() is None

        with animation():
            assert _animation_context() == (0.3, None)
            
            with animation(1.0, 'foobar'):
                assert _animation_context() == (1.0, 'foobar')
                
            assert _animation_context() == (0.3, None)
        
        assert _animation_context() is None
        
        
class TestStyleProperties:
        
    def test_base_setter_and_render(self):
        view = Core()
        
        assert view not in Core._dirties
        
        view._set_property(
            'text_color',
            (1, 1, 1, 1),
            'color', 
            'rgba(255,255,255,255)',
        )
        
        assert view in Core._dirties
        
        with animation(1.0):
            view._set_property(
                'corner_radius',
                '50%',
                'border-radius', 
                '50%',
            )
            
        with animation(2.0, 'ease-func'):
            view._set_property(
                'alpha',
                0.5,
                'opacity', 
                '50%',
            )
            
        rendered = view._render_props()
        
        assert rendered == (
            "color:rgba(255,255,255,255);"
            "border-radius:50%;"
            "opacity:50%;"
            "transition:border-radius 1.0s default-ease,opacity 2.0s ease-func"
        )

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
