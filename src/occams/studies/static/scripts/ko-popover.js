/**
 * data -- binding
 * template -- temlate to use for the content
 * options -- bootstrap options
 *
 */
ko.bindingHandlers.showPopover = {
  update: function (element, valueAccessor) {
    var value = valueAccessor();
    if (ko.unwrap(value)) {
      $(element).popoverX('show');
    } else {
      $(element).popoverX('hide');
    }
  }
};
