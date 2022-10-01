
// Some dummy objects to enable running the tests without the browser
window = {
    addEventListener: (event_name, func) => {}
};
document = {
    addEventListener: (event_name, func) => {}
};
MutationObserver = function MutationObserver(func) {
    this.observe = (node, func) => {}
};
