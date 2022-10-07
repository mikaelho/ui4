/*jshint esversion: 9 */

(function (ui4, globals, undefined) {
  'use strict';

  ui4.testHook = {initialized: 'true'};

  //let gap = 8;  // Defined outside the file
  let allDependencies = {};
  let animatedDependencies = {};
  let animatedCSS = {};
  let animating = {};

  const LEADING = "leading", TRAILING = "trailing", NEUTRAL = "neutral", CONSTANT = 'constant';

  const attrType = {
    constant: NEUTRAL,
    width: NEUTRAL,
    height: NEUTRAL,
    left: LEADING,
    right: TRAILING,
    top: LEADING,
    bottom: TRAILING,
    centerX: NEUTRAL,
    centerY: NEUTRAL,
  };

  // If true, set target to source
  const comparisons = {
    "=": (a, b) => a !== b,
    "<": (a, b) => a >= b,
    ">": (a, b) => a <= b
  };
  
  const mediaRequire = {
    portrait: "(orientation:portrait)",
    landscape: "(orientation:landscape)"
  };

  const getValue = {
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
      return right - left + 2 * gap;
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
      return bottom - top + 2 * gap;
    }
  };

  const setValue = {
    width: function(context, value) { return {width: value + 'px'};},
    height: function(context, value) { return {height: value + 'px'};},
    left: function(context, value) { return {left: value + 'px'};},
    right: function(context, value) { return {right: parseFloat(context.parentStyle.width) - value + 'px'};},
    top: function(context, value) { return {top: value + 'px'};},
    bottom: function(context, value) { return {bottom: parseFloat(context.parentStyle.height) - value + 'px'};},
    centerX: function(context, value) {
      if (context.dependencies.find(item => item.targetAttr === 'left')) {  // left locked, width must give
        return {width: 2 * (value - parseFloat(context.getStyle.left)) + 'px'};
      } else if (context.dependencies.find(item => item.targetAttr === 'right')) {  // right locked, width must give)
        return {
          width: 2 * (parseFloat(context.parentStyle.width) - parseFloat(context.getStyle.right) - value) + 'px'
        };
      } else {  // Neither locked, move left
        return {left: value - parseFloat(context.getStyle.width) / 2 + 'px'};
      }
    },
    centerY: function(context, value) {
      if (context.dependencies.find(item => item.targetAttr === 'top')) {  // top locked, height must give
        return {height: 2 * (value - parseFloat(context.getStyle.top)) + 'px'};
      } else if (context.dependencies.find(item => item.targetAttr === 'bottom')) {  // bottom locked, height must give)
        return {
          height: 2 * (parseFloat(context.parentStyle.height) - parseFloat(context.getStyle.bottom) - value) + 'px'
        };
      } else {  // Neither locked, move top
        return {top: value - parseFloat(context.getStyle.height) / 2 + 'px'};
      }
    }
  };

  ui4.checkDependencies = function() {
    checkAllDependencies();
    checkAnimationDependencies();
    checkCSSAnimations();
    checkAnimationStepComplete();
  };

  function checkAllDependencies() {
    for (const [targetId, dependencies] of Object.entries(allDependencies)) {
      let finalValues = checkElementDependencies(targetId, dependencies);
      // Apply the final value for each attribute
      for (const [targetAttr, data] of Object.entries(finalValues)) {
        const updates = setValue[targetAttr](data.context, data.sourceValue);
        for (const [key, value] of Object.entries(updates)) {
          data.context.style[key] = value;
        }
      }
    }
  }

  function checkAnimationDependencies() {
    for (const [targetId, dependencies] of Object.entries(animatedDependencies)) {

      let values = checkElementDependencies(targetId, dependencies);

      dependencies.forEach((dependency) => {
        const animationID = dependency.animationID;
        let data = values[dependency.targetAttr];
        const options = animationOptions(dependency);

        let animation = data.targetElem.animate(
         [
             setValue[dependency.targetAttr](data.context, data.targetValue),
             setValue[dependency.targetAttr](data.context, data.sourceValue)
         ],
         options
        );

        if (animationID) {
          if (animating[animationID]) {
            animating[animationID].push(animation);
          } else {
            animating[animationID] = [animation];
          }
        }

        animation.onfinish = function() {
          if (allDependencies[targetId]) {
            allDependencies[targetId].push(dependency);
          } else {
            allDependencies[targetId] = [dependency];
          }
          if (animationID) {
            animating[animationID].pop();
            //checkAnimationStepComplete();
          }
          ui4.checkDependencies();
        };
        //requestAnimationFrame(updateDependenciesWhileAnimating);
      });
      animatedDependencies = {};
    }
  }

  function checkElementDependencies(targetId, dependencies) {
    console.log("ID " + targetId);

    let targetElem = document.getElementById(targetId);
    let values = {};
    let sourceValue;
    let sourceType;
    let contained = false;

    dependencies.forEach(dependency => {
      console.log(dependency.targetAttr);
      if ('key' in dependency) {
        const sourceValues = [];
        dependency.list.forEach(subDependency => {
          const subSourceValue = getSourceValue(targetElem, subDependency);
          if (subSourceValue !== undefined) {
            sourceValues.push(subSourceValue.sourceValue);
            contained = subSourceValue.contained;
            sourceType = attrType[subDependency.sourceAttr];
            console.log("CONT "+contained);
          }
        });
        sourceValue = Math[dependency.key](...sourceValues);
      } else {
        const sourceValueData = getSourceValue(targetElem, dependency);
        if (sourceValueData !== undefined) {
          sourceValue = sourceValueData.sourceValue;
          contained = sourceValueData.contained;
          sourceType = attrType[dependency.sourceAttr];
        }
      }

      if (sourceValue === undefined) {
          return;
        }

      let targetContext = {
        dependencies: dependencies,
        targetElem: targetElem,
        getStyle: window.getComputedStyle(targetElem),
        style: targetElem.style,
        parentStyle: window.getComputedStyle(targetElem.parentElement),
        contained: false,
      };
      let targetValue = getValue[dependency.targetAttr](targetContext);

      let targetType = attrType[dependency.targetAttr];

      let modifier = dependency.modifier !== undefined ? dependency.modifier : gap;

      console.log("C " + contained + sourceValue + sourceType + targetType);
      if (contained) {
        if (sourceType === LEADING && targetType === LEADING) {
          sourceValue += modifier;
        }
        else if (sourceType === TRAILING && targetType === TRAILING) {
          sourceValue -= modifier;
        }
      } else {
        if (sourceType === LEADING && targetType === TRAILING) {
          sourceValue -= modifier;
        } else if (sourceType === TRAILING && targetType === LEADING) {
          sourceValue += modifier;
        }
      }
      console.log("D " + sourceValue);

      if (comparisons[dependency.comparison](targetValue, sourceValue)) {
        values[dependency.targetAttr] = {
          targetElem: targetElem,
          targetValue: targetValue,
          sourceValue: sourceValue,
          context: targetContext
        };
      }
    });

    return values;
  }

  function getSourceValue(targetElem, dependency) {
    if (!checkRequirements(targetElem, dependency)) {
      return;
    }

    const sourceElem = document.getElementById(dependency.sourceId);

    let sourceValue;
    let contained = false;

    if (dependency.sourceId === undefined) {
      sourceValue = dependency.modifier;
    }
    else {
      contained = targetElem.parentElement === sourceElem;

      let sourceContext = {
        contained: contained,
        getStyle: window.getComputedStyle(sourceElem),
        parentStyle: window.getComputedStyle(sourceElem.parentElement),
        targetElem: targetElem
      };
      sourceValue = getValue[dependency.sourceAttr](sourceContext);
    }
    if (dependency.multiplier !== undefined) {
      sourceValue = sourceValue * dependency.multiplier;
    }
    return {
      sourceValue: sourceValue,
      contained: contained
    };
  }

  function checkRequirements(targetElem, dependency) {
    if (
      !dependency.require || dependency.require === "max" || dependency.require === "min"
    ) {
      return true;
    }

    // Check match with viewport portrait/landscape
    const mediaQuery = mediaRequire[dependency.require];
    if (mediaQuery) {
      return window.matchMedia(mediaQuery).matches;
    }

    // Check match with parent view high/wide
    const parentStyle = window.getComputedStyle(targetElem.parentElement);
    const wide = parentStyle.width > parentStyle.height;
    if (dependency.require === "wide") {
      return wide;
    } else {
      return !wide;
    }
  }

  function setDependencies(node) {
    var targetId = node.id;
    if (!targetId) { return; }

    var ui4AnimationID = node.getAttribute("ui4anim");

    var ui4AttrValue = node.getAttribute("ui4");


    if (ui4AttrValue) {
      //var dependencies = Array();
      var dependencies = globals.null.parse(ui4AttrValue);

      /**
      var animDependencies = Array();
      var specs = JSON.parse(ui4AttrValue);
      specs.forEach( (spec) => {
        let dependency = parseFullSpec(spec, targetId);
        if (dependency) {
          if (dependency.duration) {
            if (ui4AnimationID) {
              dependency.animationID = ui4AnimationID;
            }
            animDependencies.push(dependency);
          } else {
            dependencies.push(dependency);
          }
        }
      });
      **/

      if (!dependencies.length) {
        delete allDependencies[targetId];
      } else {
        allDependencies[targetId] = dependencies;
      }
      // ui4.testHook.allDependencies = allDependencies;

      /**
      if (animDependencies.length) {
        animatedDependencies[targetId] = animDependencies;
      }
      **/
    }

    /**
    var ui4CSSValue = node.getAttribute("ui4css");

    if (ui4CSSValue) {
      const animSpecs = JSON.parse(ui4CSSValue);
      animSpecs.forEach( (spec) => {
        if (ui4AnimationID) {
          spec.animationID = ui4AnimationID;
        }
        const animSpec = parseSpec(spec.animation);
        animSpec.key = spec.key;
        animSpec.value = spec.value;
        if (animatedCSS[targetId]) {
          animatedCSS[targetId].push(animSpec);
        } else {
          animatedCSS[targetId] = [animSpec];
        }
      });
    }
    **/
  }

  function checkCSSAnimations() {
    for (const [targetId, specs] of Object.entries(animatedCSS)) {
      const elem = document.getElementById(targetId);
      const style = window.getComputedStyle(elem);

      specs.forEach((spec) => {
        const animationID = spec.animationID;
        const key = toCamelCase(spec.key);
        const fromFrame = {};
        fromFrame[key] = style[spec.key];
        const toFrame = {};
        toFrame[key] = spec.value;
        const options = animationOptions(spec);
        options.fill = "forwards";
        
        const animation = elem.animate([fromFrame, toFrame], options);

        if (animationID) {
          if (animating[animationID]) {
            animating[animationID].push(animation);
          } else {
            animating[animationID] = [animation];
          }
          animation.onfinish = function() {
            //ui4.checkDependencies();
            animating[animationID].pop();
            checkAnimationStepComplete(animationID);
          };
        }
      });
    }
    animatedCSS = {};
  }
  
  function animationOptions(spec) {
    const options = {};
    if (spec.duration) {
      spec.duration = spec.duration * 1000;
    }
    const optionKeys = ['duration', 'easing', 'direction', 'delay', 'endDelay', 'iterations'];
    optionKeys.forEach(function(key) {
      const value = spec[key];
      if (value) {
        options[key] = value;
      }
    });
    
    return options;
  }
  
  function parseFullSpec(spec, targetId) {
    let parsed = parseSpec(spec, targetId);
    if (!parsed.comparison) {
      parsed.comparison = '=';
    }
    if ('key' in spec) {
      const parsedList = {
        key: spec.key,
        list: [],
      };
      spec.list.forEach(dependencySpec => {
        parsedList.list.push(parseSpec(dependencySpec));
      });

      parsed =  {...parsedList, ...parsed};
    }
    return parsed;
  }

  const constraintKeys = "targetAttr comparison sourceId sourceAttr multiplier modifier require duration easing delay endDelay direction iterations";
  const constraintMapping = constraintKeys.split(" ");
  
  function parseSpec(spec, targetId) {
    const parsedSpec = {};
    if (targetId) {
      parsedSpec.targetId = targetId;
    }

    constraintMapping.forEach((key, index) => {
      const value = spec["a" + index];
      if (value !== undefined) {
        parsedSpec[key] = value;
      }
    });

    return parsedSpec;
  }

  function checkAnimationStepComplete() {
    // if (animationID) {
    const toDelete = [];
    for (const [animationID, animationState] of Object.entries(animating)) {
      const animationsComplete = (animationState === undefined || animationState.length === 0);
  
      if (animationsComplete) {
        toDelete.push(animationID);
      }
    }
    toDelete.forEach(function(animationID) {
      delete animating[animationID];
      htmx.trigger(document.body, 'next', {animationID: animationID});
    });
  }

  function updateDependenciesWhileAnimating() {
    ui4.checkDependencies();
    const isAnimating = Object.keys(animating).length > 0;
    if (isAnimating) {
      requestAnimationFrame(updateDependenciesWhileAnimating);
    }
  }

  function logChange(entries) {
    console.log("Got something");
  }

  function setResizeObserver(node) {
    console.log("Set");
    const resizeObserver = new ResizeObserver(logChange);
    resizeObserver.observe(node);
  }

  function classChangeHandler(mutations, observer) {
    mutations.forEach( (mutation) => {
      switch(mutation.type) {
        case 'childList':
          mutation.addedNodes.forEach( (node) => {
            setDependencies(node);
            setResizeObserver(node);
          });
          break;
        case 'attributes':
          setDependencies(mutation.target);
          setResizeObserver(mutation.target);
          break;
      }
    });
  }

  ui4.startClassObserver = function () {
    const observer = new MutationObserver(classChangeHandler);
    observer.observe(document, {
      subtree: true,
      childList: true,
      attributeFilter: ["ui4"]
    });
  };

  ui4.startTracking = function () {
    const observer = new MutationObserver(ui4.checkDependencies);
    observer.observe(document.body, {
      subtree: true,
      childList: true,
      attributeFilter: ["style"]
    });
  };

  ui4.initialize = function() {
    ui4.startTracking();
  };

  // Update constraints on window resize
  window.addEventListener('resize', function (evt) {
    ui4.checkDependencies();
  });

  function toCamelCase(variableName) {
    return variableName.replace(
      /-([a-z])/g,
      function(str, letter) {
        return letter.toUpperCase();
      }
    );
  }

  ui4._privateForTesting = {
    parseFullSpec: parseFullSpec,
    toCamelCase: toCamelCase
  };
  
} (window.ui4 || {}, this));

window.ui4.startClassObserver();

/*
const mql = window.matchMedia("(prefers-color-scheme: dark)");

mql.addEventListener("change", () => {
    alert("Dark mode: " + mql.matches);
  });
*/
