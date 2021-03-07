import inspect

import pytest

from ui4.core import Core


def test_identity():
    view1 = Core()
    view2 = Core()

    assert view1.id == 'id1'
    assert view2.id == 'id2'

    assert Core.views['id2'] == view2


def test_hierarchy():
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
    
    
def test_renderers():
    view = Core()
    
    assert len(view._renderers) == 1
    
    
def test_event_handler_decorator():    
    view = Core()
    
    with pytest.raises(ValueError):
        @view
        def on_nonexistent_event(data):
            pass
            
    @view
    def on_click(data):
        pass
        
    assert inspect.isfunction(view.on_click)
    
    assert (
        view._render_events() == \
        "hx-post='/event' hx-trigger='click'"
    )


def test_event_generator():
    view = Core()
    
    assert view._event_generator is None

