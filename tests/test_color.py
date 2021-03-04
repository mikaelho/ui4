import pytest

import ui4.color as color


def test_init_values():
    c = color.Color('red')
    assert c == [1.0, 0.0, 0.0, 1.0]
    assert c == (1, 0, 0, 1)
    assert c.r == c.red == 1.0
    assert c.g == c.green == 0.0
    assert c.b == c.blue == 0.0
    assert c.a == c.alpha == 1.0
    assert c.hex == "#ff0000"
    assert c.ints == (255, 0, 0, 255)


def test_init_with_alpha():
    c = color.Color('red', alpha=127.5)
    assert c == [1, 0, 0, 0.5]

    c = color.Color(127.5, 255, 0, 127.5)
    assert c == (0.5, 1, 0, 0.5)
    
    
def test_convert_to_name():
    c = color.Color(255, 255, 255)
    assert c.name == 'white'

