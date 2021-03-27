from ui4.core import Color
from ui4.theme import Style
from ui4.theme import Theme
from ui4.theme import contrast
from ui4.theme import theme


class TestStyles:
    
    def test_style_setting(self):
        
        class SomeStyle(Style):
    
            background_color = theme.background
            text_color = contrast.background
        
        style = SomeStyle
        
        assert callable(style.background_color)
        assert style.background_color(style) == Color('white')
        assert style.text_color(style) == Color('black')
        
        class OtherTheme(Theme):
            background = Color('blue')
        Style.current_theme = OtherTheme
        
        assert style.background_color(style) == Color('blue')
        assert style.text_color(style) == Color('white')

