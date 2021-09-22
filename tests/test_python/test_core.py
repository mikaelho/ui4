import inspect

import pytest

from ui4 import landscape
from ui4 import minimum
from ui4.animation import animation
from ui4.core import ConstraintExpression
from ui4.core import Core
from ui4.core import Events
from ui4.core import at_least
from ui4.core import at_most
from ui4.core import delay


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


class TestConstraint:

    def test_constraint_build_up(self):
        gap = ConstraintExpression(initial_value='gap')

        assert str(gap+1) == 'gap+1'
        assert str((gap-1)*2) == '(gap-1)*2'
        assert str(minimum(1, 2)) == 'min(1,2)'
        assert str(minimum((gap + 1)/2, 2)) == 'min((gap+1)/2,2)'
        assert str(minimum(1, 2)+gap) == 'min(1,2)+gap'

        assert str(at_least(200)) == '>200'
        assert str(at_least(gap+1, 200)) == '>gap+1 >200'

        assert str((gap > 4) & 1 + 2) == '3'
        assert str(((gap > 4) & 1 + 2).condition) == 'gap>4'
        assert str(landscape & gap + 1) == 'gap+1'
        assert str((landscape & gap + 1).condition) == 'landscape'

    def test_serialize(self):
        gap = ConstraintExpression(initial_value='gap')

        assert (gap+1).serialize('foo') == 'foo=gap+1'
        assert (at_most(minimum(1, 2))).serialize('foo') == 'foo<min(1,2)'

    def test_invert(self):
        gap = ConstraintExpression(initial_value='gap')

        assert str((gap+1).invert_operator()) == 'gap-1'
        assert str((gap-1).invert_operator()) == 'gap+1'

    def test_get_anchor(self, anchor_view):
        gap = ConstraintExpression(initial_value='gap')
        view1 = anchor_view()

        assert gap.get_anchor() is False
        assert (view1.left).get_anchor().view is view1
        assert (view1.left+1).get_anchor().view is view1


class TestAnchorProperties:

    def test_anchors_basic(self, anchor_view, constraints):
        view1 = anchor_view()
        view2 = anchor_view()

        view1.left = 100
        view1.center_x = view2.left + 1
        view1.top = at_least(view2.bottom)
        assert constraints(view1) == 'left=100;centerX=id2.left+1;top>id2.bottom'

        view1.left = None
        assert constraints(view1) == 'centerX=id2.left+1;top>id2.bottom'

    def test_anchors_release(self, anchor_view, constraints):
        view = anchor_view()

        view.left = 100
        assert constraints(view) == 'left=100'

        view.left = 200
        view.right = 100
        assert constraints(view) == 'left=200;right=100'

        view.left = None
        assert constraints(view) == 'right=100'

        view.release()
        assert constraints(view) == ''

        view.left = 200
        assert constraints(view) == 'left=200'

    def test_anchors_pruning(self, anchor_view):
        view = anchor_view()
        
        view.left = 100
        view.width = 200
        assert set(view._constraints.keys()) == {'left', 'width'}
        
        view.right = 300
        assert set(view._constraints.keys()) == {'right', 'width'}
        
        view.top = 400
        view.bottom = 500
        assert set(view._constraints.keys()) == {'right', 'width', 'top', 'bottom'}
        
        view.center_y = 600
        assert set(view._constraints.keys()) == {'right', 'width', 'top', 'center_y'}

    def test_anchors_in_container(self, anchor_view, constraints):
        view1 = anchor_view()
        view2 = anchor_view()
        view3 = anchor_view()

        view1.container = view2

        view3.parent = view1

        view3.left = view1.left
        view3.right = view2.right

        assert constraints(view3) == 'left=id2.left;right=id2.right'

    
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

    def test_event_handler_option_decorator(self):
        view = Core()

        @view
        @delay
        def on_click(_):
            pass

        @view
        @delay
        def on_change(_):
            pass

        assert view._render_events()['hx-trigger'] == 'change delay:0.5s,click delay:0.5s'

        view.remove_event('change')

        assert view._render_events()['hx-trigger'] == 'click delay:0.5s'

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
            'style': 'border-radius:50%;opacity:50%',
            'ui4style': 'border-radius:50%:0.3s;opacity:50%:2.0s,ease-func,alternate,1s,2s,inf',
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
