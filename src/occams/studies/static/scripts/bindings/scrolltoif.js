/**
 * Scrolls to the given element if it's binded data value is the the same
 * as the valueAccessor
 */
ko.bindingHandlers.scrollToIf = {
  update: function(element, valueAccessor) {
    var value = ko.unwrap(valueAccessor());

    if (value) {
      var scrollTop = $(element).offset().top
        , verticalSpace = $(window).height() - $(element).height();

      if ( verticalSpace > 0 ){
        // Try to center the element if it fits inside the viewport
        scrollTop -= verticalSpace / 2;
      }

      $('html, body').animate({scrollTop: scrollTop}, 1000);
    }

  }
};
