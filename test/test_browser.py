import time


def test_constraint_parsing_and_ordering(get_page, js_value):
    get_page()

    assert js_value("ui4.parseAndOrder('left=root.left left<another.left left>other.left')") == [
        {'comparison': '=', 'sourceAttr': 'left', 'sourceId': 'root', 'targetAttr': 'left'},
        {'comparison': '<', 'sourceAttr': 'left', 'sourceId': 'another', 'targetAttr': 'left'},
        {'comparison': '>', 'sourceAttr': 'left', 'sourceId': 'other', 'targetAttr': 'left'},
    ]

    # Order enforced, equals before less than before greater than
    assert js_value(
        "ui4.parseAndOrder('left=root.left left<another.left left>other.left')"
    ) == js_value(
        "ui4.parseAndOrder('left>other.left left=root.left left<another.left')"
    )

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
def test_with_elements(get_page, js_value, js_dimensions):
    webdriver = get_page("test-layouts.html")

    assert js_value("ui4.allDependencies.centered") == [
        {'targetAttr': 'centerX', 'comparison': '=', 'sourceId': 'root', 'sourceAttr': 'centerX'},
        {'targetAttr': 'centerY', 'comparison': '=', 'sourceId': 'root', 'sourceAttr': 'centerY'},
        {'targetAttr': 'width', 'comparison': '=', 'modifier': 200},
        {'targetAttr': 'height', 'comparison': '=', 'modifier': 100},
    ]

    assert js_value("ui4.allDependencies.below") == [
        {"targetAttr": "left", "comparison": "=", "sourceId": "centered", "sourceAttr": "left"},
        {"targetAttr": "right", "comparison": "=", "sourceId": "centered", "sourceAttr": "right"},
        {"targetAttr": "top", "comparison": "=", "sourceId": "centered", "sourceAttr": "bottom"},
        {"targetAttr": "bottom", "comparison": "=", "sourceId": "root", "sourceAttr": "bottom"},
    ]

    def js_source_values(elem_id):
        return webdriver.execute_script(f"""
            targetElem = document.getElementById('{elem_id}');
            results = [];
            ui4.allDependencies.{elem_id}.forEach(function(dependency) {{
                results.push(ui4.getSourceValue(targetElem, dependency));
            }});
            return results;
        """)

    # SOURCE VALUES

    # Center
    assert js_source_values('centered') == [
        {'contained': True, 'type': 'neutral', 'value': 300},
        {'contained': True, 'type': 'neutral', 'value': 200},
        {'contained': False, 'type': 'neutral', 'value': 200},
        {'contained': False, 'type': 'neutral', 'value': 100},
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


def test_with_limits(get_page, js_dimensions):
    get_page("test-limits.html")

    assert js_dimensions('third') == [316, 116, 200, 100]
