# Base view class
import copy
import uuid

from ui4.to_css import css_mapping


class View:
    
    x = 0
    y = 0
    right = None
    bottom = None
    width = 100
    height = 100
    background_color = 'black'
    
    _fixed_styles = 'position: absolute; box-sizing: border-box; overflow: hidden; text-overflow: ellipsis; pointer-events: none;'
    
    def __init__(self, parent=None, children=None, **kwargs):
        self.id = str(uuid.uuid4())
        self._parent = None
        self.parent = parent
        self.children = children or list()
    
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError(f"Unknown attribute {key}")
                
    def _render(self):
        
        self_styles = self._render_styles()
        
        children_rendered = ''.join([
            child._render()
            for child in self.children
        ])
        
        return self._render_this(self._fixed_styles, self_styles, children_rendered)
        
        
    def _render_this(self, fixed_styles, self_styles, children_rendered):
        return (
            f'<div id="{self.id}" '
            f'style="{fixed_styles}'
            f'{self_styles}">'
            f'{children_rendered}'
            '</div>'
        )
                
    def _render_styles(self):
        return ";".join([
            f"{css[0]}: {getattr(self, key)}{css[1] if len(css) > 1 else ''}"
            for key, css
            in css_mapping.items()
            if not getattr(self, key) is None
        ])
    
    @property    
    def parent(self):
        return self._parent
        
    @parent.setter
    def parent(self, value):
        if self._parent:
            self._parent.children.remove(self)
        self._parent = value
        if self._parent and not self in self._parent.children:
            self._parent.children.append(self)

if __name__ == '__main__':
    
    print(View()._render())

