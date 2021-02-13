/*jshint esversion: 6 */

(function (ui4, undefined) {
  'use strict';

  let gap = 8;

  const LEADING = "leading", TRAILING = "trailing", NEUTRAL = "neutral";

  const attrType = {
    constant: NEUTRAL,
    width: NEUTRAL,
    height: NEUTRAL,
    left: LEADING,
    right: TRAILING,
    top: LEADING,
    bottom: TRAILING,
    centerx: NEUTRAL,
    centery: NEUTRAL,
  };

  const getValue = {
    constant: (context) => parseFloat(context.constant),
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
  };

  const setValue = {
    width: function(context, value) { context.style.width = value + 'px'; },
    height: function(context, value) { context.style.height = value + 'px'; },
    left: function(context, value) { context.style.left = value + 'px'; },
    right: function(context, value) { context.style.right = parseFloat(context.parentStyle.width) - value + 'px'; },
    top: function(context, value) { context.style.top = value + 'px'; },
    bottom: function(context, value) { context.style.bottom = parseFloat(context.parentStyle.height) - value + 'px'; },
    centerx: function(context, value) {
      if (context.dependencies.find(item => item.targetAttr === 'left')) {  // left locked, width must give
        context.style.width = 2 * (value - parseFloat(context.getStyle.left)) + 'px';
      } else if (context.dependencies.find(item => item.targetAttr === 'right')) {  // right locked, width must give)
        context.style.width =
            2 * (parseFloat(context.parentStyle.width) - parseFloat(context.getStyle.right) - value) + 'px';
      } else {  // Neither locked, move left
        context.style.left = value - parseFloat(context.getStyle.width) / 2 + 'px';
      }
    },
    centery: function(context, value) {
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
      dependencies.forEach( dependency => {
        //window.console.log(JSON.stringify(dependency));
        let sourceElem = document.getElementById(dependency.sourceId);
        let targetElem = document.getElementById(targetId);
        let sourceStyle = window.getComputedStyle(sourceElem);
        let targetStyle = window.getComputedStyle(targetElem);
        let contained = targetElem.parentElement === sourceElem;

        let sourceContext = {
          contained: contained,
          getStyle: window.getComputedStyle(sourceElem),
          parentStyle: window.getComputedStyle(sourceElem.parentElement)
        };
        let sourceValue = getValue[dependency.sourceAttr](sourceContext);
        
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
        if (contained) {
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
        

        if (targetValue !== sourceValue) {
          setValue[dependency.targetAttr](targetContext, sourceValue);
        }
      });
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
      let tokens = spec.split(/\W/);
      dependencies.push({targetAttr: tokens[0], sourceId: tokens[1], sourceAttr: tokens[2]});
    });
    if (!dependencies.length) {
      delete allDependencies[targetId];
    } else {
      allDependencies[targetId] = dependencies;
    }
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
