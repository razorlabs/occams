/**
 * Binds the element to a Bootstrap modal and
 * displays it when the argument evaluates to a truish value.
 *
 * http://stackoverflow.com/q/14683953/148781
 */
ko.bindingHandlers.showModal = {
  update: function (element, valueAccessor) {
    var value = valueAccessor();
    if (ko.unwrap(value)) {
      $(element).modal('show');
      $('input', element).focus();
    } else {
      $(element).modal('hide');
    }
  }
};
