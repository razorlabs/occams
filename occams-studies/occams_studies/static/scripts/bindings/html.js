+function(){
  'use strict';

  /**
   * Dynamically updates and binds the HTML content of an element
   *
   * http://stackoverflow.com/a/17756777/148781
   */
  ko.bindingHandlers.htmlBind = {
    init: function () {
      // we will handle the bindings of any descendants
      return { controlsDescendantBindings: true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
      ko.utils.setHtml(element, valueAccessor());
      ko.applyBindingsToDescendants(bindingContext, element);
    }
  };

}();
