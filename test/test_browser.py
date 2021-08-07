import time


def test_constraint_parsing_and_ordering(get_page, js_value):
    get_page()

    assert js_value("ui4.parseAndOrder('left=root.left left<another.left left>other.left')") == [
        {'comparison': '=', 'targetAttribute': 'left', 'value': {'attribute': 'left', 'id': 'root'}},
        {'comparison': '<', 'targetAttribute': 'left', 'value': {'attribute': 'left', 'id': 'another'}},
        {'comparison': '>', 'targetAttribute': 'left', 'value': {'attribute': 'left', 'id': 'other'}},
    ]

    # Order enforced, equals before less than before greater than
    assert js_value(
        "ui4.parseAndOrder('left=root.left left<another.left left>other.left')"
    ) == js_value(
        "ui4.parseAndOrder('left>other.left left=root.left left<another.left')"
    )

    assert js_value("ui4.parseAndOrder('left=root.left bottom=root.bottom width=100 height=100 "
                    "root.width>root.height?width=200 root.height<root.width?height=250')") == [
        {'comparison': '=', 'targetAttribute': 'left', 'value': {'attribute': 'left', 'id': 'root'}},
        {'comparison': '=', 'targetAttribute': 'bottom', 'value': {'attribute': 'bottom', 'id': 'root'}},
        {'comparison': '=', 'targetAttribute': 'width', 'value': 100},
        {'comparison': '=', 'targetAttribute': 'height', 'value': 100},
        {'comparison': '=', 'targetAttribute': 'width', 'value': 200, 'condition': {
            'comparison': '>',
            'lhs': {'attribute': 'width', 'id': 'root'},
            'rhs': {'attribute': 'height', 'id': 'root'},
        }},
        {'comparison': '=', 'targetAttribute': 'height', 'value': 250, 'condition': {
            'comparison': '<',
            'lhs': {'attribute': 'height', 'id': 'root'},
            'rhs': {'attribute': 'width', 'id': 'root'},
        }},
    ]


def test_gap_adjustment(get_page, js_value):
    get_page()

    assert js_value("ui4.gapAdjustment({contained: true, type: 'leading'}, {type: 'leading'})") == 8
    assert js_value("ui4.gapAdjustment({contained: true, type: 'trailing'}, {type: 'trailing'})") == -8
    assert js_value("ui4.gapAdjustment({contained: true, type: 'leading'}, {type: 'trailing'})") == 0
    assert js_value("ui4.gapAdjustment({contained: true, type: 'leading'}, {type: 'neutral'})") == 0

    assert js_value("ui4.gapAdjustment({contained: false, type: 'leading'}, {type: 'leading'})") == 0
    assert js_value("ui4.gapAdjustment({contained: false, type: 'trailing'}, {type: 'trailing'})") == 0
    assert js_value("ui4.gapAdjustment({contained: false, type: 'leading'}, {type: 'trailing'})") == -8
    assert js_value("ui4.gapAdjustment({contained: false, type: 'trailing'}, {type: 'leading'})") == 8
    assert js_value("ui4.gapAdjustment({contained: false, type: 'leading'}, {type: 'neutral'})") == 0


# @pytest.mark.skip(reason="Browser test")
def test_base_constraints(get_page, js_value, js_dimensions, js_with_stack):
    webdriver = get_page("test-basic-constraints.html")

    assert js_value("ui4.allDependencies.centered") == [
        {'targetAttribute': 'centerX', 'comparison': '=', 'value': {'attribute': 'centerX', 'id': 'root'}},
        {'targetAttribute': 'centerY', 'comparison': '=', 'value': {'attribute': 'centerY', 'id': 'root'}},
        {'targetAttribute': 'width', 'comparison': '=', 'value': 200},
        {'targetAttribute': 'height', 'comparison': '=', 'value': 100},
    ]

    assert js_value("ui4.allDependencies.below") == [
        {'targetAttribute': 'left', 'comparison': '=', 'value': {'attribute': 'left', 'id': 'centered'}},
        {'targetAttribute': 'right', 'comparison': '=', 'value': {'attribute': 'right', 'id': 'centered'}},
        {'targetAttribute': 'top', 'comparison': '=', 'value': {'attribute': 'bottom', 'id': 'centered'}},
        {'targetAttribute': 'bottom', 'comparison': '=', 'value': {'attribute': 'bottom', 'id': 'root'}},
    ]

    def js_source_values(elem_id):
        return js_with_stack(f"""
            targetElem = document.getElementById('{elem_id}');
            results = [];
            ui4.allDependencies.{elem_id}.forEach(function(dependency) {{
                results.push(ui4.processSourceSpec(targetElem, dependency.value));
            }});
            return results;
        """)

    # SOURCE VALUES

    # Center
    assert js_source_values('centered') == [
        {'contained': True, 'type': 'neutral', 'value': 300},
        {'contained': True, 'type': 'neutral', 'value': 200},
        200,
        100,
    ]

    # Below
    assert js_source_values('below') == [
        {'contained': False, 'type': 'leading', 'value': 200},
        {'contained': False, 'type': 'trailing', 'value': 400},
        {'contained': False, 'type': 'trailing', 'value': 250},
        {'contained': True, 'type': 'trailing', 'value': 400},
    ]

    # Above
    assert js_source_values('above') == [
        {'contained': False, 'type': 'neutral', 'value': 200},
        {'contained': False, 'type': 'neutral', 'value': 300},
        {'contained': False, 'type': 'leading', 'value': 150},
        {'contained': True, 'type': 'leading', 'value': 0},
    ]

    # On the left
    assert js_source_values('left') == [
        {'contained': False, 'type': 'leading', 'value': 150},
        {'contained': False, 'type': 'trailing', 'value': 250},
        {'contained': False, 'type': 'leading', 'value': 200},
        {'contained': True, 'type': 'leading', 'value': 0},
    ]

    # On the right
    assert js_source_values('right') == [
        {'contained': False, 'type': 'neutral', 'value': 100},
        {'contained': False, 'type': 'neutral', 'value': 200},
        {'contained': False, 'type': 'trailing', 'value': 400},
        {'contained': True, 'type': 'trailing', 'value': 600},
    ]

    # RESULTING VALUES

    # Check [x/left, y/top, width, height] values
    assert js_dimensions('centered') == [200, 150, 200, 100]  # Center
    assert js_dimensions('below') == [200, 250+8, 200, 150-2*8]  # Below
    assert js_dimensions('above') == [200, 8, 200, 150-2*8]  # Above
    assert js_dimensions('left') == [8, 150, 200-2*8, 100]  # On the left
    assert js_dimensions('right') == [400+8, 150, 200-2*8, 100]  # On the right

    # WITH UPDATED GAP
    webdriver.execute_script("ui4.setGap(0);")

    # Check [x/left, y/top, width, height] values
    assert js_dimensions('centered') == [200, 150, 200, 100]  # Center
    assert js_dimensions('below') == [200, 250, 200, 150]  # Below
    assert js_dimensions('above') == [200, 0, 200, 150]  # Above
    assert js_dimensions('left') == [0, 150, 200, 100]  # On the left
    assert js_dimensions('right') == [400, 150, 200, 100]  # On the right


def test_comparison_constraints(get_page, js_dimensions):
    get_page("test-limits.html")

    assert js_dimensions('third') == [316, 116, 200, 100]


def test_more_complex_constraints(get_page, js_dimensions):
    get_page("test-calculations.html")

    # "Complex" calculations and gap
    assert js_dimensions('first') == [8, 8, (600-2*8)/2, 400-50]

    # Multiple source attributes
    assert js_dimensions('second') == [8, 400-50+8, 100, 400-350-2*8]


def test_always_square(get_page, js_dimensions):
    get_page("test-squaring.html")

    assert js_dimensions('inLandscapeWithLessThan') == [8, 8, 84, 84]
    assert js_dimensions('inLandscapeWithMin') == [208, 8, 84, 84]
    assert js_dimensions('inPortraitWithLessThan') == [8, 8, 84, 84]
    assert js_dimensions('inPortraitWithMin') == [8, 208, 84, 84]

    assert js_dimensions('maxed') == [8, 242, 150, 150]


def test_aspect_conditions(get_page, js_dimensions):
    get_page("test-conditions.html")

    assert js_dimensions('landscapeMenu1') == [8, 8, 100, 84]
    assert js_dimensions('landscapeMenu2') == [192, 8, 100, 84]
    assert js_dimensions('portraitMenu1') == [8, 8, 84, 100]
    assert js_dimensions('portraitMenu2') == [8, 192, 84, 100]

    assert js_dimensions('comparisons') == [8, 192, 250, 200]
    time.sleep(5)
