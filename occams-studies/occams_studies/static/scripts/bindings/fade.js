/**
 * Custom binding to fade elements in/out
 * Usage:
 *    data-bind="fadeVisible: myvar()"
 *    data-bind="fadeVisible: {if: myvar(), duration: 'slow', ... }
 * Parameters:
 *    if -- (required) the observable to check
 *    duration -- (optional) easing duration ('fast', 'slow', milliseconds)
 */
ko.bindingHandlers.fadeVisible = {
  init: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
    var $element = $(element)
      , value = valueAccessor()
      , options = value || {'if': value};
    // Initially set the element to be instantly visible/hidden depending on the value
    // Use "unwrapObservable" so we can handle values that may or may not be observable
    $element.toggle(ko.unwrap(options['if']));
  },
  update: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
    var $element = $(element)
      , value = valueAccessor()
      , options = value || {'if': value};

    // Whenever the value subsequently changes, slowly fade the element in or out
    if (ko.unwrap(options['if'])) {
      $element.fadeIn(options.duration)
    } else {
      $element.fadeOut(options.duration);
    }
  }
};
