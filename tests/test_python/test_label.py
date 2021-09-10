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


def test_theme_style_fill():
    label = Label()
    assert label._text_view._render_props() == ''
    assert label._render_props() == ''
