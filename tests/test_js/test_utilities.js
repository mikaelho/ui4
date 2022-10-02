/*jshint esversion: 9 */

const UI4 = require("../../ui4/static/ui4.js");
const ui4 = new UI4();
assert = require('assert');

describe("toCamelCase", () => {
  it('turns CSS style name to JS variable name', async () => {
    assert.equal(ui4.toCamelCase('background-color'), 'backgroundColor');
  });
});
