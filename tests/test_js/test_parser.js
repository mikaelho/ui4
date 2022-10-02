/*jshint esversion: 9 */

const UI4 = require("../../ui4/static/ui4.js");

const Parser = UI4.Parser;
const parser = new UI4.Parser();

assert = require('assert');
expect = require('chai').expect;

describe("Parser.parse", () => {
    it('returns empty object for an empty string', async () => {
        expect(parser.parse("")).to.deep.equal({});
    });
    it('returns a number as a number node', async () => {
        expect(parser.parse("3")).to.deep.equal({type: 'number', value: 3});
    });
    it('ignores whitespace', async () => {
        expect(parser.parse(" 3 ")).to.deep.equal({type: 'number', value: 3});
    });
    it('returns a calculation as already calculated', async () => {
        expect(parser.parse("(1+3)/8")).to.deep.equal({type: 'number', value: 0.5});
    });
    it('understands keywords and id/attribute combos', async () => {
        expect(parser.parse("id1.left+gap")).to.deep.equal({
            type: "operator",
            operator: "+",
            left: {type: "idAndAttribute", value: {id: "id1", attribute: "left"}},
            right: {type: "keyword", value: "gap"},
        });
    });
    it('understands functions with calculated arguments', async () => {
        expect(parser.parse("share(1, 3-1)")).to.deep.equal({
            "type": "function",
            "value": "share",
            "arguments": [{"type": "number", "value": 1}, {"type": "number", "value": 2}]
        });
    });
    it('errors with garbage', async () => {
        const freshParser = new Parser();
        expect(freshParser.parse.bind(freshParser, "garbage")).to.throw(
            SyntaxError, /Could not recognize token starting from \"garbage\"/
        );
    });
    it('errors with general syntax error', async () => {
        const freshParser = new Parser();
        expect(freshParser.parse.bind(freshParser, "1++2")).to.throw(
            SyntaxError, /Unexpected operator: \+/
        );
    });
    it('errors with missing parenthesis', async () => {
        const freshParser = new Parser();
        expect(freshParser.parse.bind(freshParser, "1+(2+3")).to.throw(
            SyntaxError, /Missing closing parenthesis/
        );
    });
    it('errors with garbled function parameters', async () => {
        const freshParser = new Parser();
        expect(freshParser.parse.bind(freshParser, "min(2, 3")).to.throw(
            SyntaxError, /Expected comma or closing parenthesis/
        );
    });
    it('errors with function without parameters', async () => {
        const freshParser = new Parser();
        expect(freshParser.parse.bind(freshParser, "min+1")).to.throw(
            SyntaxError, /Function name should be followed by parenthesis/
        );
    });
    it('creates a walkable tree', async () => {
        const parseResult = parser.parse("id1.left+gap/2-5");
        const walker = node => node.type;
        expect(new UI4().walkParseTree(parseResult, walker)).to.deep.equal(
            ["operator", "operator", "idAndAttribute", "operator", "keyword", "number", "number"]
        );
    });
});
