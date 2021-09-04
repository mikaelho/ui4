import pytest

from ui4 import Label


def test_dimension_combos():
    label = Label()
    assert label.alignment == {'center', 'middle'}
    assert label._combine_keys({'center'}) == {'center', 'middle'}
    assert label._combine_keys({'top'}) == {'center', 'top'}
    assert label._combine_keys({'right'}) == {'right', 'top'}
    assert label._combine_keys({'left', 'bottom'}) == {'left', 'bottom'}

    with pytest.raises(ValueError):
        assert label._combine_keys({'foo', 'bar'})


def test_dock_keys():
    label = Label()
    assert label._get_dock_key('center') == 'center'
    assert label._get_dock_key('middle') == 'center'
    assert label._get_dock_key('left') == 'left_center'
    assert label._get_dock_key('right') == 'right_center'
    assert label._get_dock_key('top') == 'top_center'
    assert label._get_dock_key('bottom') == 'bottom_center'
    assert label._get_dock_key(['left', 'top']) == 'top_left'
    assert label._get_dock_key(['left', 'bottom']) == 'bottom_left'
    assert label._get_dock_key(['right', 'top']) == 'top_right'
    assert label._get_dock_key(['right', 'bottom']) == 'bottom_right'
    assert label._get_dock_key(['right', 'middle']) == 'right_center'


def test_theme_style_fill():
    label = Label()
    assert label._text_view._render_props() == ''
    assert label._render_props() == ''
