/*jshint esversion: 6 */

(function (ui4, undefined) {
  'use strict';

  let gap = 8;

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
    "=": (a, b) => a != b,
    "<": (a, b) => a >= b,
    ">": (a, b) => a <= b
  };
  
  const operators = {
    "+": (a, b) => a + b,
    "-": (a, b) => a - b,
    "*": (a, b) => a * b,
    "/": (a, b) => a / b
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
  };

  const setValue = {
    width: function(context, value) { context.style.width = value + 'px'; },
    height: function(context, value) { context.style.height = value + 'px'; },
    left: function(context, value) { context.style.left = value + 'px'; },
    right: function(context, value) { context.style.right = parseFloat(context.parentStyle.width) - value + 'px'; },
    top: function(context, value) { context.style.top = value + 'px'; },
    bottom: function(context, value) { context.style.bottom = parseFloat(context.parentStyle.height) - value + 'px'; },
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

  var allDependencies = {};

  ui4.checkDependencies = function() {
    for (const [targetId, dependencies] of Object.entries(allDependencies)) {
      // Only apply the final value per property
      let finalValues = {};
      dependencies.forEach( dependency => {
        //console.log(JSON.stringify(dependency));
        let sourceElem = document.getElementById(dependency.sourceId);
        let targetElem = document.getElementById(targetId);
        let targetStyle = window.getComputedStyle(targetElem);
        
        let sourceValue;
        let contained = false;
        
        if (dependency.sourceId === CONSTANT) {
          sourceValue = dependency.constant;
        }
        else {
          let sourceStyle = window.getComputedStyle(sourceElem);
          contained = targetElem.parentElement === sourceElem;
  
          let sourceContext = {
            contained: contained,
            getStyle: window.getComputedStyle(sourceElem),
            parentStyle: window.getComputedStyle(sourceElem.parentElement)
          };
          sourceValue = getValue[dependency.sourceAttr](sourceContext);
        }
        
        let targetContext = {
          dependencies: dependencies,
          getStyle: window.getComputedStyle(targetElem),
          style: targetElem.style,
          parentStyle: window.getComputedStyle(targetElem.parentElement),
          contained: false,
        };
        let targetValue = getValue[dependency.targetAttr](targetContext);

        let sourceType = attrType[dependency.sourceAttr];
        let targetType = attrType[dependency.targetAttr];
        if (dependency.operator) {
          sourceValue = operators[dependency.operator](sourceValue, dependency.constant);
        }
        else if (contained) {
          if (sourceType === LEADING && targetType === LEADING) {
            sourceValue += gap;
          }
          else if (sourceType === TRAILING && targetType === TRAILING) {
            sourceValue -= gap;
          }
        } else {
          if (sourceType === LEADING && targetType === TRAILING) {
            sourceValue -= gap;
          }
          else if (sourceType === TRAILING && targetType === LEADING) {
            sourceValue += gap;
          }
        }
        

        if (comparisons[dependency.comparison](targetValue, sourceValue)) {
          finalValues[dependency.targetAttr] = {
            value: sourceValue,
            context: targetContext
          }
        }
      });
      // Only apply the final value for each attribute
      for (const [targetAttr, data] of Object.entries(finalValues)) {
        setValue[targetAttr](data.context, data.value);
      }
    }
  };

  function setDependencies(node) {
    var targetId = node.id;
    if (!targetId) { return; }

    var ui4AttrValue = node.getAttribute("ui4");
    if (!ui4AttrValue) { return; }

    var dependencies = Array();
    var specs = ui4AttrValue.split(" ");
    specs.forEach( (spec) => {
      let dependency = parseSpec(spec);
      if (dependency) {
        dependencies.push(dependency);
      }
    });
    if (!dependencies.length) {
      delete allDependencies[targetId];
    } else {
      allDependencies[targetId] = dependencies;
    }
  }
      
  function parseSpec(spec) {
    const mainRegex = /([^=<>]+)([=<>])(.+)/;
    //let tokens = spec.split(/(\W)/);
    let tokens = mainRegex.exec(spec);
    if (!tokens || tokens.length != 4) {
      console.error("Cannot parse:", spec, " - tokens:", tokens);
      return;
    }
    let targetAttr = tokens[1];
    let comparison = tokens[2];
    let sourceSpec = tokens[3];
    let sourceId, sourceAttr, constant, operator, modifier;
    
    if (isNaN(sourceSpec)) {
      const sourceRegex = /([^\.]+)[\.]([^\+\-\/\*]+)([\+\-\/\*]?)(.*)/;
      let specTokens = sourceRegex.exec(sourceSpec);
      if (!specTokens || specTokens.length < 3) {
        console.error("Cannot parse source spec", spec);
        return;
      }
      sourceId = specTokens[1];
      sourceAttr = specTokens[2];
      if (specTokens.length == 4) {
        console.error("Missing modifier value", spec);
        return;
      }
      if (specTokens.length == 5) {
        operator = specTokens[3];
        if (isNaN(specTokens[4])) {
          console.error("Modifier is not a number", spec);
          return;
        }
        constant = parseFloat(specTokens[4]);
      } else {
        operator = false;
        constant = 0;
      }
    } else {
      constant = parseFloat(sourceSpec);
      sourceId = CONSTANT; 
      sourceAttr = null;
    }
    return {
      targetAttr: targetAttr,
      comparison: comparison,
      sourceId: sourceId, 
      sourceAttr: sourceAttr,
      operator: operator,
      constant: constant
    };
  }

  function classChangeHandler(mutations, observer) {
    mutations.forEach( (mutation) => {
      switch(mutation.type) {
        case 'childList':
          mutation.addedNodes.forEach( (node) => {
            setDependencies(node);
          });
          //console.log(mutation.removedNodes)
          break;
        case 'attributes':
        setDependencies(mutation.target);
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

  // Update constraints during CSS transitions
  const startTransitionEvent = "transitionstart"; //"htmx:beforeSwap";
  const endTransitionEvent = "transitionend"; //"htmx:afterSwap";

  var runningTransitions = 0;
  var animationFrame;

  window.addEventListener(startTransitionEvent, function (evt) {
    if (runningTransitions === 0) {
      const dependencyRunner = function () {
        ui4.checkDependencies();
        animationFrame = requestAnimationFrame(dependencyRunner);
      };
      dependencyRunner();
      runningTransitions++;
    }
  });

  window.addEventListener(endTransitionEvent, function () {
    runningTransitions--;
    if (runningTransitions <= 0) {
      runningTransitions = 0;
      cancelAnimationFrame(animationFrame);
    }
  });

  // Update constrains on window resize
  window.addEventListener('resize', function (evt) {
    ui4.checkDependencies();
  });

  // Start reacting to node additions, deletions and style changes
  document.addEventListener('DOMContentLoaded', ui4.startTracking);

} ( window.ui4 = window.ui4 || {} ));

ui4.startClassObserver();
