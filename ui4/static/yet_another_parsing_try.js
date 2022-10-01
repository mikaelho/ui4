/*jshint esversion: 9 */



// Basic math
const OPERATOR = "operator";
const LEFT_PARENTHESIS = "leftParenthesis";
const RIGHT_PARENTHESIS = "rightParenthesis";
const NUMBER = "number";

// Application-specific
const ID_AND_ATTRIBUTE = "idAndAttribute";
const KEYWORD = "keyword";
const FUNCTION = "function";
const COMMA = "comma";

const AS_IS_TYPES = [ID_AND_ATTRIBUTE, KEYWORD];

class Parser {

    constructor(string) {
        const TOKEN_TYPES = [
            "(?<idAndAttribute>([a-zA-Z]|\\d|_|-)+\\.([a-zA-Z]+))",
            "(?<keyword>gap)",
            "(?<function>min|max|share)",
            "(?<comma>,)",
            "(?<operator>[\\+\\-\\*\\/\\^])",
            "(?<leftParenthesis>[(\\[])",
            "(?<rightParenthesis>[)\\]])",
            "(?<number>[\\d\\.]+)",
        ];
        this.matcher = new RegExp(`(${TOKEN_TYPES.join("|")})`,);

        this.currentToken = undefined;
        this.tokens = this.tokenize(string);
    }

    * tokenize(string) {
        let index = 0;
        string = string.replace(' ', '');
        while (index < string.length) {
            const match = string.substring(index).match(this.matcher);

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
        } else if (token && AS_IS_TYPES.includes(token.type)) {
            this.skipToken();
            return {type: token.type, value: token.value};
        } else if (token && token.type === FUNCTION) {
            const functionName = token.value;
            this.skipToken();
            token = this.getToken();
            if (token && token.type !== LEFT_PARENTHESIS) {
                throw `Function name should be followed by parenthesis, not ${token.type}: ${token.value}`;
            }
            return {type: FUNCTION, value: functionName, arguments: this.arguments()};
        } else if (token && token.type === LEFT_PARENTHESIS) {
            this.skipToken();
            const node = this.additive();
            token = this.getToken();
            if (token && token.type !== RIGHT_PARENTHESIS) {
                throw "Missing closing parenthesis";
            }
            return node;
        } else {
            throw `Unexpected ${token.type}: ${token.value}`;
        }
    }

    arguments() {
        let argument = this.additive();
        let token = this.getToken();
        if (token && token.type === COMMA) {
            return [argument].concat(this.arguments());
        } else if (token && token.type === RIGHT_PARENTHESIS) {
            return [argument];
        } else {
            throw `Expected comma or closing parenthesis in function arguments, got: ${token}`;
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


function tester(string) {
    console.log('INPUT: ' + string);
    try {
        console.log('OUTPUT:');
        console.log(JSON.stringify(new Parser(string).parse(), null, 4));
    } catch (error) {
        console.log(error);
    }
}

try {
    new Parser("foo").parse();
} catch (error) {

}

console.log('-----------------------------------------------------------------------------------------------');
tester("foo");
tester("1+2");
tester("1+2+gap+gap");
tester("id1.left");
tester("id1.left-gap");
tester("id1.left+2*(gap+1)");
tester("id1.left+2*(gap+1/2)");
tester("id1.left+2*(gap+1/2)");
tester("min(1, 2)");
tester("share(1+1, 2*gap");
tester("share(1+1, 2*gap)");