ui4
===

```html
<div ui4="top=root.top; left=root.left; width=mirror.width:0.1s;"></div>
```

htmx alternative
================

Just naming
```html
<div ui4="top=root.top; width=other.width:0.1s;"></div>
```
Or separate attributes? Take a lot "hx namespace".
```html
<div ui4-top="root.top" ui4-width="mirror.width:0.1s"></div>
```

Docks
```html
<div ui4-dock="all"></div>
```
```html
<div ui4-dock="other.below"
```

Fit contents
```html
<div ui4-fit="both"></div>
```

Animation
```html
<div ui4="width=other.width:1s"></div>
```

Share of space
```html
<div ui4-dock="left" ui4-width="2,3"></div>
```

Attributes
==========

Already in:

- constant
- left, top, right, bottom
- centerX, centerY
- width, height

Docks:

- top, left, bottom, right
- top_left, top_right, bottom_left, bottom_right
- center, top_center, bottom_center, left_center, right_center
- sides
- top_and_bottom
- all

- above
- below
- left_of
- right_of


Fit:

- width, height, both

Constraints:

- 

Width values:

- `width=2of3` - two thirds of available space, considering gaps
- `= (full - ((3 + 1) * gap)) / 3 * 2 + ((2 - 1) * gap)`
- if gap = 0, reduces to `= full / 3 * 2`

Percentage values?