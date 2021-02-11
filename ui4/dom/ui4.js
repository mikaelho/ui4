ui4 = {
  attrs: {
    top: "leading",
    left: "leading",
    
  },
  classChangeHandler: function (mutations, observer) {
    mutations.forEach( (mutation) => {
      switch(mutation.type) {
        case 'childList':
          mutation.addedNodes.forEach( (node) => {
            console.log(node.className)
          });
          console.log(mutation.removedNodes)
          break;
        case 'attributes':
          console.log(mutation.attributeName);
          break;
      }
    });
  },
  startClassObserver: function () {
    const observer = new MutationObserver(ui4.classChangeHandler);
    observer.observe(document, {
      subtree: true,
      childList: true,
      attributeFilter: ["class"]
    });
  },
  startTracking: function (sourceId, sourceAttr, targetId, targetAttr) {
    const sourceElem = document.getElementById(sourceId);
    const targetElem = document.getElementById(targetId);
    const observer = new MutationObserver(
      function () {
        console.log("hep");
        var sourceStyle = window.getComputedStyle(sourceElem);
        targetElem.style[targetAttr] = sourceStyle.getPropertyValue(sourceAttr);
      }
    );
    observer.observe(document.body, {
      subtree: true,
      childList: true,
      attributeFilter: ["style"]
    });
  }
}
