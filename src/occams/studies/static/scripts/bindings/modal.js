/**
 * Binds the element to a Bootstrap modal and
 * displays it when the argument evaluates to a truish value.
 *
 * http://stackoverflow.com/q/14683953/148781
 */
ko.bindingHandlers.showModal = {
  update: function (element, valueAccessor) {
    $(element).modal(ko.unwrap(valueAccessor()) ? 'show' : 'hide');
  }
};

$(function(){
  // Autofocus an element when it is first shown
  $(document).on('shown.bs.modal', '.modal', function() {
    $('[autofocus]', this).focus();
  });
});

