Constraints
-----------

| Constraint | Example | Details | 
|---|---|---|
| Number | `view.left = 200` | Fixed amount in pixels. |
| Anchor | `view.left = view2.right` | <p>"Keep the left edge of `view` where the right edge of `view2` is." </p><p> Possible anchors are `top`, `bottom`, `left`, `right`, `width`, `height`, `center_x`, `center_y`. </p><p> A default gap of 8 pixels is applied between the views when applicable.</p> |
| Composite anchors | `view.center = view2.center` | <p>Convenience anchors setting more than one value at the same time.</p><p> Possible composite anchors are `center`, `position`, `size`, `frame` (combo of `position` and `size`).</p>
| Anchor with superview | `view.left = view3.left` | <p>"Keep to the left edge of the superview."</p><p>(Assuming `view3` is `view`'s superview.)</p> |
| Calculation | `view.left = view2.right - 2` | Default gap is not applied is you make a specific adjustment. Positive amounts are always towards bottom right corner. |
| With gap | `view.width = (view2.width - gap * 3)/2` | <p>"Half of the width of the other view."</p> `gap` is equal to the currently set default gap. |
| With helper | `view.width = half(view2.width)` | Same result as previous example, but more readable. Other convenient alternatives are `third` and `fourth`. |
| More generic helper | `view.width = share(view2.width, 2)` | Same result as previous example. |
| Limit | `view.left = at_least(view2.left)` | Lower limit for the value. There is also the corresponding `at_most`. |
| Several | `view.left = view2.left, at_least(view3.left)` | <p>"`view2.left` is equal to the larger of the left edges of the two other views."</p> Order of application is from left to right, so constraints to the right have a higher "priority". |
| With minmax helper | `view.left = maximum(view2.left, view3.left)` | Same result as above, but more readable. |
| Condition | `view.left = wide & view2.left` | <p>Constraint is applied only when the condition before `&` is true.</p> `wide` requires that view's superview is "landscape", the alternative is `high` for "portrait". |
| Screen aspect | `view.left = wide_root & view2.left` | As above, but references the whole viewport dimensions. |
| Detailed condition | `view.left = (view2.width > 300) & view2.left` | Single comparisons only, please, no `a < b < c`. |
||||
