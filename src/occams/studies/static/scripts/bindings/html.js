+function(){
  'use strict';

  ko.bindingHandlers.htmlBind = {
    init: function () {
      // we will handle the bindings of any descendants
      return { controlsDescendantBindings: true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
      // must read the value so it will update on changes to the value
      var value = ko.unwrap(valueAccessor());
      ko.cleanNode(element);
      // create the child html using the value
      ko.applyBindingsToNode(element, { html: value });
      // apply bindings on the created html
      ko.applyBindingsToDescendants(bindingContext, element);
    }
  };

}();
