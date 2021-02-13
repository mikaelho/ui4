/*jshint esversion: 6 */

(function (ui4, undefined) {
  'use strict';

  let gap = 8;
  
  const startTransitionEvent = "transitionstart"; //"htmx:beforeSwap";
  const endTransitionEvent = "transitionend"; //"htmx:afterSwap";

  const LEADING="leading", TRAILING="trailing", NEUTRAL="neutral";
  
  const attrs = {
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

  const compositeAttrTypes = {
    x: [attrs.left],
    y: [attrs.top],
    center: [attrs.centerx, attrs.centery],
    position: [attrs.left, attrs.top],
    size: [attrs.width, attrs.height],
    bbox: [attrs.left, attrs.top, attrs.width, attrs.height]
  };
  
  var allDependencies = {};
  
  ui4.checkDependencies = function() {
    for (const [targetId, dependencies] of Object.entries(allDependencies)) {
      dependencies.forEach( (dependency) => {
        //window.console.log(JSON.stringify(dependency));
        var sourceElem = document.getElementById(dependency.sourceId);
        var targetElem = document.getElementById(targetId);
        var sourceStyle = window.getComputedStyle(sourceElem);
        var targetStyle = window.getComputedStyle(targetElem);
        dependency.updateFunc(
            sourceElem, sourceStyle, dependency.sourceAttr,
            targetElem, targetStyle, dependency.targetAttr
        );
      });
    }
  }
  
  function updateEqual(sourceElem, sourceStyle, sourceAttr, targetElem, targetStyle, targetAttr) {
    var sourceValue = sourceStyle.getPropertyValue(sourceAttr);
    var targetValue = targetStyle.getPropertyValue(targetAttr);
    if (sourceValue !== targetValue) {
      targetElem.style[targetAttr] = sourceValue;
    }
  }

  const complementValue = {
    left: (parentStyle, sourceStyle) => parseFloat(parentStyle.width) - parseFloat(sourceStyle.right) + gap,
    right: (parentStyle, sourceStyle) => parentStyle.width - sourceStyle.left - gap,
    top: (parentStyle, sourceStyle) => parseFloat(parentStyle.height) - parseFloat(sourceStyle.bottom) + gap,
    bottom: (parentStyle, sourceStyle) => parentStyle.height - sourceStyle.top - gap
  };

  function updateComplementary(sourceElem, sourceStyle, sourceAttr, targetElem, targetStyle, targetAttr) {
    let parentStyle = window.getComputedStyle(sourceElem.parentElement);
    let sourceValue = complementValue[targetAttr](parentStyle, sourceStyle) + "px";
    let targetValue = targetStyle.getPropertyValue(targetAttr);
    if (sourceValue !== targetValue) {
      targetElem.style[targetAttr] = sourceValue;
    }
  }
  
  function getUpdateFunction(source, target) {
    if (attrs[source] === attrs[target] || attrs[source] === NEUTRAL || attrs[target] === NEUTRAL) {
      return updateEqual;
    }
    else {
      return updateComplementary;
    }
  }
  
  function setDependencies(node) {
    var targetId = node.id; 
    if (!targetId) { return; }
    
    var ui4AttrValue = node.getAttribute("ui4");
    if (!ui4AttrValue) { return; }

    var dependencies = Array();
    var specs = ui4AttrValue.split(" ");
    specs.forEach( (spec) => {
      let tokens = spec.split(/\W/);
      dependencies.push({
        updateFunc: getUpdateFunction(tokens[2], tokens[0]),
        targetAttr: tokens[0],
        sourceId: tokens[1],
        sourceAttr: tokens[2]
      });
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
  
  // Manage updates during CSS transitions
  
  var runningTransitions = 0;
  var animationFrame;
  
  window.addEventListener(startTransitionEvent, function (evt) {
    if (runningTransitions === 0) {
      function dependencyRunner() {
        ui4.checkDependencies();
        animationFrame = requestAnimationFrame(dependencyRunner);
      }
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
  
  
} ( window.ui4 = window.ui4 || {} ));

ui4.startClassObserver();
