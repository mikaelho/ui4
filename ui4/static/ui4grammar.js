/*jshint esversion: 9 */

function calculate(expression) {
    expression = expression.replace(/\s/g, '');
    return helper(Array.from(expression), 0);
}

function helper(string, index) {
    var stack = [];
    let operator = '+';
    let num = 0;
    let numString = '';
    for (let i = index; i < string.length; i++) {
        let ch = string[i];
        if (ch >= '0' && ch <= '9' || ch === '.') {
            numString += ch;
            num = parseFloat(numString);
        }
        if (!(ch >= '0' && ch <= '9' || ch === '.') || i === string.length - 1) {
            if (ch === '(') {
                num = helper(string, i + 1);
                let l = 1, r = 0;
                for (let j = i + 1; j < string.length; j++) {
                    if (string[j] === ')') {
                        r++;
                        if (r === l) {
                            i = j;
                            break;
                        }
                    } else if (string[j] === '(') l++;
                }
            }
            let pre = -1;
            switch (operator) {
                case '+':
                    stack.push(num);
                    break;
                case '-':
                    stack.push(num * -1);
                    break;
                case '*':
                    pre = stack.pop();
                    stack.push(pre * num);
                    break;
                case '/':
                    pre = stack.pop();
                    stack.push(pre / num);
                    break;
            }
            operator = ch;
            num = 0;
            numString = '';
            if (ch === ')') break;
        }
    }
    let objectPart = [];
    let numberPart;
    while (stack.length > 0) {
        const popped = stack.pop();
        if (typeof popped === 'object') {
            objectPart.push(popped);
        } else {
            if (numberPart === undefined) {numberPart = 0;}
            numberPart += stack.pop();
        }
    }
    if (objectPart.length > 0) {
        const answer = {operator: '+', values: objectPart};
        if (numberPart !== undefined) {answer.values.push(numberPart);}
        return answer;
    } else if (numberPart !== undefined) {
        return numberPart;
    } else {
        throw `Could not parse "${string}"`;
    }
}

console.log(calculate("4.5*(1.5+2.5)/5"));

const matcher = new RegExp(`[a-zA-Z\\d_-]+\\.below`);

if ("centerButton.below".match(matcher)) {
    console.log("Yews");
}