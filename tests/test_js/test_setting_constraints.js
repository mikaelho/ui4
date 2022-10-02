/*jshint esversion: 9 */

const UI4 = require("../../ui4/static/ui4.js");
const ui4 = new UI4();
assert = require('assert');
expect = require('chai').expect;

beforeEach(function () {
  this.jsdomClean = require('jsdom-global')();
});

after(function () {
  this.jsdomClean();
});

describe("combineConstraintAttributes", () => {
    it('combines several attributes into a single string', async () => {
        const fakeNode = {
            getAttribute: name => "left=id1.left",
            attributes: [{name: "right", value: "id1.right"}, {name: "fit", value: "both"}],
        };
        expect(ui4.combineConstraintAttributes(fakeNode)).to.equal("left=id1.left;right=id1.right;fit=both");
    });
});

describe("checkStyles", () => {
    it('sets base CSS styles on any node with ui4 attribute', async () => {
        const fakeDiv = document.createElement("div");
        fakeDiv.setAttribute("ui4", "left=id1.left");
        ui4.checkStyles(fakeDiv);
        expect(fakeDiv.style.position).to.equal("absolute");
        expect(fakeDiv.style.width).to.equal("");
    });
    it('sets ui4 and root CSS styles on root node', async () => {
        const fakeDiv = document.createElement("div");
        fakeDiv.classList = ["ui4Root"];
        ui4.checkStyles(fakeDiv);
        expect(fakeDiv.style.position).to.equal("absolute");
        expect(fakeDiv.style.width).to.equal("100%");
    });
});
