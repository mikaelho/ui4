/*jshint esversion: 9 */

// Depends on globals:
// parse - the ui4 attribute value parser, from ui4parser.js
// const parse = this.null.parse;  // From ui4parser.js

// import { parse } from './ui4parser.js';

function getSourceID(sourceSpec) {
    const idCatcher = {};
    const idCatcherProxy = new Proxy(idCatcher, {
        get(target, name, receiver) {
            if (name !== '_ui4_sourceID') {
                if (target._ui4_sourceID === undefined) {
                    target._ui4_sourceID = name;
                }
                return 0;
            } else {
                return target._ui4_sourceID;
            }
        }
    });

    let left, right, top, bottom, centerX, centerY, width, height;
    left = right = top = bottom = centerX = centerY = width = height = idCatcherProxy;
    const gap = 0;
    try {
        eval(sourceSpec);
    }
    catch (ReferenceError) {}

    return idCatcherProxy._ui4_sourceID;  // May be undefined
}

function createGetFunction(sourceSpec, _this) {
    return (
        function(sourceID, sourceAttribute, context) {
            const attributeGetProxy = new Proxy(
                {},
                {
                    get(target, name) {
                        if (name === sourceID) {
                            return _this.getValue[sourceAttribute](context);
                        }
                        return 0;
                    }
                }
            );
            let left, right, top, bottom, centerX, centerY, width, height;
            left = right = top = bottom = centerX = centerY = width = height = attributeGetProxy;
            const gap = _this.gap;
            return eval(sourceSpec);
        }
    );
}

class UI4 {

    static rootStyles = {
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        padding: 0
    };

    static elementStyles = {
        position: "absolute",
        margin: 0,
        outline: 0,
        padding: 0,
        "box-sizing": "border-box"
    }

    static lhsKeywords = "dock fit left right top bottom centerX centerY center position size frame".split(" ");

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

    static parentDock = {
        top: ["left", "top", "right"],
        left: ["top", "left", "bottom"],
        bottom: ["left", "bottom", "right"],
        right: ["top", "right", "bottom"],
        topLeft: ["top", "left"],
        topRight: ["top", "right"],
        bottomLeft: ["bottom", "left"],
        bottomRight: ["bottom", "right"],
        center: ["centerX", "centerY"],
        topCenter: ["top", "centerX"],
        bottomCenter: ["bottom", "centerX"],
        leftCenter: ["left", "centerY"],
        rightCenter: ["right", "centerY"],
        sides: ["left", "right"],
        top_and_bottom: ["top", "bottom"],
        all: ["left", "right", "top", "bottom"],
    };

    static composites = {
        center: ["centerX", "centerY"],
        position: ["left", "top"],
        size: ["width", "height"],
        frame: ["top", "left", "width", "height"],
    }

    static peerDock = {
        above: {size: "width", center: "centerX", myEdge: "bottom", yourEdge: "top"},
        below: {size: "width", center: "centerX", myEdge: "top", yourEdge: "bottom"},
        rightOf: {size: "height", center: "centerY", myEdge: "left", yourEdge: "right"},
        leftOf: {size: "height", center: "centerY", myEdge: "right", yourEdge: "left"},
    }

    static operations = {
        "+": (a, b) => a + b,
        "-": (a, b) => a - b,
        "*": (a, b) => a * b,
        "/": (a, b) => a / b,
        "min": Math.min,
        "max": Math.max,
    };
    static comparisons = {"=": (a, b) => a !== b, "<": (a, b) => a >= b, ">": (a, b) => a <= b};
    static ordering = {"=": 0, "<": 1, ">": 2};
    static conditions = {"=": (a, b) => a === b, "<": (a, b) => a < b, ">": (a, b) => a > b};

    constructor() {
        this.gap = 8;

        this.callLog = [];

        this.allDependencies = {};
        this.sourceDependencies = {};

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
                if (context.dependencies.find(item => item.targetAttribute === 'left')) {  // left locked, width must give
                    return {width: 2 * (value - parseFloat(context.getStyle.left)) + 'px'};
                } else if (context.dependencies.find(item => item.targetAttribute === 'right')) {  // width must give)
                    return {
                        width: 2 * (parseFloat(context.parentStyle.width) -
                            parseFloat(context.getStyle.right) - value) + 'px'
                    };
                } else {  // Neither locked, move left
                    return {left: value - parseFloat(context.getStyle.width) / 2 + 'px'};
                }
            },
            centerY: function(context, value) {
                if (context.dependencies.find(item => item.targetAttribute === 'top')) {  // top locked, height must give
                    return {height: 2 * (value - parseFloat(context.getStyle.top)) + 'px'};
                } else if (context.dependencies.find(item => item.targetAttribute === 'bottom')) {  // height must give)
                    return {
                        height: 2 * (parseFloat(context.parentStyle.height) -
                            parseFloat(context.getStyle.bottom) - value) + 'px'
                    };
                } else {  // Neither locked, move top
                    return {top: value - parseFloat(context.getStyle.height) / 2 + 'px'};
                }
            }
        };

        this.valueProxies = {};
        Object.keys(this.getValue).forEach(attribute => {
            this.valueProxies[attribute] = new Proxy({}, {
                get(target, name, receiver) {
                    return 2;
                }
}           );
        });
    }

    setGap(gap) {
        this.gap = gap;
        this.checkDependencies();
    }

    setResizeObserver(node) {
        const sourceID = node.id;
        if (!sourceID) { return; }
        const resizeObserver = new ResizeObserver(this.checkSourceDependencies.bind(this));
        resizeObserver.observe(node);
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
                        if (node.id) {
                            this.setDependencies(node);
                            this.setResizeObserver(node);
                        }
                    });
                    break;
                case 'attributes':
                    if (mutation.target.id) {
                        this.setDependencies(mutation.target);
                        this.setResizeObserver(mutation.target);
                    }
                    break;
            }
        });
    }

    startTracking() {
        const observer = new MutationObserver(this.checkDependencies.bind(this));
        observer.observe(document.body, {
            subtree: true,
            childList: true,
            attributeFilter: ["style"]
        });
        this.checkDependencies();
    }

    combineConstraintAttributes(node) {
        let ui4Attr = node.getAttribute('ui4');

        for (const attributeName of node.getAttributeNames()) {
            if (attributeName.startsWith('ui4-')) {
                const constraintValue = node.getAttribute(attributeName);
                if (constraintValue) {
                    if (!ui4Attr.endsWith(';')) {
                        ui4Attr += ';';
                    }
                    ui4Attr += attributeName.substring('ui4-'.length) + '=' + constraintValue;
                }
            }
        }

        return ui4Attr;
    }

    setDependencies(node) {
        const targetId = node.id;
        if (!targetId) { return; }

        // const ui4AnimationID = node.getAttribute("ui4anim");

        // Check constraints
        const ui4Attr = this.combineConstraintAttributes(node);
        const isRootElem = node.classList.contains("ui4Root");

        if (ui4Attr || isRootElem) {
            Object.assign(node.style, UI4.elementStyles);
        }

        if (isRootElem) {
            Object.assign(node.style, UI4.rootStyles);
        }

        if (ui4Attr) {
            let dependencies;
            try {
                dependencies = this.parseAndOrderDependencies(ui4Attr);
            } catch(error) {
                console.error(error);
                return;
            }
            if (!dependencies.length) {
                if (targetId in this.allDependencies) {
                    for (const dependency of this.allDependencies[targetId]) {
                        if (typeof dependency.value === 'object' && 'id' in dependency.value) {
                            const sourceID = dependency.value.id;
                            delete this.sourceDependencies[sourceID][targetId];
                        }
                    }
                }
                delete this.allDependencies[targetId];
            } else {
                // dependencies = this.expandCompositeDependencies(node, dependencies);
                this.allDependencies[targetId] = dependencies;
                for (const dependency of dependencies) {
                    if (typeof dependency.value === 'object' && 'id' in dependency.value) {
                        const sourceID = dependency.value.id;
                        const targetIds = this.sourceDependencies[sourceID] || {};
                        targetIds[targetId] = true;
                        console.log(sourceID + " -> " + JSON.stringify(targetIds));
                        this.sourceDependencies[sourceID] = targetIds;
                    }
                }
            }
        }
        /*
        // Check animated styles
        const ui4Style = node.getAttribute('ui4style');

        if (ui4Style) {
            let styles;
            try {
                styles = parse(ui4Style.replace(/\s/g,''), {startRule: 'styles'});
            } catch(error) {
                console.error(error.toString());
                return;
            }
            if (styles) {
                this.startCSSAnimations(node, styles);
            }
        }
        */
        // Check children, since mutation observer only seems to pick the root of changes
        node.childNodes.forEach(childNode => this.setDependencies(childNode));
    }

    parseAndOrderDependencies(specString) {
        const dependencies = this.parse(specString.replace(/\s/g,""));

        dependencies.sort((a, b) => UI4.ordering[a.comparison] - UI4.ordering[b.comparison]);
        return dependencies;
    }

    parse(specString) {
        const specs = specString.split(";");
        const dependencies = [];
        specs.forEach(spec => {
            if (!spec) { return; }  // Accidental double ";" or similar

            // Process conditions and animation, if any
            let coreSpec = spec;
            const conditionAndCore = spec.split("?");
            if (conditionAndCore.length === 2) {
                coreSpec = conditionAndCore[1];
            } else if (conditionAndCore.length > 2) {
                console.log(`Too many '?' in '${spec}'`);
                return;
            }
            const coreAndAnimation = spec.split(":");
            if (coreAndAnimation.length === 2) {
                coreSpec = coreAndAnimation[0];
            } else if (coreAndAnimation.length > 2) {
                console.log(`Too many ':' in '${spec}'`);
                return;
            }
            let targetAttribute, comparison, sourceSpec;
            for (const comparisonCandidate of Object.keys(UI4.comparisons)) {
                const targetAttributeAndSourceSpec = coreSpec.split(comparisonCandidate);
                if (targetAttributeAndSourceSpec.length === 2) {
                    targetAttribute = targetAttributeAndSourceSpec[0];
                    comparison = comparisonCandidate;
                    sourceSpec = targetAttributeAndSourceSpec[1];
                    break;
                }
            }
            if (comparison === undefined) {
                console.log(`Could not locate '=', '>' or '<' in ${spec}`);
                return;
            }
            if (!(targetAttribute in this.setValue)) {
                console.log(`Unknown target attribute in ${spec}: ${targetAttribute}`);
                return;
            }
            dependencies.push({
                targetAttribute: targetAttribute,
                comparison: comparison,
                value: this.parseSourceSpec(targetAttribute, sourceSpec),
            });
        });
        return dependencies;
    }

    parseSourceSpec(targetAttribute, sourceSpec) {
        // const contained = targetAttribute.parentElement === sourceElem;
        let sourceAttribute, sourceID;
        for (const attributeCandidate in this.setValue) {
            if (sourceSpec.startsWith(attributeCandidate)) {
                sourceAttribute = attributeCandidate;
                break;
            }
        }
        if (sourceAttribute) {
            sourceID = getSourceID(sourceSpec);  // May be undefined
        } else {
            sourceAttribute = "constant";
        }
        const source = {
            attribute: sourceAttribute,
        };
        if (sourceID !== undefined) {
            source.id = sourceID;
            source.valueFunction = createGetFunction(sourceSpec, this);
        } else {
            const toEvaluate = `(function(gap) {return ${sourceSpec};})`;
            source.valueFunction = eval(toEvaluate);
        }
        return source;
    }

    expandCompositeDependencies(node, dependencies) {
        let updatedDependencies = Array();
        dependencies.forEach(dependency => {
            if (dependency.targetAttribute in UI4.composites && dependency.value) {

                if (dependency.targetAttribute === dependency.value.attribute) {
                    UI4.composites[dependency.targetAttribute].forEach(attribute => {
                        const cloned = structuredClone(dependency);
                        cloned.targetAttribute = attribute;
                        cloned.value.attribute = attribute;
                        updatedDependencies.push(cloned);
                    });
                } else {
                    const allowed = {center: true, position: true};
                    if (dependency.targetAttribute in allowed && dependency.value.attribute in allowed) {
                        const sourceComposite = UI4.composites[dependency.value.attribute];
                        UI4.composites[dependency.targetAttribute].forEach((attribute, index) => {
                            const cloned = structuredClone(dependency);
                            cloned.targetAttribute = attribute;
                            cloned.value.attribute = sourceComposite[index];
                            updatedDependencies.push(cloned);
                        });
                    }
                }
            } else if (dependency.targetAttribute === 'dock') {
                if ('id' in dependency.value) {
                    const spec = UI4.peerDock[dependency.value.attribute];
                    const sourceId = dependency.value.id;
                    updatedDependencies.push({
                        targetAttribute: spec.size,
                        comparison: '=',
                        value: {id: sourceId, attribute: spec.size},
                    });
                    updatedDependencies.push({
                        targetAttribute: spec.center,
                        comparison: '=',
                        value: {id: sourceId, attribute: spec.center},
                    });
                    const cloned = structuredClone(dependency);
                    cloned.targetAttribute = spec.myEdge;
                    cloned.value.attribute = spec.yourEdge;
                    updatedDependencies.push(cloned);
                } else {
                    const parentId = node.parentNode.id;
                    UI4.parentDock[dependency.value.attribute].forEach(attribute => {
                        const cloned = structuredClone(dependency);
                        cloned.targetAttribute = attribute;
                        cloned.value.id = parentId;
                        cloned.value.attribute = attribute;
                        updatedDependencies.push(cloned);
                    });
                }
            } else if (dependency.targetAttribute === 'fit') {
                const fitKeyword = dependency.value.attribute;
                if (fitKeyword === "width" || fitKeyword === "true") {
                    updatedDependencies.push({
                        targetAttribute: "width",
                        comparison: '=',
                        value: {id: node.id, attribute: "fitWidth"},
                    });
                }
                if (fitKeyword === "height" || fitKeyword === "true") {
                    updatedDependencies.push({
                        targetAttribute: "height",
                        comparison: '=',
                        value: {id: node.id, attribute: "fitHeight"},
                    });
                }
            } else {
                updatedDependencies.push(dependency);
            }
        });
        return updatedDependencies;
    }

    startCSSAnimations(elem, styles) {
        const startingStyles = window.getComputedStyle(elem);

        styles.forEach((targetStyle) => {
            //const animationID = spec.animationID;
            const key = this.toCamelCase(targetStyle.key);
            const fromFrame = {};
            fromFrame[key] = startingStyles[targetStyle.key];
            const toFrame = {};
            toFrame[key] = targetStyle.value;

            const animation = elem.animate([fromFrame, toFrame], targetStyle.options);
        });
    }

    checkSourceDependencies(entries) {
        entries.forEach(entry => {
            const sourceNode = entry.target;
            if (!sourceNode || !sourceNode.id) {
                return;
            }
            console.log("Source ID " + sourceNode.id + " deps " + Object.keys(this.sourceDependencies).length);
            const dependants = this.sourceDependencies[sourceNode.id];
            if (dependants) {
                console.log(sourceNode.id + " dependants " + dependants);
                for (const targetId of Object.keys(dependants)) {
                    this.checkDependenciesFor(targetId);
                }
            }
        });
    }

    checkDependencies() {
        this.callLog.push("checkDependencies");
        this.checkAllDependencies();
    }

    checkAllDependencies() {
        let redrawNeeded = false;
        for (const [targetId, dependencies] of Object.entries(this.allDependencies)) {
            redrawNeeded = this.checkDependenciesFor(targetId, dependencies);
        }
        if (redrawNeeded) {
            requestAnimationFrame(this.checkDependencies.bind(this));
        }
    }

    checkDependenciesFor(targetId) {
        let redrawNeeded = false;

        let checkResults = this.checkResults(targetId);

        let finalValues = checkResults[0];
        if (checkResults[1]) {
            redrawNeeded = true;
        }

        // Apply the final value for each attribute
        for (const [targetAttribute, data] of Object.entries(finalValues)) {
            const updates = this.setValue[targetAttribute](data.context, data.sourceValue);
            for (const [key, value] of Object.entries(updates)) {
                if (data.context.style[key] !== value) {
                    data.context.style[key] = value;
                }
            }
        }

        return redrawNeeded;
    }

    checkResults(targetId) {
        const targetElem = document.getElementById(targetId);
        const dependencies = this.allDependencies[targetId];
        let values = {};
        let redrawNeeded = false;

        dependencies.forEach(dependency => {
            if ('animation' in dependency && dependency.animation.running) {
                redrawNeeded = true;
                return;
            }

            if (!this.checkCondition(targetElem, dependency)) {
                return;
            }

            const source = this.processSourceSpec(targetElem, dependency.value);

            if (source === undefined) {
                return;
            }

            let targetContext = this.getTargetContext(targetElem, dependencies);
            let target = this.getTargetValue(dependency.targetAttribute, targetContext);

            let sourceValue = source;
            if (typeof source !== 'number') {
                sourceValue = source.value;
                sourceValue += this.gapAdjustment(source, target);
            }

            const result = {
                targetElem: targetElem,
                targetValue: target.value,
                sourceValue: sourceValue,
                context: target.context
            };
            const previousResult = values[dependency.targetAttribute];
            let setValue;

            if (previousResult) {
                if (UI4.comparisons[dependency.comparison](previousResult.sourceValue, sourceValue)) {
                    setValue = result;
                }
            } else if (UI4.comparisons[dependency.comparison](target.value, sourceValue)) {
                setValue = result;
            } else if ('animation' in dependency && !dependency.animation.running) {
                delete dependency.animation;
                setValue = result;
            }

            if (setValue !== undefined) {
                if ('animation' in dependency) {
                    this.startAnimation(dependency.targetAttribute, result, dependency);
                } else {
                    values[dependency.targetAttribute] = setValue;
                }
            }
        });

        return [values, redrawNeeded];
    }

    checkCondition(targetElem, dependency) {
        const condition = dependency.condition;

        if (condition === undefined) {
            return true;
        }

        if ('aspect' in condition) {
            let referenceElement;
            if ('elemId' in condition) {
                referenceElement = document.getElementById(condition.elemId);
                if (!referenceElement) {
                    console.error('Could not find source element with id ' + condition.elemId);
                    return false;
                }
            } else {
                referenceElement = targetElem.parentElement;
            }
            const referenceStyle = window.getComputedStyle(referenceElement);
            if (condition.aspect === 'portrait') {
                return referenceStyle.width < referenceStyle.height;
            } else {
                return referenceStyle.width > referenceStyle.height;
            }
        }
        else if ('comparison' in condition) {
            let lhsValue = this.processSourceSpec(targetElem, condition.lhs);
            let rhsValue = this.processSourceSpec(targetElem, condition.rhs);
            if (typeof lhsValue !== 'number') {
                lhsValue = lhsValue.value;
            }
            if (typeof rhsValue !== 'number') {
                rhsValue = rhsValue.value;
            }
            return UI4.conditions[condition.comparison](lhsValue, rhsValue);
        }
    }

    processSourceSpec(targetElem, sourceSpec) {
        console.log("Source spec " + JSON.stringify(sourceSpec));
        if (typeof sourceSpec === 'number') {
            return sourceSpec;
        }
        // else if (sourceSpec === 'gap') {
        //     return this.gap;
        // }
        else if ('id' in sourceSpec) {
            return this.processSourceAttribute(targetElem, sourceSpec);
        }
        else if (sourceSpec.attribute === "constant") {
            return {
                value: sourceSpec.valueFunction(this.gap),
                type: UI4.attrType[sourceSpec.attribute],
                contained: true,
            };
        }
        else if ('operation' in sourceSpec) {
            let lhs = this.processSourceSpec(targetElem, sourceSpec.lhs);
            let rhs = this.processSourceSpec(targetElem, sourceSpec.rhs);
            if (typeof lhs !== 'number') {
                lhs = lhs.value;
            }
            if (typeof rhs !== 'number') {
                rhs = rhs.value;
            }
            return UI4.operations[sourceSpec.operation](lhs, rhs);
        }
        else if ('func' in sourceSpec) {
            const _this = this;
            const values = sourceSpec.values.map(function(item) {
                let value = _this.processSourceSpec(targetElem, item);
                if (typeof value !== 'number') {
                    value = value.value;
                }
                return value;
            });
            return UI4.operations[sourceSpec.func](...values);
        }
    }

    processSourceAttribute(targetElem, sourceSpec) {
        const sourceElem = document.getElementById(sourceSpec.id);

        if (!sourceElem) {
            console.error('Could not find source element with id ' + sourceSpec.id);
            return;
        }

        const contained = targetElem.parentElement === sourceElem;

        let sourceContext = {
            contained: contained,
            getStyle: window.getComputedStyle(sourceElem),
            parentStyle: window.getComputedStyle(sourceElem.parentElement),
            targetElem: targetElem
        };
        const source = {
            value: sourceSpec.valueFunction(sourceElem.id, sourceSpec.attribute, sourceContext),  //this.getValue[sourceSpec.attribute](sourceContext),
            type: UI4.attrType[sourceSpec.attribute],
            contained: contained,
        };
        console.log("Source " + JSON.stringify(source));

        return source;
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

    getTargetValue(targetAttribute, targetContext) {
        return {
            value: this.getValue[targetAttribute](targetContext),
            type: UI4.attrType[targetAttribute],
            context: targetContext,
        };
    }

    gapAdjustment(source, target) {
        if (source.contained) {
            if (source.type === UI4.LEADING && target.type === UI4.LEADING) {
                return this.gap;
            }
            else if (source.type === UI4.TRAILING && target.type === UI4.TRAILING) {
                return -this.gap;
            }
        } else {  // butting
            if (source.type === UI4.LEADING && target.type === UI4.TRAILING) {
                return -this.gap;
            } else if (source.type === UI4.TRAILING && target.type === UI4.LEADING) {
                return this.gap;
            }
        }

        return 0;
    }

    startAnimation(targetAttr, data, dependency) {
        const animationOptions = dependency.animation;
        if ('iterations' in animationOptions && animationOptions.iterations === 0) {
            animationOptions.iterations = Infinity;
        }
        const animation = data.targetElem.animate(
         [
             this.setValue[targetAttr](data.context, data.targetValue),
             this.setValue[targetAttr](data.context, data.sourceValue)
         ],
         animationOptions
        );
        animationOptions.running = true;
        animation.onfinish = function() {
            dependency.animation.running = false;
        };
    }

    // Utilities

    toCamelCase(variableName) {
        return variableName.replace(
            /-([a-z])/g,
            function(str, letter) {
                return letter.toUpperCase();
            }
        );
    }

    dimensions(count, width, height) {
        const initialX = Math.min(count, Math.sqrt(count * width / height));
        const initialY = Math.min(count, Math.sqrt(count * height / width));
        const operations = [
            [Math.floor, Math.floor],
            [Math.floor, Math.ceil],
            [Math.ceil, Math.floor],
            [Math.ceil, Math.ceil],
        ];
        let best, bestX, bestY;
        operations.forEach(operation => {
            const candidateX = operation[0](initialX);
            const candidateY = operation[1](initialY);
            const delta = candidateX * candidateY - count;
            if (delta >= 0) {
                if (best === undefined || delta < best) {
                    best = delta;
                    bestX = candidateX;
                    bestY = candidateY;
                }
            }
        });
        return {x: bestX, y: bestY};
    }
}

var ui4 = new UI4();

ui4.startClassObserver();
//window.onload = ui4.startTracking.bind(ui4);
