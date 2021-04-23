
// Some dummy objects to enable running the tests without the browser
window = {
    addEventListener: (event_name, func) => {}
};
document = {
    addEventListener: (event_name, func) => {}
};
MutationObserver = function MutationObserver(func) {
    this.observe = (node, func) => {}
};

require("../ui4/static/ui4.js");

const test = window.ui4._privateForTesting;

assert = require('assert');

describe("#parseSpec", () => {
  it('should parse spec from backend', async () => {
    const spec = {
      a0: "left",
      a5: 200
    };
    
    const result = test.parseSpec(spec, "id22");
    
    const expected = {
      targetId: 'id22',
      targetAttr: 'left',
      comparison: '=',
      modifier: 200
    };
    
    assert.deepEqual(result, expected);
  });
});

describe("#toCamelCase", () => {
  it('should turn CSS style name to JS variable name', async () => {
    assert.equal(test.toCamelCase('background-color'), 'backgroundColor');
  });
});

describe("#maxMinCheck", () => {
  it('should retain and return true for the maximum/minimum values', async () => {
    const maxValues = {left: 100};
    const minValues = {};
    const dependency = {require: 'max', targetAttr: 'left'};

    shouldApply = test.maxMinCheck(dependency, 200, maxValues, minValues);
    assert.equal(shouldApply, true);
    assert.equal(maxValues.left, 200);

    shouldApply = test.maxMinCheck(dependency, 100, maxValues, minValues);
    assert.equal(shouldApply, false);
    assert.equal(maxValues.left, 200);

    delete dependency.require;
    shouldApply = test.maxMinCheck(dependency, 100, maxValues, minValues);
    assert.equal(shouldApply, true);
    assert.equal(maxValues.left, 200);

    dependency.require = 'min';
    dependency.targetAttr = 'bottom';
    shouldApply = test.maxMinCheck(dependency, 150, maxValues, minValues);
    assert.equal(shouldApply, true);
    assert.equal(minValues.bottom, 150);

    shouldApply = test.maxMinCheck(dependency, -150, maxValues, minValues);
    assert.equal(shouldApply, true);
    assert.equal(minValues.bottom, -150);
  });
});