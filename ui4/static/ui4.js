/*jshint esversion: 6 */

(function (ui4, undefined) {
  'use strict';

  let gap = 8;
  let allDependencies = {};
  let animatedDependencies = {};
  let latestValues = {};
  let transitioning = {};

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
        if (left === false) {
          const bbox = child.getBoundingClientRect();
          left = bbox.left;
          right = bbox.right;
        } else {
          const bbox = child.getBoundingClientRect();
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
        if (top === false) {
          const bbox = child.getBoundingClientRect();
          top = bbox.top;
          bottom = bbox.bottom;
        } else {
          const bbox = child.getBoundingClientRect();
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
        context.style.width = 2 * (value - parseFloat(context.getStyle.left)) + 'px';
      } else if (context.dependencies.find(item => item.targetAttr === 'right')) {  // right locked, width must give)
        context.style.width =
            2 * (parseFloat(context.parentStyle.width) - parseFloat(context.getStyle.right) - value) + 'px';
      } else {  // Neither locked, move left
        context.style.left = value - parseFloat(context.getStyle.width) / 2 + 'px';
      }
    },
    centerY: function(context, value) {
      if (context.dependencies.find(item => item.targetAttr === 'top')) {  // top locked, height must give
        context.style.height = 2 * (value - parseFloat(context.getStyle.top)) + 'px';
      } else if (context.dependencies.find(item => item.targetAttr === 'bottom')) {  // bottom locked, height must give)
        context.style.height =
            2 * (parseFloat(context.parentStyle.height) - parseFloat(context.getStyle.bottom) - value) + 'px';
      } else {  // Neither locked, move top
        context.style.top = value - parseFloat(context.getStyle.height) / 2 + 'px';
      }
    }
  };

  ui4.checkDependencies = function() {
    checkAllDependencies();
    checkAnimationDependencies();
  };
    
  function checkAllDependencies() {
    for (const [targetId, dependencies] of Object.entries(allDependencies)) {
      let finalValues = checkAttribute(targetId, dependencies);
      // Apply the final value for each attribute
      for (const [targetAttr, data] of Object.entries(finalValues)) {
        setValue[targetAttr](data.context, data.sourceValue);
        latestValues[targetId + "." + targetAttr] = data.sourceValue;
      }
    }
  }
  
  function checkAnimationDependencies() {
    for (const [targetId, dependencies] of Object.entries(animatedDependencies)) {

      let values = checkAttribute(targetId, dependencies);
      
      dependencies.forEach((dependency, index) => {
        let data = values[dependency.targetAttr];
        let from = {};
        from[dependency.targetAttr] = data.targetValue;
        let to = {};
        to[dependency.targetAttr] = data.sourceValue;

        let animation = data.targetElem.animate(
         [from, to],
         {duration: dependency.duration, easing: dependency.easeFunc}
        );
        setValue[dependency.targetAttr](data.context, data.sourceValue);
        let currentValue;
        const currentTime = Date.now();
        if (currentTime >= dependency.readyBy) {
          currentValue = data.sourceValue;
          delete dependencies[index];
          if (allDependencies[dependency.targetId]) {
            allDependencies[dependency.targetId].push(dependency);
          } else {
            allDependencies[dependency.targetId] = [dependency];
          }
          checkAnimationStepComplete(dependency.targetId);
        } else {
          const progress = (currentTime - dependency.previousTime)/(dependency.readyBy - dependency.previousTime);
          dependency.previousTime = currentTime;
          let previousValue = latestValues[dependency.targetId + "." + dependency.targetAttr];
          if (previousValue === undefined) {
            previousValue = data.targetValue;
          }
          currentValue = previousValue + (data.sourceValue - previousValue) * progress;
        }
        setValue[dependency.targetAttr](data.context, currentValue);
        latestValues[targetId + "." + dependency.targetAttr] = currentValue;
      });
      
      if (Object.keys(animatedDependencies).length) {
        requestAnimationFrame(checkAnimationDependencies);
      }
    }
  }
      
  function checkAttribute(targetId, dependencies) {
    let values = {};

    dependencies.forEach( dependency => {
      //console.log(JSON.stringify(dependency));
      let sourceElem = document.getElementById(dependency.sourceId);
      let targetElem = document.getElementById(targetId);
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
      
      let targetContext = {
        dependencies: dependencies,
        targetElem: targetElem,
        getStyle: window.getComputedStyle(targetElem),
        style: targetElem.style,
        parentStyle: window.getComputedStyle(targetElem.parentElement),
        contained: false,
      };
      let targetValue = getValue[dependency.targetAttr](targetContext);

      let sourceType = attrType[dependency.sourceAttr];
      let targetType = attrType[dependency.targetAttr];

      if (dependency.multiplier !== undefined) {
        sourceValue = sourceValue * dependency.multiplier;
      }

      let modifier = dependency.modifier !== undefined ? dependency.modifier : gap;

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
        }
        else if (sourceType === TRAILING && targetType === LEADING) {
          sourceValue += modifier;
        }
      }

      if (comparisons[dependency.comparison](targetValue, sourceValue)) {
        values[dependency.targetAttr] = {
          targetValue: targetValue,
          sourceValue: sourceValue,
          context: targetContext
        };
      }
    });

    return values;
  }

  function setDependencies(node) {
    var targetId = node.id;
    if (!targetId) { return; }

    var ui4AttrValue = node.getAttribute("ui4");
    
    if (ui4AttrValue) {
      var dependencies = Array();
      var animDependencies = Array();
      var specs = ui4AttrValue.split(" ");
      specs.forEach( (spec) => {
        let dependency = parseSpec(spec, targetId);
        if (dependency) {
          if (spec.duration) {
            animDependencies.push(dependency);
          } else {
            dependencies.push(dependency);
          }
        }
      });
      if (!dependencies.length) {
        delete allDependencies[targetId];
      } else {
        allDependencies[targetId] = dependencies;
      }
      if (animDependencies.length) {
        animatedDependencies[targetId] = animDependencies;
      }
    }
  }

  const constraintKeys = "targetAttr comparison sourceId sourceAttr multiplier modifier duration easeFunc";
  const constraintMapping = constraintKeys.split(" ");

  function parseSpec(spec, targetId) {
    let parsedSpec = {targetId: targetId};

    constraintMapping.forEach((key, index) => {
      const value = spec["a" + index];
      if (value !== undefined) {
        parsedSpec[key] = value;
      }
    });

    return parsedSpec;
  }
  
  function setTransitionHandlers(node) {
    node.addEventListener(
      'transitionrun',
      function (evt) {
        if (this.id) {
          transitioning[this.id] = (transitioning[this.id] || 0) + 1;
        }
      });
    node.addEventListener(
      'transitionend',
      function (evt) {
        if (this.id) {
          transitioning[this.id] -= 1;
          if (transitioning[this.id] === 0) {
            console.log(this.id + "." + evt.propertyName + " complete");
            checkAnimationStepComplete(this.id);
          }
        }
      });
  }
  
  function checkAnimationStepComplete(nodeId) {
    const transitionState = transitioning[nodeId];
    const animationState = animatedDependencies[nodeId];
    
    const transitionsComplete = (transitionState === undefined || transitionState === 0);
    const animationsComplete = (animationState === undefined || animationState.length === 0);
    
    if (transitionsComplete && animationsComplete) {
      const elem = document.getElementById(nodeId);
      elem.dispatchEvent(new Event('next'));
    }
  }

  function classChangeHandler(mutations, observer) {
    mutations.forEach( (mutation) => {
      switch(mutation.type) {
        case 'childList':
          mutation.addedNodes.forEach( (node) => {
            setDependencies(node);
            setTransitionHandlers(node);
          });
          
          //console.log(mutation.removedNodes)
          break;
        case 'attributes':
        setDependencies(mutation.target);
          setTransitionHandlers(mutation.target);
          break;
      }
    });
  }

  ui4.startClassObserver = function () {
    const observer = new MutationObserver(classChangeHandler);
    observer.observe(document, {
      subtree: true,
      childList: true,
      attributeFilter: ["ui4", "ui4anim"]
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
  
  // Know when we are making CSS transitions
  const startTransitionEvent = "transitionstart";
  const endTransitionEvent = "transitionend";

  var runningTransitions = 0;
  var animationFrame;

  // Update constraints on window resize
  window.addEventListener('resize', function (evt) {
    ui4.checkDependencies();
  });

  // Start reacting to node additions, deletions and style changes
  document.addEventListener('DOMContentLoaded', ui4.startTracking);

} ( window.ui4 = window.ui4 || {} ));

ui4.startClassObserver();

/*
const mql = window.matchMedia("(prefers-color-scheme: dark)");

mql.addEventListener("change", () => {
    alert("Dark mode: " + mql.matches);
  });
*/
