
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

assert = require('assert');

it('should not fail', async () => {
  const one = 1;
  const two = 2;

  // Assert
  assert.equal(one, one);
});
