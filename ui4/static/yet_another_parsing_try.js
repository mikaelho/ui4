/*jshint esversion: 9 */


const ID_AND_ATTRIBUTE = "idAndAttribute";
const IDENTIFIER = "identifier";
const OPERATOR = "operator";
const LEFT_PARENTHESIS = "leftParenthesis";
const RIGHT_PARENTHESIS = "rightParenthesis";
const NUMBER = "number";
const GAP = "gap";


class Parser {

    constructor(string) {
        const PER_TOKEN = [
            "(?<idAndAttribute>([a-zA-Z]|\\d|_|-)+\\.([a-zA-Z]+))",
            "(?<gap>gap)",
            "(?<identifier>[a-zA-Z]+)",
            "(?<operator>[\\+\\-\\*\\/\\^])",
            "(?<leftParenthesis>[(\\[])",
            "(?<rightParenthesis>[)\\]])",
            "(?<number>[\\d\\.]+)",
        ];
        const COMBINED_TOKENS = PER_TOKEN.join("|");

        this.complete_matcher = new RegExp(`(${COMBINED_TOKENS})`,);

        this.currentToken = undefined;
        this.tokens = this.tokenize(string);
    }

    * tokenize(string) {
        let index = 0;
        while (index < string.length) {
            const match = string.substring(index).match(this.complete_matcher);

            if (!match) {
                throw `Could not recognize token starting from "${string.substring(index)}"`;
            }
            index += match[0].length;
            for (const [key, value] of Object.entries(match.groups)) {
                if (value !== undefined) {
                    yield {type: key, value: value};
                    break;
                }
            }
        }
    }

    getToken() {
        let token = this.currentToken ? this.currentToken : this.tokens.next().value;
        this.currentToken = undefined;
        return token;
    }

    peekToken() {
        if (!this.currentToken) {
            this.currentToken = this.tokens.next().value;
        }
        return this.currentToken;
    }

    skipToken() {
        if (!this.currentToken) {
            this.currentToken = this.tokens.next().value;
        }
        this.currentToken = undefined;
    }

    parse() {
        return this.additive();
    }

    additive() {
        let left = this.multiplicative()
        let token = this.peekToken();
        while (token && token.type === OPERATOR && (token.value === '+' || token.value === '-')) {
            this.skipToken();
            const right = this.multiplicative();
            left = this.getNode(token.value, left, right);
            token = this.peekToken();
        }
        return left;
    }

    multiplicative() {
        let left = this.primary();
        let token = this.peekToken();
        while (token && token.type === OPERATOR && (token.value === '*' || token.value === '/')) {
            this.skipToken();
            const right = this.primary();
            left = this.getNode(token.value, left, right);
            token = this.peekToken();
        }
        return left;
    }

    primary() {
        let token = this.peekToken();
        if (token && token.type === NUMBER) {
            this.skipToken();
            return {type: token.type, value: parseFloat(token.value)};
        } else if (token && (token.type === GAP || token.type === ID_AND_ATTRIBUTE || token.type === IDENTIFIER)) {
            this.skipToken();
            return {type: token.type, value: token.value};
        } else if (token && token.type === LEFT_PARENTHESIS) {
            this.skipToken();
            const node = this.additive(); // The beauty of recursion
            token = this.getToken();
            if (token && token.type !== RIGHT_PARENTHESIS) {
                throw "Missing closing parenthesis";
            }
            return node;
        } else {
            throw `Unexpected ${token.type}: ${token.value}`;
        }
    }

    getNode(operator, left, right) {
        // Return a node combining the operator and left and right sides, or if possible, already calculated number node
        const operations = {"+": (a, b) => a + b, "-": (a, b) => a - b, "*": (a, b) => a * b, "/": (a, b) => a / b};
        if ((left && left.type === NUMBER) && (right && right.type === NUMBER)) {
            return {type: NUMBER, value: operations[operator](left.value, right.value)};
        } else {
            return {operator: operator, left: left, right: right};
        }
    }
}

// function parse(expression) {
//     const tokens = tokenize(expression);
//
//     const [tree, remainingTokens] = parseTokens(tokens, 0);
// }
//
//
//
// function parseTokens(tokens, position) {
//     let sign = "+";
//     let delta = 0;
//     let stack = [];
//
//     while(position < tokens.length) {
//         let token = tokens[position];
//         let delta = 1;
//         if (token[0] === "left parenthesis") {
//             [token, delta] = parseTokens(tokens, position + 1);
//         }
//         if (token[0] === )
//     }
// }

// for (const token of (new Tokens("id1.left+2*(gap+1)")).tokens) {
//     console.log(token);
// }

function pretty(obj) {
    console.log(JSON.stringify(obj, null, 4));
}

pretty(new Parser("1+2").parse());
pretty(new Parser("id1.left").parse());
pretty(new Parser("id1.left-gap").parse());
pretty(new Parser("id1.left+2*(gap+1)").parse());
pretty(new Parser("id1.left+2*(gap+1/2)").parse());