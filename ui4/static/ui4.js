/*jshint esversion: 9 */

// Depends on globals:
// parse - the ui4 attribute value parser, from ui4parser.js
const parse = this.null.parse;  // From ui4parser.js


class UI4 {

    static LEADING = 'leading';
    static TRAILING = 'trailing';
    static NEUTRAL = 'neutral';

    static attrType = {
        constant: UI4.NEUTRAL,
        width: UI4.NEUTRAL,
        height: UI4.NEUTRAL,
        left: UI4.LEADING,
        right: UI4.TRAILING,
        top: UI4.LEADING,
        bottom: UI4.TRAILING,
        centerX: UI4.NEUTRAL,
        centerY: UI4.NEUTRAL,
    };

    static operations = {"+": (a, b) => a + b, "-": (a, b) => a - b, "*": (a, b) => a * b, "/": (a, b) => a / b};
    static comparisons = {"=": (a, b) => a !== b, "<": (a, b) => a >= b, ">": (a, b) => a <= b};
    static ordering = {"=": 0, "<": 1, ">": 2};

    constructor() {
        this.gap = 8;

        this.callLog = [];

        this.allDependencies = {};

        const _this = this;
        this.getValue = {
            width: (context) => parseFloat(context.getStyle.width),
            height: (context) => parseFloat(context.getStyle.height),
            left: (context) => context.contained ?  0 : parseFloat(context.getStyle.left),
            right: (context) => context.contained ?
                parseFloat(context.getStyle.width) :
                parseFloat(context.parentStyle.width) - parseFloat(context.getStyle.right),
            top: (context) => context.contained ?  0 : parseFloat(context.getStyle.top),
            bottom: (context) => context.contained ?
                parseFloat(context.getStyle.height) :
                parseFloat(context.parentStyle.height) - parseFloat(context.getStyle.bottom),
            centerX: (context) => context.contained ?
                parseFloat(context.getStyle.width) / 2 :
                parseFloat(context.getStyle.left) + parseFloat(context.getStyle.width) / 2,
            centerY: (context) => context.contained ?
                parseFloat(context.getStyle.height) / 2 :
                parseFloat(context.getStyle.top) + parseFloat(context.getStyle.height) / 2,
            fitWidth: function (context) {
                let left = false;
                let right;
                for (const child of context.targetElem.children) {
                    const bbox = child.getBoundingClientRect();
                    if (left === false) {
                        left = bbox.left;
                        right = bbox.right;
                    } else {
                        left = Math.min(left, bbox.left);
                        right = Math.max(right, bbox.right);
                    }
                }
                if (left === false) {
                    right = left = 0;
                }
                return right - left + 2 * _this.gap;
            },
            fitHeight: function (context) {
                let top = false;
                let bottom;
                for (const child of context.targetElem.children) {
                    const bbox = child.getBoundingClientRect();
                    if (top === false) {
                        top = bbox.top;
                        bottom = bbox.bottom;
                    } else {
                        top = Math.min(top, bbox.top);
                        bottom = Math.max(bottom, bbox.bottom);
                    }
                }
                if (!top) {
                    bottom = top = 0;
                }
                return bottom - top + 2 * _this.gap;
            }
        };

        this.setValue = {
            width: function(context, value) { return {width: value + 'px'};},
            height: function(context, value) { return {height: value + 'px'};},
            left: function(context, value) { return {left: value + 'px'};},
            right: function(context, value) { return {right: parseFloat(context.parentStyle.width) - value + 'px'};},
            top: function(context, value) { return {top: value + 'px'};},
            bottom: function(context, value) { return {bottom: parseFloat(context.parentStyle.height) - value + 'px'};},
            centerX: function(context, value) {
                if (context.dependencies.find(item => item.targetAttr === 'left')) {  // left locked, width must give
                    return {width: 2 * (value - parseFloat(context.getStyle.left)) + 'px'};
                } else if (context.dependencies.find(item => item.targetAttr === 'right')) {  // width must give)
                    return {
                        width: 2 * (parseFloat(context.parentStyle.width) -
                            parseFloat(context.getStyle.right) - value) + 'px'
                    };
                } else {  // Neither locked, move left
                    return {left: value - parseFloat(context.getStyle.width) / 2 + 'px'};
                }
            },
            centerY: function(context, value) {
                if (context.dependencies.find(item => item.targetAttr === 'top')) {  // top locked, height must give
                    return {height: 2 * (value - parseFloat(context.getStyle.top)) + 'px'};
                } else if (context.dependencies.find(item => item.targetAttr === 'bottom')) {  // height must give)
                    return {
                        height: 2 * (parseFloat(context.parentStyle.height) -
                            parseFloat(context.getStyle.bottom) - value) + 'px'
                    };
                } else {  // Neither locked, move top
                    return {top: value - parseFloat(context.getStyle.height) / 2 + 'px'};
                }
            }
        };
    }

    setGap(gap) {
        this.gap = gap;
        this.checkDependencies();
    }

    startClassObserver() {
        const observer = new MutationObserver(this.classChangeHandler.bind(this));
        observer.observe(document, {
          subtree: true,
          childList: true,
          attributeFilter: ["ui4"]
        });
    }

    classChangeHandler(mutations, observer) {
        mutations.forEach((mutation) => {
            switch (mutation.type) {
                case 'childList':
                    mutation.addedNodes.forEach((node) => {
                        this.setDependencies(node);
                    });
                    break;
                case 'attributes':
                    this.setDependencies(mutation.target);
                    break;
            }
        });
    }

    startTracking() {
        this.callLog.push("startTracking");
        const observer = new MutationObserver(this.checkDependencies.bind(this));
        observer.observe(document.body, {
            subtree: true,
            childList: true,
            attributeFilter: ["style"]
        });
        this.checkDependencies();
    }

    setDependencies(node) {
        const targetId = node.id;
        if (!targetId) { return; }

        // const ui4AnimationID = node.getAttribute("ui4anim");
        const ui4AttrValue = node.getAttribute("ui4");

        if (ui4AttrValue) {
            let dependencies;
            try {
                dependencies = this.parseAndOrder(ui4AttrValue);
            } catch(error) {
                console.error(error.toString());
                return;
            }
            if (!dependencies.length) {
                delete this.allDependencies[targetId];
            } else {
                this.allDependencies[targetId] = dependencies;
            }
        }
    }

    parseAndOrder(spec) {
        const dependencies = parse(spec);
        dependencies.sort((a, b) => UI4.ordering[a.comparison] - UI4.ordering[b.comparison]);
        return dependencies;
    }

    checkDependencies() {
        this.callLog.push("checkDependencies");
        this.checkAllStaticDependencies();
    }

    checkAllStaticDependencies() {
        for (const [targetId, dependencies] of Object.entries(this.allDependencies)) {
            let finalValues = this.checkDependenciesForOneElement(targetId, dependencies);
            // Apply the final value for each attribute
            for (const [targetAttr, data] of Object.entries(finalValues)) {
                const updates = this.setValue[targetAttr](data.context, data.sourceValue);
                for (const [key, value] of Object.entries(updates)) {
                    data.context.style[key] = value;
                }
            }
        }
    }

    checkDependenciesForOneElement(targetId, dependencies) {
        let targetElem = document.getElementById(targetId);
        let values = {};

        dependencies.forEach(dependency => {
            const source = this.getSourceValue(targetElem, dependency);

            if (source === undefined) {
                return;
            }

            let targetContext = this.getTargetContext(targetElem, dependencies);
            let target = this.getTargetValue(dependency.targetAttr, targetContext);
            let modifier = dependency.modifier !== undefined ? dependency.modifier : this.gap;

            source.value += this.gapAdjustment(source, target, modifier);

            if (UI4.comparisons[dependency.comparison](target.value, source.value)) {
                values[dependency.targetAttr] = {
                    targetElem: targetElem,
                    targetValue: target.value,
                    sourceValue: source.value,
                    context: target.context
                };
            }
        });

        return values;
      }

    getSourceValue(targetElem, dependency) {
        /**
        if (!checkRequirements(targetElem, dependency)) {
            return;
        }
         **/

        if (dependency.sourceId === undefined && dependency.modifier !== undefined) {
            return {
                value: dependency.modifier,
                type: UI4.NEUTRAL,
                contained: false
            };
        }
        else {
            const sourceElem = document.getElementById(dependency.sourceId);

            if (!sourceElem) {
                console.error('Could not find source element with id ' + dependency.sourceId);
                return;
            }

            const contained = targetElem.parentElement === sourceElem;

            let sourceContext = {
                contained: contained,
                getStyle: window.getComputedStyle(sourceElem),
                parentStyle: window.getComputedStyle(sourceElem.parentElement),
                targetElem: targetElem
            };
            let sourceValue = this.getValue[dependency.sourceAttr](sourceContext);

            if (dependency.multiplier !== undefined) {
                sourceValue = sourceValue * dependency.multiplier;
            }
            return {
                value: sourceValue,
                type: UI4.attrType[dependency.sourceAttr],
                contained: contained
            };
        }
    }

    getTargetContext(targetElem, dependencies) {
        return {
            dependencies: dependencies,
            targetElem: targetElem,
            getStyle: window.getComputedStyle(targetElem),
            style: targetElem.style,
            parentStyle: window.getComputedStyle(targetElem.parentElement),
            contained: false,
        };
    }

    getTargetValue(targetAttr, targetContext) {
        return {
            value: this.getValue[targetAttr](targetContext),
            type: UI4.attrType[targetAttr],
            context: targetContext,
        };
    }

    gapAdjustment(source, target, modifier=8) {
        if (source.contained) {
            if (source.type === UI4.LEADING && target.type === UI4.LEADING) {
                return modifier;
            }
            else if (source.type === UI4.TRAILING && target.type === UI4.TRAILING) {
                return -modifier;
            }
        } else {  // butting
            if (source.type === UI4.LEADING && target.type === UI4.TRAILING) {
                return -modifier;
            } else if (source.type === UI4.TRAILING && target.type === UI4.LEADING) {
                return modifier;
            }
        }

        return 0;
    }
}

var ui4 = new UI4();

ui4.startClassObserver();
window.onload = ui4.startTracking.bind(ui4);
