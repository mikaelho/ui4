/*jshint esversion: 9 */

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
        centerx: UI4.NEUTRAL,
        centery: UI4.NEUTRAL,
    };

    static composites = {
        center: ["centerx", "centery"],
        position: ["left", "top"],
        size: ["width", "height"],
        frame: ["top", "left", "width", "height"],
    }

    static parentDock = {  // Order is significant
        topleft: ["top", "left"],
        topright: ["top", "right"],
        bottomleft: ["bottom", "left"],
        bottomright: ["bottom", "right"],
        topcenter: ["top", "centerx"],
        bottomcenter: ["bottom", "centerx"],
        leftcenter: ["left", "centery"],
        rightcenter: ["right", "centery"],
        sides: ["left", "right"],
        topbottom: ["top", "bottom"],
        top: ["left", "top", "right"],
        left: ["top", "left", "bottom"],
        bottom: ["left", "bottom", "right"],
        right: ["top", "right", "bottom"],
        center: ["centerx", "centery"],
        all: ["left", "right", "top", "bottom"],
    };

    static peerDock = {
        above: {size: "width", center: "centerx", myEdge: "bottom", yourEdge: "top"},
        below: {size: "width", center: "centerx", myEdge: "top", yourEdge: "bottom"},
        rightof: {size: "height", center: "centery", myEdge: "left", yourEdge: "right"},
        leftof: {size: "height", center: "centery", myEdge: "right", yourEdge: "left"},
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

    // Parser node types
    static OPERATOR = "operator";
    static NUMBER = "number";
    static ID_AND_ATTRIBUTE = "idAndAttribute";
    static KEYWORD = "keyword";
    static FUNCTION = "function";

    constructor() {
        this._gap = 8;

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
            centerx: (context) => context.contained ?
                parseFloat(context.getStyle.width) / 2 :
                parseFloat(context.getStyle.left) + parseFloat(context.getStyle.width) / 2,
            centery: (context) => context.contained ?
                parseFloat(context.getStyle.height) / 2 :
                parseFloat(context.getStyle.top) + parseFloat(context.getStyle.height) / 2,
            fitwidth: function (context) {
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
            fitheight: function (context) {
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

        const attributeOptions = Object.keys(this.getValue).join('|');
        this.idAndAttribute = new RegExp(`(?<id>([a-zA-Z]|\\d|_|-)+)\\.(?<attribute>(${attributeOptions}))`);

        this.setValue = {
            width: function(context, value) { return {width: value + 'px'};},
            height: function(context, value) { return {height: value + 'px'};},
            left: function(context, value) { return {left: value + 'px'};},
            right: function(context, value) { return {right: parseFloat(context.parentStyle.width) - value + 'px'};},
            top: function(context, value) { return {top: value + 'px'};},
            bottom: function(context, value) { return {bottom: parseFloat(context.parentStyle.height) - value + 'px'};},
            centerx: function(context, value) {
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
            centery: function(context, value) {
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

    // Gap is the only externally-settable parameter
    get gap() {
        return this._gap;
    }

    set gap(value) {
        this._gap = value;
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

    setDependencies(node) {
        const targetId = node.id;
        if (!targetId) { return; }

        // const ui4AnimationID = node.getAttribute("ui4anim");

        const ui4Attr = this.checkStyles(node);

        if (ui4Attr) {
            let dependencies;
            try {
                dependencies = this.parseAndOrderDependencies(node, ui4Attr);
            } catch(error) {
                console.error(error);
                return;
            }
            if (!dependencies.length) {
                if (targetId in this.allDependencies) {
                    for (const dependency of this.allDependencies[targetId]) {
                        if (typeof dependency.value === 'object' && 'dependencyIDs' in dependency.value) {
                            dependency.value.dependencyIDs.forEach(
                                sourceID => delete this.sourceDependencies[sourceID][targetId]
                            );
                        }
                    }
                }
                delete this.allDependencies[targetId];
            } else {
                // dependencies = this.expandCompositeDependencies(node, dependencies);
                this.allDependencies[targetId] = dependencies;
                for (const dependency of dependencies) {
                    if (typeof dependency.value === 'object' && 'dependencyIDs' in dependency.value) {
                        dependency.value.dependencyIDs.forEach(
                            sourceID => {
                                const targetIds = this.sourceDependencies[sourceID] || {};
                                targetIds[targetId] = true;
                                this.sourceDependencies[sourceID] = targetIds;
                            }
                        );
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

    checkStyles(node) {
        // Check constraints
        const ui4Attr = this.combineConstraintAttributes(node);
        const isRootElem = node.classList.contains("ui4Root");

        if (ui4Attr || isRootElem) {
            Object.assign(node.style, UI4.elementStyles);
        }

        if (isRootElem) {
            Object.assign(node.style, UI4.rootStyles);
        }

        return ui4Attr;
    }

    combineConstraintAttributes(node) {
        let ui4Attr = node.getAttribute("ui4");
        const constraintArray = ui4Attr && ui4Attr.split(";") || [];

        for (const attribute of node.attributes) {
            const name = attribute.name;
            if (name in this.setValue || name in UI4.composites || ["dock", "fit"].includes(name)) {
                for (const singleConstraint of attribute.value.split(";")) {
                    const fullConstraint = `${attribute.name}=${singleConstraint}`;
                    constraintArray.push(fullConstraint);
                }
            }
        }
        return constraintArray.join(";");
    }

    parseAndOrderDependencies(node, specString) {
        const dependencies = this.parse(node, specString.replace(/\s/g,""));

        dependencies.sort((a, b) => UI4.ordering[a.comparison] - UI4.ordering[b.comparison]);
        return dependencies;
    }

    parse(node, specString) {
        const specs = specString.split(";");
        const dependencies = [];
        specs.forEach(spec => {
            if (!spec) { return; }  // Accidental double ";", probably

            // Process conditions and animation, if any
            let coreSpec = spec;
            const conditionAndCore = spec.split("?");
            if (conditionAndCore.length === 2) {
                coreSpec = conditionAndCore[1];
            } else if (conditionAndCore.length > 2) {
                console.error(`Too many '?' in '${spec}'`);
                return;
            }
            const coreAndAnimation = spec.split(":");
            if (coreAndAnimation.length === 2) {
                coreSpec = coreAndAnimation[0];
            } else if (coreAndAnimation.length > 2) {
                console.error(`Too many ':' in '${spec}'`);
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
                console.error(`Could not locate '=', '>' or '<' in ${spec}`);
                return;
            }

            this.parseCoreSpec(node, targetAttribute, comparison, sourceSpec, dependencies);
        });
        return dependencies;
    }

    parseCoreSpec(node, targetAttribute, comparison, sourceSpec, dependencies) {
        if (targetAttribute in this.setValue) {
            const sourceTree = new UI4.Parser().parse(sourceSpec);
            sourceTree.dependencyIDs = this.finalizeIdAndAttributeTree(sourceTree);
            dependencies.push({
                targetAttribute: targetAttribute, comparison: comparison, value: sourceTree
            });
        }
        else if (targetAttribute in UI4.composites) {
            const targetCombo = UI4.composites[targetAttribute];
            let sourceAttribute, sourceCombo;
            for (const [attribute, combo] of Object.entries(UI4.composites)) {
                if (combo.length === targetCombo.length) {
                    if (sourceSpec.includes(`.${attribute}`)) {
                        sourceAttribute = attribute;
                        sourceCombo = combo;
                        break;
                    }
                }
            }
            if (sourceAttribute) {
                targetCombo.forEach((expandedAttribute, index) => {
                    const modifiedSourceSpec = sourceSpec.replace(`.${sourceAttribute}`, `.${sourceCombo[index]}`);
                    this.parseCoreSpec(node, expandedAttribute, comparison, modifiedSourceSpec, dependencies);
                });
            }
        }
        else if (targetAttribute === "dock") {
            let peerDocked = false;
            for (const [dockAttribute, attributes] of Object.entries(UI4.peerDock)) {
                const matcher = new RegExp(`[a-zA-Z\\d_-]+\\.${dockAttribute}`);
                if (sourceSpec.match(matcher)) {
                    let modifiedSourceSpec = sourceSpec.replace(dockAttribute, attributes.size);
                    this.parseCoreSpec(node, attributes.size, comparison, modifiedSourceSpec, dependencies);

                    modifiedSourceSpec = sourceSpec.replace(dockAttribute, attributes.center);
                    this.parseCoreSpec(node, attributes.center, comparison, modifiedSourceSpec, dependencies);

                    modifiedSourceSpec = sourceSpec.replace(dockAttribute, attributes.yourEdge);
                    this.parseCoreSpec(node, attributes.myEdge, comparison, modifiedSourceSpec, dependencies);

                    peerDocked = true;
                    break;
                }
            }

            if (!peerDocked) {
                for (const [dockAttribute, attributes] of Object.entries(UI4.parentDock)) {
                    if (sourceSpec.startsWith(dockAttribute)) {
                        const parentId = node.parentNode.id;
                        attributes.forEach(attribute => {
                            const modifiedSourceSpec = sourceSpec.replace(
                                dockAttribute, `${parentId}.${attribute}`
                            );
                            this.parseCoreSpec(node, attribute, comparison, modifiedSourceSpec, dependencies);
                        });
                        break;
                    }
                }
            }
        }

        else if (targetAttribute === 'fit') {
            if (sourceSpec === "width" || sourceSpec === "true") {
                this.parseCoreSpec(node, "width", comparison, `${node.id}.fitwidth`, dependencies);
            }
            if (sourceSpec === "height" || sourceSpec === "true") {
                this.parseCoreSpec(node, "height", comparison, `${node.id}.fitheight`, dependencies);
            }
        }

        else {
            console.error(`Unknown target attribute: ${targetAttribute}`);
        }
    }

    finalizeIdAndAttributeTree(sourceTree) {
        const _this = this;
        const walker = function(node) {
            switch (node.type) {
                case UI4.ID_AND_ATTRIBUTE:
                    if (!(node.value.attribute in _this.getValue)) {
                        throw SyntaxError(`Unknown attribute in '${node.value.id}.${node.value.attribute}'`);
                    }
                    node.function = _this.getIdAndAttributeValue.bind(_this);
                    return node.value.id;  // Return dependency IDs
                case UI4.KEYWORD:
                    if (node.value !== "gap") {
                        throw SyntaxError(`Unknown keyword '${node.value}'`);
                    }
                    node.function = (targetElem, treeNode, result) => _this.gap;
                    return;
                case UI4.FUNCTION:
                    switch (node.value) {
                        case "min":
                            node.function = Math.min;
                            return;
                        case "max":
                            node.function = Math.max;
                            return;
                    }
                    throw SyntaxError(`Unknown function '${node.value}'`);
            }
        };
        const dependencyIDs = this.walkParseTree(sourceTree, walker);
        const uniqueDependencies = new Set(dependencyIDs);
        uniqueDependencies.delete(undefined);
        return [...uniqueDependencies];
    }

    getIdAndAttributeValue(targetElem, treeNode, resultContext) {
        const id = treeNode.value.id;
        const attribute = treeNode.value.attribute;
        const attributeType = UI4.attrType[attribute];
        if (!resultContext.type) {
            resultContext.type = attributeType;
        } else if (resultContext.type !== attributeType) {
            throw SyntaxError(
                `Mixed attribute types in one constraint: ${attributeType}, ${result.type}`
            );
        }
        const sourceElem = document.getElementById(id);

        if (!sourceElem) {
            throw SyntaxError(`Could not find source element with id ${id}`);
        }

        const contained = targetElem.parentElement === sourceElem;
        if (!resultContext.contained) {
            resultContext.contained = contained;
        } else if (resultContext.contained !== contained) {
            throw SyntaxError(
                'Both contained and non-contained source attributes in one constraint'
            );
        }

        let sourceContext = {
            contained: contained,
            getStyle: window.getComputedStyle(sourceElem),
            parentStyle: window.getComputedStyle(sourceElem.parentElement),
            targetElem: targetElem
        };

        return this.getValue[attribute](sourceContext);
    }

    addToDependencies(dependencies, targetAttribute, comparison, sourceSpec) {
        dependencies.push({
            targetAttribute: targetAttribute,
            comparison: comparison,
            value: this.parseSourceSpec(targetAttribute, sourceSpec),
        });
    }

    parseSourceSpec(targetAttribute, sourceSpec) {
        const keywordRE = /[a-z]+/g;
        const shareRE = /share\((?<first>\d+(\.\d+)?)(,(?<second>\d+(\.\d+)?))?\)/;

        // const contained = targetAttribute.parentElement === sourceElem;
        let sourceAttribute, sourceID;
        let source = {};

        let match = sourceSpec.match(this.idAndAttribute);
        if (match) {
            source.id = match.groups.id;
            source.attribute = match.groups.attribute;
        }
        match = sourceSpec.match(shareRE);
        if (match) {
            source.share = {share: match.groups.first, outOf: match.groups.second};
        }

        source.getFunction = validateAndCreateGetFunction(sourceSpec, source, this);

        return source;
    }

    // expandCompositeDependencies(node, dependencies) {
    //     let updatedDependencies = Array();
    //     dependencies.forEach(dependency => {
    //         if (dependency.targetAttribute in UI4.composites && dependency.value) {
    //
    //             if (dependency.targetAttribute === dependency.value.attribute) {
    //                 UI4.composites[dependency.targetAttribute].forEach(attribute => {
    //                     const cloned = structuredClone(dependency);
    //                     cloned.targetAttribute = attribute;
    //                     cloned.value.attribute = attribute;
    //                     updatedDependencies.push(cloned);
    //                 });
    //             } else {
    //                 const allowed = {center: true, position: true};
    //                 if (dependency.targetAttribute in allowed && dependency.value.attribute in allowed) {
    //                     const sourceComposite = UI4.composites[dependency.value.attribute];
    //                     UI4.composites[dependency.targetAttribute].forEach((attribute, index) => {
    //                         const cloned = structuredClone(dependency);
    //                         cloned.targetAttribute = attribute;
    //                         cloned.value.attribute = sourceComposite[index];
    //                         updatedDependencies.push(cloned);
    //                     });
    //                 }
    //             }
    //         } else if (dependency.targetAttribute === 'dock') {
    //             if ('id' in dependency.value) {
    //                 const spec = UI4.peerDock[dependency.value.attribute];
    //                 const sourceId = dependency.value.id;
    //                 updatedDependencies.push({
    //                     targetAttribute: spec.size,
    //                     comparison: '=',
    //                     value: {id: sourceId, attribute: spec.size},
    //                 });
    //                 updatedDependencies.push({
    //                     targetAttribute: spec.center,
    //                     comparison: '=',
    //                     value: {id: sourceId, attribute: spec.center},
    //                 });
    //                 const cloned = structuredClone(dependency);
    //                 cloned.targetAttribute = spec.myEdge;
    //                 cloned.value.attribute = spec.yourEdge;
    //                 updatedDependencies.push(cloned);
    //             } else {
    //                 const parentId = node.parentNode.id;
    //                 UI4.parentDock[dependency.value.attribute].forEach(attribute => {
    //                     const cloned = structuredClone(dependency);
    //                     cloned.targetAttribute = attribute;
    //                     cloned.value.id = parentId;
    //                     cloned.value.attribute = attribute;
    //                     updatedDependencies.push(cloned);
    //                 });
    //             }
    //         } else if (dependency.targetAttribute === 'fit') {
    //             const fitKeyword = dependency.value.attribute;
    //             if (fitKeyword === "width" || fitKeyword === "true") {
    //                 updatedDependencies.push({
    //                     targetAttribute: "width",
    //                     comparison: '=',
    //                     value: {id: node.id, attribute: "fitwidth"},
    //                 });
    //             }
    //             if (fitKeyword === "height" || fitKeyword === "true") {
    //                 updatedDependencies.push({
    //                     targetAttribute: "height",
    //                     comparison: '=',
    //                     value: {id: node.id, attribute: "fitheight"},
    //                 });
    //             }
    //         } else {
    //             updatedDependencies.push(dependency);
    //         }
    //     });
    //     return updatedDependencies;
    // }

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
        const toCheck = [];
        const seen = {};
        let findDependants = [];
        entries.forEach(entry => {
            const sourceNode = entry.target;
            if (sourceNode) {
                const sourceID = sourceNode.id;
                if (sourceID && !(sourceID in seen)) {
                    toCheck.push(sourceID);
                    findDependants.push(sourceID);
                    seen[sourceID] = 1;
                }
            }
        });

        while (findDependants.length > 0) {
            const toExpand = findDependants.shift();
            const dependants = this.sourceDependencies[toExpand];
            if (dependants) {
                Object.keys(dependants).forEach(dependantID => {
                    const seenCount = seen[dependantID] || 0;
                    if (seenCount > 3) {  // Allow little circularity
                        return;
                    }
                    toCheck.push(dependantID);
                    findDependants.push(dependantID);
                    seen[dependantID] = seenCount + 1;
                });
            }

        }
        for (const targetId of toCheck) {
            if (targetId in this.allDependencies) {
                this.checkDependenciesFor(targetId);
            }
        }
    }

    checkDependencies() {
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
            // if ('animation' in dependency && dependency.animation.running) {
            //     redrawNeeded = true;
            //     return;
            // }
            //
            // if (!this.checkCondition(targetElem, dependency)) {
            //     return;
            // }

            const sourceContext = {};
            let sourceValue = this.resolveSourceTree(targetElem, dependency.value, sourceContext);

            if (sourceValue === undefined) {
                return;
            }

            let targetContext = this.getTargetContext(targetElem, dependencies);
            let target = this.getTargetValue(dependency.targetAttribute, targetContext);

            sourceValue += this.gapAdjustment(sourceContext, target);

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

    resolveSourceTree(targetElem, treeNode, resultContext) {
        if (treeNode.type === UI4.NUMBER) {
            return treeNode.value;
        }
        else if (treeNode.type === UI4.OPERATOR) {
            const left = this.resolveSourceTree(targetElem, treeNode.left, resultContext);
            const right = this.resolveSourceTree(targetElem, treeNode.right, resultContext);
            return UI4.operations[treeNode.operator](left, right);
        }
        else if ([UI4.ID_AND_ATTRIBUTE, UI4.KEYWORD].includes(treeNode.type)) {
            return treeNode.function(targetElem, treeNode, resultContext);
        }
        else if (treeNode.type === UI4.FUNCTION) {
            const functionArguments = [];
            for (const attributeTreeNode of treeNode.arguments) {
                functionArguments.push(this.resolveSourceTree(targetElem, attributeTreeNode, resultContext));
            }
            return treeNode.function(...functionArguments);
        }
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
        if ('id' in sourceSpec) {
            return this.processSourceAttribute(targetElem, sourceSpec);
        }
        else if (sourceSpec.attribute === "constant") {
            return {
                value: sourceSpec.valueFunction(this.gap),
                type: UI4.attrType[sourceSpec.attribute],
                contained: true,
            };
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
            value: this.getValue[sourceSpec.attribute](sourceContext),
            type: UI4.attrType[sourceSpec.attribute],
            contained: contained,
        };

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

    // UTILITIES

    walkParseTree(treeNode, walker) {
        let result = [walker(treeNode)];

        if (treeNode.left) {
            result = result.concat(this.walkParseTree(treeNode.left, walker));
        }
        if (treeNode.right) {
            result = result.concat(this.walkParseTree(treeNode.right, walker));
        }
        if (treeNode.arguments) {
            treeNode.arguments.forEach(argument => result = result.concat(this.walkParseTree(argument, walker)));
        }

        return result;
    }

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

// UI4 ATTRIBUTE PARSER

UI4.Parser = class {

    constructor() {
        // Tokens - Basic math
        this.OPERATOR = "operator";
        this.LEFT_PARENTHESIS = "leftParenthesis";
        this.RIGHT_PARENTHESIS = "rightParenthesis";
        this.NUMBER = "number";

        // Tokens - Application-specific
        this.ID_AND_ATTRIBUTE = "idAndAttribute";
        this.KEYWORD = "keyword";
        this.FUNCTION = "function";
        this.COMMA = "comma";

        this.AS_IS_TYPES = [this.ID_AND_ATTRIBUTE, this.KEYWORD];

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
    }

    parse(string) {
        string = string.replace(' ', '');
        if (string.length === 0) {
            return {};
        }

        this.tokens = this.tokenize(string);
        return this.additive();
    }

    * tokenize(string) {
        let index = 0;
        string = string.replace(' ', '');
        while (index < string.length) {
            const match = string.substring(index).match(this.matcher);

            if (!match) {
                throw new SyntaxError(`Could not recognize token starting from "${string.substring(index)}"`);
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

    additive() {
        let left = this.multiplicative()
        let token = this.peekToken();
        while (token && token.type === this.OPERATOR && (token.value === '+' || token.value === '-')) {
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
        while (token && token.type === this.OPERATOR && (token.value === '*' || token.value === '/')) {
            this.skipToken();
            const right = this.primary();
            left = this.getNode(token.value, left, right);
            token = this.peekToken();
        }
        return left;
    }

    primary() {
        let token = this.peekToken();
        if (token && token.type === this.NUMBER) {
            this.skipToken();
            return {type: this.NUMBER, value: parseFloat(token.value)};
        } else if (token && token.type === this.ID_AND_ATTRIBUTE) {
            this.skipToken();
            const [id, attribute] = token.value.split(".");
            return {type: this.ID_AND_ATTRIBUTE, value: {id: id, attribute: attribute}};
        } else if (token && token.type === this.KEYWORD) {
            this.skipToken();
            return {type: this.KEYWORD, value: token.value};
        } else if (token && token.type === this.FUNCTION) {
            const functionName = token.value;
            this.skipToken();
            token = this.getToken();
            if (!token || token.type !== this.LEFT_PARENTHESIS) {
                throw new SyntaxError(
                    `Function name should be followed by parenthesis`
                );
            }
            return {type: this.FUNCTION, value: functionName, arguments: this.arguments()};
        } else if (token && token.type === this.LEFT_PARENTHESIS) {
            this.skipToken();
            const node = this.additive();
            token = this.getToken();
            if (!token || token.type !== this.RIGHT_PARENTHESIS) {
                throw new SyntaxError('Missing closing parenthesis');
            }
            return node;
        } else {
            throw new SyntaxError(`Unexpected ${token.type}: ${token.value}`);
        }
    }

    arguments() {
        let argument = this.additive();
        let token = this.getToken();
        if (token && token.type === this.COMMA) {
            return [argument].concat(this.arguments());
        } else if (token && token.type === this.RIGHT_PARENTHESIS) {
            return [argument];
        } else {
            throw new SyntaxError(`Expected comma or closing parenthesis in function arguments, got: ${token}`);
        }
    }

    getNode(operator, left, right) {
        // Return a node combining the operator and left and right sides, or if possible, already calculated number node
        const operations = {"+": (a, b) => a + b, "-": (a, b) => a - b, "*": (a, b) => a * b, "/": (a, b) => a / b};
        if ((left && left.type === this.NUMBER) && (right && right.type === this.NUMBER)) {
            return {type: this.NUMBER, value: operations[operator](left.value, right.value)};
        } else {
            return {type: this.OPERATOR, operator: operator, left: left, right: right};
        }
    }
};

var ui4 = new UI4();

ui4.startClassObserver();
//window.onload = ui4.startTracking.bind(ui4);

// Export only for tests under Node
if (new Function("try {return this === global;} catch(e) {return false;}")()) { module.exports = UI4; }
