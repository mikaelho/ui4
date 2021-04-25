
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
  it('should parse 1-dependency spec from backend', async () => {
    const spec = {
      a0: "left",
      a5: 200
    };
    
    const result = test.parseFullSpec(spec, "id22");
    
    const expected = {
      targetId: 'id22',
      targetAttr: 'left',
      comparison: '=',
      modifier: 200
    };
    
    assert.deepEqual(result, expected);
  });
  
  it('should parse list dependency spec with animation', async () => {
    const spec = {
      key: "max",
      list: [
        {
          a0: "left",
          a5: 200
        },
        {
          a0: "left",
          a5: 300
        }
      ],
      a7: 0.3
    };
    
    const result = test.parseFullSpec(spec, "id22");
    
    const expected = {
      targetId: 'id22',
      comparison: '=',
      key: "max",
      list: [
        {
          targetAttr: 'left',
          comparison: '=',
          modifier: 200
        },
        {
          targetAttr: 'left',
          comparison: '=',
          modifier: 300
        }
      ],
      duration: 0.3
    };
    
    assert.deepEqual(result, expected);
  });
});

describe("#toCamelCase", () => {
  it('should turn CSS style name to JS variable name', async () => {
    assert.equal(test.toCamelCase('background-color'), 'backgroundColor');
  });
});
