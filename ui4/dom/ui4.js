(function (ui4, undefined) {
  
  var LEADING="leading", TRAILING="trailing", NEUTRAL="neutral";
  
  var attrTypes = {
    width: NEUTRAL,
    height: NEUTRAL,
    left: LEADING,
    right: TRAILING,
    top: LEADING,
    bottom: TRAILING
  };
  
  var allDependencies = {};
  
  function checkDependecies() {
    for (const [targetId, dependencies] of Object.entries(allDependencies)) {
      dependencies.forEach( (d) => {
        console.log(JSON.stringify(d));
        var sourceElem = document.getElementById(d.sourceId);
        var targetElem = document.getElementById(targetId);
        var sourceStyle = window.getComputedStyle(sourceElem);
        var targetStyle = window.getComputedStyle(targetElem);
        d.updateFunc(sourceStyle, d.sourceAttr, targetElem, targetStyle, d.targetAttr);
      });
    }
  }
  
  function updateEqual(sourceStyle, sourceAttr, targetElem, targetStyle, targetAttr) {
    var sourceValue = sourceStyle.getPropertyValue(sourceAttr);
    var targetValue = targetStyle.getPropertyValue(targetAttr);
    if (sourceValue !== targetValue) {
      targetElem.style[targetAttr] = sourceValue;
    }
  }
  
  function getUpdateFunction(source, target) {
    if (attrTypes[source] === attrTypes[target]) {
      return updateEqual;
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
    const observer = new MutationObserver(checkDependecies);
    observer.observe(document.body, {
      subtree: true,
      childList: true,
      attributeFilter: ["style"]
    });
  }
  
} ( window.ui4 = window.ui4 || {} ));

ui4.startClassObserver();
