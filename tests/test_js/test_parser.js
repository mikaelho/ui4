/*jshint esversion: 9 */

require("./dummy_objects.js");
const UI4 = require("../../ui4/static/ui4.js");

const parser = new UI4.Parser();

assert = require('assert');
expect = require('chai').expect;

describe("Parser.parse", () => {
    it('should return empty object for an empty string', async () => {
        expect(parser.parse("")).to.deep.equal({});
    });
    it('should return a number as a number node', async () => {
        expect(parser.parse("3")).to.deep.equal({type: 'number', value: 3});
    });
    it('should ignore whitespace', async () => {
        expect(parser.parse(" 3 ")).to.deep.equal({type: 'number', value: 3});
    });
    it('should return a calculation as already calculated', async () => {
        expect(parser.parse("(1+3)/8")).to.deep.equal({type: 'number', value: 0.5});
    });
    it('should understand keywords and id/attribute combos', async () => {
        expect(parser.parse("id1.left+gap")).to.deep.equal({
            "operator": "+",
                "left": {"type": "idAndAttribute", "value": "id1.left"},
                "right": {"type": "keyword", "value": "gap"},
        });
    });
    it('should understand functions with calculated arguments', async () => {
        expect(parser.parse("share(1, 3-1)")).to.deep.equal({
            "type": "function",
            "value": "share",
            "arguments": [{"type": "number", "value": 1}, {"type": "number", "value": 2}]
        });
    });
    it('should give a meaningful error for garbage', async () => {
        expect(parser.parse.bind(parser, "garbage")).to.throw(
            SyntaxError, /Could not recognize token starting from \"garbage\"/
        );
    });
});
