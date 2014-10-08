/**
 * data -- binding
 * template -- temlate to use for the content
 * options -- bootstrap options
 *
 */
ko.bindingHandlers.popover = {
  init: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
    var options = $.extend({}, {
      }, ko.unwrap(valueAccessor()));

      $(element).popover(options.options);
  }
}
