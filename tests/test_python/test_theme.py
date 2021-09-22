from ui4.core import Color
from ui4.core import Core
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

    def test_style_fill(self):
        class TestCore(Core):
            pass

        TestCore.text_color = Core._css_color_prop('text_color', 'color')
        TestCore.background_color = Core._css_color_prop('background_color', 'background-color')
        
        class SomeStyle(Style):
            background_color = theme.background
            
        class OtherTheme(Theme):
            background = Color('indigo')
            
        Style.current_theme = OtherTheme
            
        TestCore.style = SomeStyle
            
        view = TestCore()
        view.text_color = 'black'
        
        assert 'color' in view._css_properties
        assert len(view._css_properties) == 1
        
        css_properties = view._set_position_and_fill_from_theme()
        
        assert 'background-color' in css_properties
        assert len(css_properties) == 2
        assert css_properties['background-color'] == Color('indigo').css
        
